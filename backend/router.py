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
        "Если ты не нашел подходящих фильмов или сериалов под запрос пользователя то ответь так 'Извините, "
        "к сожалению, я не смог найти подходящих фильмов или сериалов'"
        f"Пользователь попросил: {user_query}. "
        f"Порекомендуй фильм(ы) или сериал(ы) с учетом предпочтений. {genre_clause}"
        "К фильму добавляй его рейтинг на IMDB и подписывай, что рейтинг взят с IMDB. "
    )
    return prompt


@router.post("/search", response_model=MovieResponse)
async def search_movies(query: MovieQuery):
    if len(query.query.strip().split()) < 3:
        return {"answer": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста.", 'query': query.query}
    try:
        wrapped_prompt = wrap_prompt(query.query, query.genres)
        answer = retrieval_chain.invoke(wrapped_prompt).get('result', '')

        if not answer or any(phrase in answer.lower() for phrase in ["не найден", "не смог", "нет похожих", "ничего не найдено", "не найдено"]):
            answer = search_agent.invoke(wrapped_prompt).get('result', '')
            logger.error('2====> ')
            logger.error(answer)

        stats_agent_answer_agent = await movie_stats_agent.ainvoke(input=query)
        stats_agent_answer = stats_agent_answer_agent['messages'][0].text()
        logger.error('3====> ')
        logger.error(stats_agent_answer_agent['messages'][0].text())

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
