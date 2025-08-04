import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("MISTRAL_API_KEY")
mistral_client = Mistral(api_key=api_key)

