import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from DB.db import init_db
from backend.router import router

app = FastAPI(title="Movie Recommendation Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Укажите адрес вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)
app.include_router(router)

#########################################
# Запуск сервера через uvicorn          #
#########################################


if __name__ == "__main__":
    init_db()  # Сначала инициализируем базу данных
    print("Starting server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=True)
