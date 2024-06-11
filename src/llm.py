from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from src.Schemas import PipelineCode
from mistralai.models.chat_completion import ChatCompletionResponse
import json
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

class BaseLLM:
    def __init__(self) -> None:
        pass

    def get_chat_message(self) -> None:
        pass

    def get_chat_content(self) -> dict:
        pass

    def invoke(self) -> None:
        pass

class MistralLLM(BaseLLM):
    def __init__(self, mistral_client : MistralClient) -> None:
        self.mistral_client = mistral_client

    def get_chat_message(self, content : str, role : str) -> ChatMessage:
        return ChatMessage(role=role, content=content)
    
    def get_chat_content(self, message : ChatMessage) -> dict:
        return message.content
    
    def invoke(self, model : str, messages : list[ChatMessage], temperature : float, tools : dict = None, return_tool : bool = True) -> ChatCompletionResponse | dict:
        print("--------------")
        print(self.get_chat_content(messages[-1]))
        print("--------------")
        
        response = self.mistral_client.chat(model=model, messages=messages, tools=tools, tool_choice="any", temperature = temperature)
        if(return_tool == True):
            tool_call = response.choices[0].message.tool_calls

            function_call_argument = json.loads(tool_call[0].function.arguments)

            print("==============")
            print(function_call_argument)
            print("==============")

            return function_call_argument
        else:
            print("==============")
            print(response.choices[0].message.content)
            print("==============")
            return response.choices[0].message.content


class OpenAILLM(BaseLLM):
    def __init__(self, openai_client : OpenAI) -> None:
        self.openai_client = openai_client

    def get_chat_message(self, content : str, role : str) -> dict:
        return {"role": role, "content": content}
    
    def get_chat_content(self, message : dict) -> dict:
        return message["content"]
    
    def invoke(self, model : str, messages : list[dict], temperature : float, tools : dict = None, return_tool : bool = True) ->  ChatCompletion | dict:
        if(return_tool == True):
            print("--------------")
            print(self.get_chat_content(messages[-1]))
            print("--------------")
            response = self.openai_client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="required",  temperature = temperature)

            tool_call = response.choices[0].message.tool_calls
            function_call_argument = json.loads(tool_call[0].function.arguments)

            print("==============")
            print(function_call_argument)
            print("==============")
            return function_call_argument
        else:
            print("--------------")
            print(self.get_chat_content(messages[-1]))
            print("--------------")
            response = self.openai_client.chat.completions.create(model=model, messages=messages, temperature = temperature)
            print("==============")
            print(response.choices[0].message.content)
            print("==============")
            return response.choices[0].message.content