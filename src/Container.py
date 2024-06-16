from dependency_injector import containers, providers
from src.DBReader import MongoReader
import os
from mistralai.client import MistralClient
from src.llm import MistralLLM, OpenAILLM
from src.DBAgent import DBQueryAgent
from openai import OpenAI


class Container(containers.DeclarativeContainer):
    mongo_client = providers.Factory(
        MongoReader
    )

    mistral_client = providers.Singleton(
        MistralClient, api_key = os.environ["MISTRALAI_API_KEY"]
    )

    openai_client = providers.Singleton(
        OpenAI, api_key = os.environ["OPENAI_API_KEY"]
    )

    mistral_llm = providers.Singleton(
        MistralLLM, mistral_client = mistral_client
    )

    openai_llm = providers.Singleton(
        OpenAILLM, openai_client = openai_client
    )
    

    db_agent = providers.Factory(
        DBQueryAgent
    )
