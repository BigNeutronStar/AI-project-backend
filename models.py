from pydantic import BaseModel

#############################
# Часть 2. Определение моделей #
#############################


class MovieQuery(BaseModel):
    query: str
