import os
import tempfile
import numpy as np
import logging
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import uvicorn
import openai
from dotenv import load_dotenv
from typing import List, Any

# Импорты из langchain-community
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# Импорт необходимых классов для создания кастомного retriever'а
from langchain.schema import BaseRetriever, Document

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из файла .env
load_dotenv()
# Убедитесь, что переменная окружения OPENAI_API_KEY установлена
if not os.getenv("OPENAI_API_KEY"):
    raise Exception("Переменная окружения OPENAI_API_KEY не установлена в файле .env.")
openai.api_key = os.getenv("OPENAI_API_KEY")

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

############################################
# Часть 1. Реализация кастомного retriever'а
############################################

class SimpleRetriever(BaseRetriever):
    texts: List[str]
    metadatas: List[Any]
    k: int = 2
    embeddings_model: Any
    embeddings: List[np.ndarray] = []

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, texts: List[str], metadatas: List[Any], embeddings_model: Any, k: int = 2):
        data = {
            "texts": texts,
            "metadatas": metadatas,
            "k": k,
            "embeddings_model": embeddings_model,
        }
        super().__init__(**data)
        try:
            self.embeddings = [np.array(vec) for vec in embeddings_model.embed_documents(texts)]
        except Exception as e:
            logger.error(f"Ошибка при вычислении эмбеддингов: {e}")
            raise

    def get_relevant_documents(self, query: str) -> List[Document]:
        try:
            query_embedding = np.array(self.embeddings_model.embed_query(query))
        except Exception as e:
            logger.error(f"Ошибка при вычислении эмбеддинга для запроса: {e}")
            raise
        scores = []
        for emb in self.embeddings:
            sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            scores.append(sim)
        top_k_indices = np.argsort(scores)[-self.k:][::-1]
        docs = []
        for i in top_k_indices:
            docs.append(Document(page_content=self.texts[i], metadata=self.metadatas[i]))
        return docs

    @property
    def search_kwargs(self):
        return {"k": self.k}

def build_retriever():
    texts = [movie["description"] for movie in movies]
    metadatas = [
        {"title": movie["title"], "genre": movie["genre"], "rating": movie["rating"]}
        for movie in movies
    ]
    embeddings_model = OpenAIEmbeddings()
    retriever = SimpleRetriever(texts, metadatas, embeddings_model, k=2)
    return retriever

def create_retrieval_chain():
    """
    Создаем цепочку RetrievalQA, используя наш кастомный retriever.
    """
    retriever = build_retriever()
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    try:
        chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    except Exception as e:
        logger.error(f"Ошибка при создании цепочки RetrievalQA: {e}")
        raise
    return chain

retrieval_chain = create_retrieval_chain()

#############################
# Часть 2. Определение моделей
#############################

class MovieQuery(BaseModel):
    query: str

##############################################
# Часть 3. Реализация API эндпоинтов
##############################################

@app.post("/search")
async def search_movies(query: MovieQuery):
    if len(query.query.split()) < 3:
        return {"error": "Запрос слишком короткий или неоднозначный, уточните, пожалуйста."}
    try:
        answer = retrieval_chain.invoke({"query": query.query})
        return {"query": query.query, "answer": answer}
    except Exception as e:
        logger.error(f"Ошибка в /search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice")
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

        try:
            answer = retrieval_chain.invoke({"query": transcription_text})
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса после транскрипции: {e}")
            raise

        os.remove(tmp_path)

        return {
            "transcription": transcription_text,
            "answer": answer,
            "note": "Голосовой ответ (синтез аудио) временно не генерируется."
        }
    except Exception as e:
        logger.error(f"Ошибка в /voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
