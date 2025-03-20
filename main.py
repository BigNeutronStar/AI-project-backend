import uvicorn
from fastapi import FastAPI
from router import router

app = FastAPI(title="Movie Recommendation Backend")
app.include_router(router)


#########################################
# Запуск сервера через uvicorn          #
#########################################
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=True)
