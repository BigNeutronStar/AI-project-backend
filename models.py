from pydantic import BaseModel
from typing import List, Dict


class MovieQuery(BaseModel):
    query: str
    genres: Dict[str, List[str]]

    class Config:
        schema_extra = {
            "example": {
                "query": "история про супергероев",
                "genres": {
                    "favorite": ["фантастика", "боевик"],
                    "hated": ["ужасы", "мелодрама"]
                }
            }
        }
