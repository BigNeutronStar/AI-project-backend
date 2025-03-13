from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from example_data import movies
from setup import openai_api_key


#########################################
# Часть 1. Настройка Retrieval с LangChain #
#########################################

def build_vector_store():
    """
    Создаем векторное хранилище (FAISS) на основе описаний фильмов.
    """
    texts = [movie["description"] for movie in movies]
    metadatas = [
        {"title": movie["title"], "genre": movie["genre"], "rating": movie["rating"]}
        for movie in movies
    ]
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    return vector_store


vector_store = build_vector_store()
