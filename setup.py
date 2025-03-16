import os

from dotenv import load_dotenv
import openai

load_dotenv()
kinopoisk_api_key = os.getenv("KINOPOISK_API_KEY")

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise Exception("Переменная окружения OPENAI_API_KEY не установлена в файле .env.")

