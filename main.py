import os
import tempfile
import base64
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import uvicorn
import openai
from gtts import gTTS
from dotenv import load_dotenv

# Обновлённые импорты из langchain-community
from langchain_community.llms import OpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA



# Загружаем переменные окружения из .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise Exception("Переменная окружения OPENAI_API_KEY не установлена в файле .env.")
openai.api_key = openai_api_key

app = FastAPI(title="Movie Recommendation Backend")

# Пример данных о фильмах
movies = [
    {
        "title": "Комедия жизни",
        "genre": "Комедия",
        "description": "Легкий и веселый фильм о жизни с множеством комичных ситуаций.",
        "rating": 7.5,
    },
    {
        "title": "Драма судьбы",
        "genre": "Драма",
        "description": "Глубокая история с неожиданными поворотами судьбы, полная эмоций.",
        "rating": 8.0,
    },
    {
        "title": "Экшн-миссия",
        "genre": "Экшн",
        "description": "Напряженный фильм о борьбе с преступностью, с захватывающими погонями и битвами.",
        "rating": 7.8,
    },
    {
        "title": "Романтическая комедия",
        "genre": "Романтика, Комедия",
        "description": "Забавная история любви, наполненная юмором и забавными ситуациями.",
        "rating": 7.2,
    },
]

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

def create_retrieval_chain():
    """
    Создаем цепочку RetrievalQA, которая использует OpenAI (через langchain-community) и FAISS для RAG.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return chain

retrieval_chain = create_retrieval_chain()

#############################
# Часть 2. Определение моделей #
#############################

class MovieQuery(BaseModel):
    query: str

##############################################
# Часть 3. Реализация API эндпоинтов           #
##############################################

# 1. Текстовый интерфейс: поиск фильмов по запросу
@app.post("/search")
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
@app.post("/voice")
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
@app.post("/agent")
async def agent_task(query: MovieQuery):
    q_lower = query.query.lower()
    if "средний рейтинг" in q_lower:
        avg_rating = sum(movie["rating"] for movie in movies) / len(movies)
        return {"task": "средний рейтинг", "average_rating": round(avg_rating, 2)}
    elif "количество фильмов" in q_lower:
        return {"task": "количество фильмов", "count": len(movies)}
    else:
        return {"message": "Агент не смог распознать задачу. Попробуйте уточнить запрос."}

#########################################
# Запуск сервера через uvicorn          #
#########################################
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
