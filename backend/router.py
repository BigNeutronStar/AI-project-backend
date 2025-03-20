import io
import logging
from typing import Dict, List

from fastapi import APIRouter

from openai import OpenAI

import base64
from fastapi import HTTPException
from gtts import gTTS

from AI.agents import search_agent, movie_stats_agent
from AI.chains import retrieval_chain
from backend.models import MovieQuery, MovieResponse, VoiceResponse, VoiceQuery

client = OpenAI()

logger = logging.getLogger(__name__)

router = APIRouter()


def wrap_prompt(user_query: str, genres: Dict[str, List[str]]) -> str:
    """
    Формирует промпт для ChatGPT на основе запроса пользователя.
    Если в запросе не указано слово "жанр", добавляется условие использовать выбранный жанр.
    """
    like_genres = genres["favorite"]
    unlike_genres = genres["hated"]

    genre_clause = ''
    if len(like_genres) > 0:
        genre_clause += f'Вот жанры, которые НРАВЯТСЯ пользователю: {like_genres}. '
    if len(unlike_genres) > 0:
        genre_clause += f'Вот жанры, которые НЕ НРАВЯТСЯ пользователю: {unlike_genres}. '

    prompt = (
        "Ты - эксперт по подбору фильмов и сериалов. Отвечай только по теме кино и сериалов. "
        "Если вопрос не связан с кино, отвечай: 'не могу помочь с данным вопросом, но могу порекомендовать фильм или "
        "сериал'."
        f"Пользователь попросил: {user_query}. "
        f"Порекомендуй фильм(ы) или сериал(ы) с учетом предпочтений. {genre_clause}"
        "К фильму добавляй его рейтинг на IMDB и подписывай, что рейтинг взят с IMDB. "
    )
    return prompt


def wrap_prompt_for_stats(user_query: str) -> str:
    """
    Формирует промпт для Агента подсчитывающего статистику на основе запроса пользователя.
    """

    prompt = (
        "Твоя задача исключительно подсчет статистики. "
        "Если в пользовательском запросе нет упоминания статистики или ползователь в ней не нуждается, отвечай пустой "
        "строкой: ''."
        f"Если ты понял, что пользователю нужна дополнительная оинформация о статистике тогда с помощью своих "
        f"инструментов посчитай количество фильмов в жанрах которые упоминал пользователь и их средний рейтинг в "
        f"каждом жанре по кинопоиску и по IMDB"
        f"Пользователь попросил: {user_query}. "
    )
    return prompt


@router.post("/search", response_model=MovieResponse)
async def search_movies(query: MovieQuery):
    if len(query.query.strip().split()) < 3:
        return {"answer": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста.", 'query': query.query}
    try:
        wrapped_prompt = wrap_prompt(query.query, query.genres)
        answer = retrieval_chain.invoke(wrapped_prompt)

        if not answer or any(phrase in answer.lower() for phrase in ["не найден", "нет похожих", "ничего не найдено", "не найдено"]):
            answer = search_agent.invoke(wrapped_prompt)

        stats_agent_answer = await movie_stats_agent.ainvoke(wrap_prompt_for_stats(query.query))

        return {"query": query.query, "answer": answer + '\n' + stats_agent_answer}
    except Exception as e:
        logger.error(f"Ошибка в /search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TODO: разделить на 2 различных эндпоинта
# один для файла
# второй для ответа от гпт (возможно вместо второго стоит использовать эндпоинт /search)
@router.post("/voice",
             response_model=VoiceResponse,
             responses={
                 200: {
                     "content": {"application/json": {"example": VoiceResponse.Config.json_schema_extra["example"]}},
                     "description": "Success response with audio data"
                 },
                 500: {"description": "Internal server error"}
             },
             )
async def voice_interface(query: VoiceQuery):
    try:

        # Обработка запроса
        answer = await retrieval_chain.arun(wrap_prompt(query.transcription, query.genres))

        # Генерация аудио в памяти
        with io.BytesIO() as audio_buffer:
            tts = gTTS(text=answer, lang="ru")
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_base64 = base64.b64encode(audio_buffer.read()).decode()

        return {
            "answer": answer,
            "audio_base64": audio_base64
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Processing error")

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
