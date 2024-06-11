from src.Schemas import QueryInput, GraphState, PipelineCode, AnalyzeConditions
from src.Constant import get_agent_prompt, MAX_ITERATION, execute_query_user_error_msg, contains_error_msg, prepare_analyze_tools, prepare_execution_tools, generate_pipeline_query_msg, analyze_pipeline_query_user_msg, intermediate_query_error_msg, contains_raw_output_error_msg, contains_DML_operation_error_msg, execute_query_user_msg, analyze_pipeline_query_assistant_msg, analyze_pipeline_query_user_msg_seccond, user_message
from src.llm import BaseLLM
from src.DBReader import BaseDBReader
import json
from datetime import datetime


class DBQueryAgent:
    def __init__(self, llm : BaseLLM, database : BaseDBReader) -> None:
        self.llm = llm
        self.database = database
    
    def prepare_intial_messages(self, collection_list : list[str], collection_explanation : str, user_query : str, db_description : str) -> list:
        messages = [
            self.llm.get_chat_message(role="system", content=get_agent_prompt(collection_list, collection_explanation, db_description)),
            self.llm.get_chat_message(role="user", content=user_message(collection_list, collection_explanation, db_description, user_query)) 
        ]

        return messages
    
    def convert_dates_in_query(self, query : list[dict]):

        date_format = "%Y-%m-%d"

        def is_date(string):
            check_date = []
            try:
                datetime.strptime(string, date_format)
                check_date.append(True)
            except:                    
                check_date.append(False)

            try:
                datetime.fromisoformat(string)
                check_date.append(True)
            except:                    
                check_date.append(False)
            
            return bool(sum(check_date))

        def convert_dates(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and is_date(value):
                        try:
                            obj[key] = datetime.strptime(value, date_format)
                        except:
                            obj[key] = datetime.fromisoformat(value)

                    elif isinstance(value, dict) or isinstance(value, list):
                        convert_dates(value)
            elif isinstance(obj, list):
                for item in obj:
                    convert_dates(item)

        query_copy = json.loads(json.dumps(query))
        convert_dates(query_copy)
        return query_copy
    
    def generate_pipeline_query(self, state: GraphState, input_parameters : QueryInput) -> GraphState:
        output = self.llm.invoke(model = input_parameters.llm_name, temperature = input_parameters.temperature, tools=prepare_execution_tools(), messages = state.messages)    
        state.generation = PipelineCode(**output)

        state.generation.mongodb_pipeline = json.loads(state.generation.mongodb_pipeline)

        if(len(state.messages) > 1):
            state.generation.query_analysis_failed = False
        state.generation.mongodb_pipeline = self.convert_dates_in_query(state.generation.mongodb_pipeline)
        state.messages.append(self.llm.get_chat_message(role="assistant", content=generate_pipeline_query_msg(state.generation.mongodb_pipeline, state.generation.collection_name, state.generation.query_analysis_failed)))
        state.iterations = state.iterations + 1

        return state 
    
    def analyze_pipeline_query(self, state : GraphState, input_parameters : QueryInput) -> GraphState:
        state.messages.append(self.llm.get_chat_message(
            role = "user", 
            content=analyze_pipeline_query_user_msg(input_parameters.query, state.generation.mongodb_pipeline, state.generation.collection_name)))

        response = self.llm.invoke(model=input_parameters.llm_name, messages=state.messages, tools=prepare_analyze_tools(input_parameters.query),  temperature = input_parameters.temperature)

        response_schema = AnalyzeConditions(**response)

        state.error = bool(response_schema.intermediate_query + response_schema.contains_raw_output + response_schema.contains_DML_operation + response_schema.incorrect_query)

        if(state.error == False):
            state = self.execute_query(state, input_parameters)
        else:
            output_message = []
            if(response_schema.intermediate_query == True):
                output_message.append(intermediate_query_error_msg(response_schema.reason_for_intermediate_query))

            if(response_schema.contains_raw_output == True):
                output_message.append(contains_raw_output_error_msg(response_schema.reason_for_contains_raw_output))

            if(response_schema.contains_DML_operation == True):
                output_message.append(contains_DML_operation_error_msg(response_schema.reason_for_contains_DML_operation))

            if(response_schema.incorrect_query == True):
                output_message.append(contains_error_msg(response_schema.reason_for_incorrect_query))

            state.messages.append(self.llm.get_chat_message(role = "assistant", content = analyze_pipeline_query_assistant_msg()))
            
            state.messages.append(self.llm.get_chat_message(role = "user", content = analyze_pipeline_query_user_msg_seccond(output_message, state.generation.mongodb_pipeline)))
        
        state.iterations = state.iterations + 1

        return state

    def execute_query(self, state : GraphState, input_parameters : QueryInput):
        try:
            result = self.database.run_pipeline_query(state.generation.collection_name, state.generation.mongodb_pipeline)
            output_data = []
            reached_max_count = False

            for i in result:
                output_data.append(str(i))
                if(len(output_data) > input_parameters.max_output_count):
                    reached_max_count = True
                    break

            state.messages.append(self.llm.get_chat_message(role = "user", content = execute_query_user_msg(reached_max_count, input_parameters.max_output_count, output_data)))
            state.iterations = state.iterations + 1
            state.error = False
            return state
        except Exception as e:
            state.messages.append(self.llm.get_chat_message(role = "user", content = execute_query_user_error_msg(str(e))))
            state.iterations = state.iterations + 1
            state.error = True
            return state
    
    def decide_to_finish(self, state: GraphState) -> bool:

        if state.error == True:
            return False
        elif state.iterations > MAX_ITERATION:
            return True
        else:
            return True
        
    def prepare_final_response(self, state : GraphState, input_parameters : QueryInput) -> GraphState:
        output = self.llm.invoke(model = input_parameters.llm_name, temperature = input_parameters.temperature, messages = state.messages, return_tool = False)    
        
        state.messages.append(self.llm.get_chat_message(content = output, role = "assistant"))

        return state
        
    def run_loop(self, graph_state : GraphState, input_parameters : QueryInput) -> str:
        while True:
            graph_state = self.generate_pipeline_query(graph_state, input_parameters)

            if graph_state.generation.query_analysis_failed == True:
                return self.llm.get_chat_content(graph_state.messages[-1])
            
            graph_state = self.analyze_pipeline_query(graph_state, input_parameters)


            decision = self.decide_to_finish(graph_state)

            if decision == True:
                return self.llm.get_chat_content(self.prepare_final_response(graph_state, input_parameters).messages[-1])
    
    def execute_agent(self, input_parameters : QueryInput) -> str:
        collection_explanation = self.database.prepare_schema_prompt(input_parameters.collection_list, input_parameters.max_output_count)
        
        initial_state = GraphState(
            error=False, 
            messages=self.prepare_intial_messages(input_parameters.collection_list, collection_explanation, input_parameters.query, input_parameters.description),
            generation=None,
            iterations=0
        )

        return self.run_loop(initial_state, input_parameters)
            
        
        



