import asyncio
import os

from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from DB.db import add_movies_from_metadata
from external_api.api import get_movies
from setup import openai_api_key


#########################################
# Часть 1. Настройка Retrieval с LangChain #
#########################################

VECTOR_STORE_PATH = "movie_vector_store"


def get_vector_store():
    """
    Создаем векторное хранилище (FAISS) на основе описаний фильмов.
    """
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    if os.path.exists(VECTOR_STORE_PATH):
        return FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)

    movies = get_movies(1, 40)

    texts = [movie["shortDescription"] for movie in movies]
    metadatas = [{
        "name": movie["name"],
        "type": movie.get("type"),
        "genres": [genre["name"] for genre in movie["genres"]],
        "rating_kp": movie["rating"]["kp"],
        "rating_imdb": movie["rating"].get("imdb"),
        "year": movie["year"],
        "actors": [person["name"] for person in movie["persons"] if person["enProfession"] == 'actor'],
        "countries": [country["name"] for country in movie["countries"]],
    } for movie in movies]


    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vector_store.save_local(VECTOR_STORE_PATH)

    print('====> ', 'В векторное хранилище записано ', len(movies), ' фильмов')

    add_movies_from_metadata(metadatas)

    return vector_store


vector_store = get_vector_store()

