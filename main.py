from dotenv import load_dotenv

load_dotenv()


from fastapi import Depends, FastAPI
from src.Exception import handle_exceptions
from src.Container import Container
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from src.Schemas import TaskResponse, QueryInput
from src.utils import check_token
from src.Constant import MONGODB, MISTRAL_CODE_MODEL, OPENAI_GPT4_MODEL
import uvicorn


app = FastAPI()
auth_scheme = HTTPBearer()
container = Container()

@app.post("/analyze_db")
@handle_exceptions
def index_data(
    input_data: QueryInput,
    api_key: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    
    check_token(api_key)
    if(input_data.llm_name == MISTRAL_CODE_MODEL):
        llm = container.mistral_llm()
    elif(input_data.llm_name == OPENAI_GPT4_MODEL):
        llm = container.openai_llm()
    else:
        raise Exception("Not Implemented")
    
    if(input_data.database_type == MONGODB):
        database = container.mongo_client(input_data.connection_url, input_data.database_name)
    else:
        raise Exception("Not Implemented")
    
    db_agent = container.db_agent(llm, database)
    result = db_agent.execute_agent(input_data)

    task_response = TaskResponse()
    task_response.output = result

    return JSONResponse(content=task_response.model_dump(), status_code=200)
   

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        timeout_keep_alive=9000,
    )
