from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)


class PromptManager:
    def __init__(self, messages=[], model="gpt-4o-mini"):
        self.messages = messages
        self.model = model

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
    
    def set_messages(self, messages):
        self.messages = messages

    def get_messages(self):
        return self.messages

    def generate(self):
        response = client.chat.completions.create(
            model=self.model, messages=self.messages, temperature=0.1
        )
        return response.choices[0].message.content
    
    def generate_structure(self, schema):
        response = client.beta.chat.completions.parse(
            model=self.model, messages=self.messages, response_format=schema, temperature=0.1
        )
        result = response.choices[0].message.model_dump() 
        content = json.loads(result['content'])
        return content