import chromadb
import os
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

chroma_client = chromadb.HttpClient(host='localhost', port=8010)

openai_api_key = os.getenv("OPENAI_API_KEY")

embedding_function = OpenAIEmbeddingFunction(
    api_key=openai_api_key,
    model_name="text-embedding-3-small",
    dimensions=384
)

collection = chroma_client.get_or_create_collection(
    name="cv_collection",
    embedding_function=embedding_function
)

job_collection = chroma_client.get_or_create_collection(
    name="job_collection",
    embedding_function=embedding_function
)