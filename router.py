import logging
import os
import tempfile
import base64
from fastapi import HTTPException, File, UploadFile, APIRouter
from pydantic import BaseModel
import uvicorn
from openai import OpenAI
from setup import *

import os
import base64
import tempfile
import asyncio
from fastapi import HTTPException, UploadFile, File
from gtts import gTTS
import openai


client = OpenAI()
from dotenv import load_dotenv

# Импорт ваших цепочек и моделей
from chains import retrieval_chain
from models import MovieQuery

logger = logging.getLogger(__name__)

# Глобальная переменная с выбранным жанром (передается с фронтенда)
selected_genre = "Драма"

router = APIRouter()

def wrap_prompt(user_query: str, selected_genre: str) -> str:
    """
    Формирует промпт для ChatGPT на основе запроса пользователя.
    Если в запросе не указано слово "жанр", добавляется условие использовать выбранный жанр.
    """
    if "жанр" not in user_query.lower():
        genre_clause = f"Если в запросе не указан жанр, используй жанр \"{selected_genre}\". "
    else:
        genre_clause = ""

    prompt = (
        "Ты - эксперт по подбору фильмов и сериалов. Отвечай только по теме кино и сериалов. "
        "Если вопрос не связан с кино, отвечай: 'не могу помочь с данным вопросом, но могу порекомендовать фильм или сериал'. "
        f"Пользователь попросил: {user_query}. "
        f"Порекомендуй фильм(ы) или сериал(ы) с учетом предпочтений. {genre_clause}"
        "К фильму добавляй его рейтинг на IMDB и подписывай, что рейтинг взят с IMDB. "

    )
    return prompt

@router.post("/search")
async def search_movies(query: MovieQuery):
    if len(query.query.strip().split()) < 3:
        return {"error": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста."}
    try:
        wrapped_prompt = wrap_prompt(query.query, selected_genre)
        # Убедитесь, что retrieval_chain не сохраняет историю; по умолчанию каждый вызов создаёт новое обращение
        answer = retrieval_chain.invoke(wrapped_prompt)
        return {"query": query.query, "wrapped_prompt": wrapped_prompt, "answer": answer}
    except Exception as e:
        logger.error(f"Ошибка в /search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice")
async def voice_interface(file: UploadFile = File(...)):
    tmp_path = None
    tts_file_path = None
    try:
        # Сохраняем аудиофайл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", mode="wb") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Транскрибирование с асинхронным клиентом OpenAI
        client = openai.AsyncOpenAI()
        with open(tmp_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        transcription_text = transcription.text.strip()
        if not transcription_text:
            return {"error": "Не удалось распознать речь."}

        # Получаем ответ (предполагаем, что retrieval_chain поддерживает async)
        answer = await retrieval_chain.arun(transcription_text)

        # Асинхронный синтез речи
        loop = asyncio.get_event_loop()
        tts = gTTS(text=answer, lang="ru")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", mode="wb") as tts_file:
            tts_file_path = tts_file.name
            await loop.run_in_executor(None, tts.save, tts_file_path)

        # Кодируем в base64
        with open(tts_file_path, "rb") as audio_out:
            audio_base64 = base64.b64encode(audio_out.read()).decode("utf-8")

        return {
            "transcription": transcription_text,
            "answer": answer,
            "audio_answer_base64": audio_base64,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")
    finally:
        # Гарантированное удаление временных файлов
        for path in [tmp_path, tts_file_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Ошибка удаления файла {path}: {str(e)}")

# 3. Эндпоинт для агентов: выполнение дополнительных задач
# @router.post("/agent")
# async def agent_task(query: MovieQuery):
#     q_lower = query.query.lower()
#     if "средний рейтинг" in q_lower:
#         avg_rating = sum(movie["rating"] for movie in movies) / len(movies)
#         return {"task": "средний рейтинг", "average_rating": round(avg_rating, 2)}
#     elif "количество фильмов" in q_lower:
#         return {"task": "количество фильмов", "count": len(movies)}
#     else:
#         return {"message": "Агент не смог распознать задачу. Попробуйте уточнить запрос."}
