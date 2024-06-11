from textwrap import dedent
import json

MISTRAL_CODE_MODEL = "codestral-latest"
MISTRAL_LLM_TEMPERATURE = 0.0
MAX_ITERATION = 10
MONGODB = "MongoDB"
OPENAI_GPT4_MODEL = "gpt-4-turbo-2024-04-09"


def get_agent_prompt(collection_list : list[str], collection_explanation : str, db_description : str, database_type : str = MONGODB) -> str:
    if(database_type == MONGODB):
        return dedent(
            f"""
            As a PyMongo agent, your main responsibility is to interact with a MongoDB database. For each task assigned to you, you must create a syntactically correct pipeline. This pipeline will then be passed to a tool that checks the output of the generated pipeline. The tool is already connected to the database through PyMongo, and the pipeline you provide will be used in the aggregate function associated with the specified collection.


            You have been granted access to the following collections within the User database:

            **Collection List:**
            {collection_list}

            **Detailed Descriptions of Each Collection:**
            =============
            {collection_explanation}
            =============

            **User given Database Description:**
            {db_description}

            Based on the information provided, please construct the pipeline code that addresses the user query.

            """)
    else:
        raise Exception("Not Implemented")

def user_message(collection_list : list[str], collection_explanation : str, db_description : str, user_query : str, database_type : str = MONGODB) -> str:
    return dedent(
        f"""

        Answer the following questions as best you can. You have access to the following tools:

        "test_mongo_pipeline_query". 
        Above function runs given query using PyMongo aggregation pipelines. It returns successful output or associated errors if pipeline is incorrect. 
        Args:
            mongodb_pipeline: MongoDb pipeline which need to be test on given collection
            collection_name: collection_name on which mongodb pipeline will run through pymongo.
            query_analysis_failed : boolean parameter to specify if given user query is not related to generating mongo pipeline query.

        You must use above tool 'test_mongo_pipeline_query' for analyzing mongodb pipeline.

        You must respond with a single function call and mongodb pipeline and single function input. Multiple function calls are strictly prohibited. 

        EXAMPLES
        ----
        user_query: "How many users are there in given users collection?"
        AI Assistant:
        "action": "test_mongo_pipeline_query",
        "action_input": {{"mongodb_pipeline": "[{{"$group": {{"_id": None, "count": {{"$sum": 1}}}}]", "collection_name": "Users", "query_analysis_failed": False}}}}"
        

        Begin!

        user_query: {user_query}

        """
    )

def prepare_execution_tools(database_type : str = MONGODB) -> dict:
    if(database_type == MONGODB):
        return [{
            "type": "function",
            "function": {
                "name": "test_mongo_pipeline",
                "description": dedent(
                """
                function runs given query using PyMongo aggregation pipelines. It returns successful output or associated errors if pipeline is incorrect. 
                Args:
                    mongodb_pipeline: MongoDb pipeline which need to be test on given collection
                    collection_name: collection_name on which mongodb pipeline will run through pymongo.
                    query_analysis_failed : boolean parameter to specify if given user query is not related to generating mongo pipeline query.
                """),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "collection_name": {
                            "title": "Collection Name",
                            "description": "The collection_name specifies the MongoDB collection to query. The function will not operate without specifying the collection_name.",
                            "type": "string"
                        },
                        "mongodb_pipeline": {
                            "title": "MongoDb Pipeline",
                            "description": "The mongodb_pipeline is a list of aggregation commands that will be passed to the MongoDB aggregate function for the specified collection.",
                            "type": "string"
                        },
                        "query_analysis_failed" : {
                            "title": "Query analysis failed",
                            "description": "If the question is not related to creating a MongoDB pipeline query, then return true, else return false. If you have given some correction by user, do not mark correction as irrelevant and return false in this case.",
                            "type": "boolean",
                        },
                        
                    },
                    "required": [ "collection_name", "query_analysis_failed", "mongodb_pipeline"]
                }
            }
        }]
    else:
        raise Exception("Not Implemented")
    
def prepare_analyze_tools(user_query : str) -> list[dict]:
    return [{
        "type": "function",
        "function": {
            "name": "analyze_mongodb_pipeline",
            "description": "Analyze AI-generated pipeline queries for given conditions to avoid any kind of disruption. Make sure that, you provide all the required parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incorrect_query": {
                        "type": "boolean",
                        "description": dedent(
                        """
                        Please detect errors in a given AI-generated MongoDB pipeline query. Check for syntactic, logical, or other types of errors and returns `True` if any errors are found, otherwise it returns `False`. This AI-generated MongoDB pipeline query would be executed inside pymongo aggregate function. So, find errors according to that.
                        """)
                    },
                    "reason_for_incorrect_query": {
                        "type": "string",
                        "description": "Provide the reason for marking incorrect_query as true or false. Write in detailed. Provide the corrections. "
                    },
                    "intermediate_query": {
                        "type": "boolean",
                        "description": dedent(f"""If the given AI-generated PyMongoDB mongodb_pipeline is not able to fetch the data relevant to user query, then return true. If the mongodb_pipeline is empty or None, then return true. Otherwise, return false. Make sure that mongodb_pipeline is fetching data from multiple collection in single step to complete operation faster. Do not return true, if mongodb_pipeline is fetching data from multiple collection in single step.
                        """)
                    },
                    "reason_for_intermediate_query": {
                        "type": "string",
                        "description": "Provide the reason for marking intermediate_query as true or false. If the answer is false, explain why this is not an intermediate query."
                    },
                    "contains_DML_operation": {
                        "type": "boolean",
                        "description": "If the given AI-generated PyMongoDB mongodb_pipeline contains any kind of delete, modify, insert, or update operation, return true. Otherwise, return false."
                    },
                    "reason_for_contains_DML_operation": {
                        "type": "string",
                        "description": "Provide the reason for marking contains_DML_operation as true or false."
                    },
                    "contains_raw_output": {
                        "type": "boolean",
                        "description": "If the execution of the given AI-generated PyMongoDB mongodb_pipeline would result in the output of only raw data which is hard for the user to understand, then return true. For example, if running the pipeline query could result in only object IDs, then it is considered raw data. Hence, return true in that case."
                    },
                    "reason_for_contains_raw_output": {
                        "type": "string",
                        "description": "Provide the reason for marking contains_raw_output as true or false."
                    }
                },
                "required": ["intermediate_query", "contains_DML_operation", "contains_raw_output", "incorrect_query", "reason_for_incorrect_query", "reason_for_contains_raw_output", "reason_for_contains_DML_operation", "reason_for_intermediate_query"]
            }
        }
    }]


def generate_pipeline_query_msg(pipeline_query : list[dict], collection_name : str, query_analysis_failed : bool) -> str:
    if(query_analysis_failed == True):
        return dedent(
            "The question is not relevant to the current topic or discussion."
        )
    else:
        return dedent(
            f"""Here's the answer to your query:
            The AI-generated mongodb_pipeline is: {pipeline_query}
            It searches through the data in: "{collection_name}" collection"""
        )

def analyze_pipeline_query_user_msg(user_query : str, pipeline_query : list[dict], collection_name : str) -> str:
    return dedent(
        f"""Please review the following AI-generated query based on the given conditions in tool.
        The user's original question was: {user_query}

        The AI has created this MongoDB mongodb_pipeline command for the database:
        mongodb_pipeline command: {pipeline_query}
        This command searches the data in: {collection_name}"""
    )


def analyze_pipeline_query_assistant_msg() -> str:
    return dedent(
        """I've reviewed the AI-generated MongoDB pipeline commands and shared the results."""
    )

def analyze_pipeline_query_user_msg_seccond(output_message : list[str], generated_pipeline_query : list[dict]) -> str:
    output_string = "\n\n".join(output_message)
    return dedent(
        f"""I found a couple of problems with the AI-generated mongodb_pipeline:
        Issues are as follows :
        {output_string}

        Here is AI-generated mongodb_pipeline : 
        Please rectify it:
        {generated_pipeline_query}
        """
    )

def intermediate_query_error_msg(intermediate_query_reason : str) -> str:
    return dedent(
        f"""
            The current AI generated mongodb_pipeline command won't return all the relevant results for user question. This is because {intermediate_query_reason}. 
            Please update the search command to fix this issue. Also, mongodb_pipeline is none, make sure to provide proper query in tool_Call.
        """
    )

def contains_raw_output_error_msg(contains_raw_output_reason : str) -> str:
    return dedent(
        f"""
            The AI generated mongodb_pipeline includes some technical details and raw output that may be confusing. This is because {contains_raw_output_reason}. 
            Please modify the command to make the output easier to understand.
        """
    )


def contains_DML_operation_error_msg(contains_DML_operation_reason : str) -> str:
    return dedent(
        f"""
            The AI-generated mongodb_pipeline includes operations that could change, update or delete data. This is because {contains_DML_operation_reason}. 
            Please revise the command to remove any data modification operations.
        """
    )

def contains_error_msg(contains_incorrect_query_reason : str) -> str:
    return dedent(
        f"""
            The AI-generated mongodb_pipeline is not correct. This is because {contains_incorrect_query_reason}. 
            Please revise the command to avoid any error in fetching data. Also, mongodb_pipeline is none, make sure to provide proper query in tool_Call.
        """
    )

def execute_query_user_msg(reached_max_count : bool, max_output_count : int, output_data : list) -> str:
    if(reached_max_count == True):
        return dedent(
            f"""
            The AI-generated mongodb_pipeline worked and returned the following results:
            =========================================
            {str(json.dumps(output_data, indent=4))}
            =========================================

            However, your search returned more than {max_output_count} results. To keep the output manageable, only the first {max_output_count} results are shown above. Please take a look at the results above and try to format the output in an easy-to-read way for user. """)
    else:
        return dedent(
            f"""
            The AI-generated mongodb_pipeline worked and returned the following results:
            =========================================
            {str(json.dumps(output_data, indent=4))}
            =========================================

            Please take a look at the results above and try to format the output in an easy-to-read way for user. """)
    
def execute_query_user_error_msg(error_string : str) -> str:
    return dedent(
            f"""
            The AI-generated mongodb_pipeline did not worked and returned the following error results:
            =========================================
            {error_string}
            =========================================

            Please modify the AI-generated mongodb_pipeline accordingly to avoid errors. """)
    
def description_msg() -> str:
    return dedent("""
    Here are some refined guidelines for constructing a PyMongo pipeline query:

    1. Always use the User ID to look up information. If you only have details like an email or a Discord name, first find the User ID from the user database and use it to get information from other databases.

    2. MongoDB doesn't allow you to directly compare fields using simple operators like `$gte` or `$lte` in the `$match` stage. Instead, use the `$expr` operator, which lets you use more complex expressions to compare fields.

    3. Don't use `{'$date': 'date_string'}` in your queries. Simply use the date string directly, like `{'$gte': '2024-05-20T00:00:00Z', '$lte': '2024-06-10T23:59:59Z'}` or {'$gte': datetime.datetime(2024, 5, 20, 0, 0), '$lte': datetime.datetime(2024, 6, 10, 23, 59, 59)}}}, to filter by date correctly. 
    """)