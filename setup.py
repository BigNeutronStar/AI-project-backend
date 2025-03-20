import os

from dotenv import load_dotenv
import openai
from langchain_openai import ChatOpenAI

load_dotenv()
kinopoisk_api_key = os.getenv("KINOPOISK_API_KEY")
if not kinopoisk_api_key:
    raise Exception("Переменная окружения KINOPOISK_API_KEY не установлена в файле .env.")


tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    raise Exception("Переменная окружения TAVILY_API_KEY не установлена в файле .env.")


openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise Exception("Переменная окружения OPENAI_API_KEY не установлена в файле .env.")


db_password = os.getenv("DB_PASSWORD")
if not db_password:
    raise Exception("Переменная окружения DB_PASSWORD не установлена в файле .env.")


llm = ChatOpenAI(model_name="o3-mini", openai_api_key=openai_api_key)
