import base64
import os
import tempfile
from gtts import gTTS
from fastapi import HTTPException, File, UploadFile, APIRouter
import openai
from chains import retrieval_chain
from models import MovieQuery

##############################################
# Часть 3. Реализация API эндпоинтов           #
##############################################

router = APIRouter()


# 1. Текстовый интерфейс: поиск фильмов по запросу
@router.post("/search")
async def search_movies(query: MovieQuery):
    # Если запрос слишком короткий – считаем его неоднозначным
    if len(query.query.split()) < 3:
        return {"error": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста."}
    try:
        answer = retrieval_chain.run(query.query)
        # Возвращаем ответ, сгенерированный с учетом найденных описаний фильмов
        return {"query": query.query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. Голосовой интерфейс: получение аудиофайла, распознавание речи и синтез ответа
@router.post("/voice")
async def voice_interface(file: UploadFile = File(...)):
    try:
        # Сохраняем полученный аудиофайл во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Используем OpenAI Whisper для транскрибирования аудио
        with open(tmp_path, "rb") as audio_file:
            transcription_result = openai.Audio.transcribe("whisper-1", audio_file)
        transcription_text = transcription_result.get("text", "").strip()
        if not transcription_text:
            return {"error": "Не удалось распознать речь."}

        # Обрабатываем транскрибированный текст через RetrievalQA цепочку
        answer = retrieval_chain.run(transcription_text)

        # Синтезируем голосовой ответ с помощью gTTS
        tts = gTTS(text=answer, lang="ru")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_file:
            tts.save(tts_file.name)
            tts_file_path = tts_file.name

        # Кодируем аудиофайл ответа в base64 для отправки в JSON
        with open(tts_file_path, "rb") as audio_out:
            audio_bytes = audio_out.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Удаляем временные файлы
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
