import logging
import os
import tempfile
import base64
from fastapi import HTTPException, File, UploadFile, APIRouter
from pydantic import BaseModel
import uvicorn
import openai
from dotenv import load_dotenv

# Импорт ваших цепочек и моделей
from chains import retrieval_chain
from models import MovieQuery

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная с выбранным жанром (передается с фронтенда)
selected_genre = "Драма"

router = APIRouter()

def compare_genre(user_query: str, selected_genre: str) -> int:
    """
    Делает запрос к ChatGPT для сравнения жанра, указанного в запросе пользователя, с выбранным жанром.
    Если жанры совпадают или жанр не указан, возвращает 0; если различаются — 1.
    """
    prompt = (
        "Проверь, совпадает ли жанр, указанный в следующем запросе пользователя, с жанром, выбранным на фронтенде. "
        "Если жанр в запросе не указан или жанры совпадают, верни 0. Если жанры различаются, верни 1.\n"
        f"Запрос пользователя: '{user_query}'\n"
        f"Выбранный жанр: '{selected_genre}'\n"
        "Ответ должен быть только числом 0 или 1."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        value = int(result)
        if value not in (0, 1):
            return 0
        return value
    except Exception as e:
        logger.error(f"Ошибка в compare_genre: {e}")
        return 0

def wrap_prompt(user_query: str, selected_genre: str) -> str:
    """
    Оборачивает запрос пользователя в промпт для ChatGPT.
    Если функция compare_genre возвращает 0 (жанры совпадают), используется выбранный жанр.
    Если возвращается 1, жанр из глобальной переменной не используется.
    Кроме того, если в запросе содержится слово "сериал", в промпт подставляется "сериал(ы)",
    иначе используется "фильм(ы)".
    """
    cmp_result = compare_genre(user_query, selected_genre)
    if cmp_result == 0:
        genre_clause = f"используя жанр: {selected_genre}"
    else:
        extracted_genre = extract_genre(user_query)
        genre_clause = f"используя жанр: {extracted_genre}" if extracted_genre else f"используя жанр: {selected_genre}"
    
    # Определяем тип контента: сериал или фильм
    if "сериал" in user_query.lower():
        content_type = "сериал(ы)"
    elif "фильм" in user_query.lower():
        content_type = "фильм(ы)"
    else:
        content_type = "фильм(ы)"  # или другой вариант по умолчанию

    prompt = (
        "Ты - эксперт по подбору фильмов и сериалов. Отвечай только по теме кино и сериалов. "
        "Если вопрос не связан с кино, отвечай: 'не могу помочь с данным вопросом, но могу порекомендовать фильм или сериал'. "
        f"Пользователь попросил: {user_query}. "
        f"Порекомендуй {content_type} с учетом предпочтений, {genre_clause}."
    )
    return prompt


@router.post("/search")
async def search_movies(query: MovieQuery):
    if len(query.query.split()) < 3:
        return {"error": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста."}
    try:
        wrapped_prompt = wrap_prompt(query.query, selected_genre)
        answer = retrieval_chain.run(wrapped_prompt)
        return {"query": query.query, "wrapped_prompt": wrapped_prompt, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice")
async def voice_interface(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription_result = openai.Audio.transcribe("whisper-1", audio_file)
        transcription_text = transcription_result.get("text", "").strip()
        if not transcription_text:
            return {"error": "Не удалось распознать речь."}

        answer = retrieval_chain.run(transcription_text)

        from gtts import gTTS
        tts = gTTS(text=answer, lang="ru")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
            tts.save(tts_file.name)
            tts_file_path = tts_file.name

        with open(tts_file_path, "rb") as audio_out:
            audio_bytes = audio_out.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        os.remove(tmp_path)
        os.remove(tts_file_path)

        return {
            "transcription": transcription_text,
            "answer": answer,
            "audio_answer_base64": audio_base64,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
