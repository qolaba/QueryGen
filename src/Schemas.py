from pydantic import BaseModel
from src.Constant import MISTRAL_CODE_MODEL, MISTRAL_LLM_TEMPERATURE, MONGODB, OPENAI_GPT4_MODEL, description_msg
import os


class QueryInput(BaseModel):
    connection_url : str = os.environ["connection_url"]
    collection_list : list[str] = os.environ["collection_list"]
    database_name : str = os.environ["database_name"]
    description : str = description_msg()
    query : str = os.environ["query"]
    example_count : int = 10
    max_output_count : int = 30
    database_type : str = MONGODB
    llm_name : str = OPENAI_GPT4_MODEL
    temperature : float = MISTRAL_LLM_TEMPERATURE

class PipelineCode(BaseModel):
    mongodb_pipeline: list[dict] | None | str = None
    collection_name : str
    query_analysis_failed : bool = False

class QueryAnalyze(BaseModel):
    intermediate_query : bool
    reason_for_intermediate_query : str
    contains_DML_operation : bool
    reason_for_contains_DML_operation : str
    contains_raw_output : bool
    reason_for_contains_raw_output : str


class GraphState(BaseModel):
    error: bool
    messages: list
    generation: PipelineCode | None
    iterations: int

class TaskResponse(BaseModel):
    output: str | None = None
    error: str | None = None
    error_data: str | dict | None = None

class AnalyzeConditions(BaseModel):
    intermediate_query : bool
    reason_for_intermediate_query : str
    contains_DML_operation : bool
    reason_for_contains_DML_operation : str
    contains_raw_output : bool
    reason_for_contains_raw_output : str
    incorrect_query : bool
    reason_for_incorrect_query : str