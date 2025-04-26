from pydantic import BaseModel
from typing import List, Dict


class MovieQuery(BaseModel):
    query: str
    genres: Dict[str, List[str]]

    class Config:
        json_schema_extra = {
            "example": {
                "query": "история про супергероев",
                "genres": {
                    "favorite": ["фантастика", "боевик"],
                    "hated": ["ужасы", "мелодрама"]
                }
            }
        }


class MovieResponse(BaseModel):
    query: str
    answer: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "история про супергероев",
                "answer": "Могу порекомендовать фильм 'Человек Паук' ..."
            }
        }


class VoiceQuery(BaseModel):
    transcription: str
    genres: Dict[str, List[str]]

    class Config:
        json_schema_extra = {
            "example": {
                "transcription": "Порекомендуй фильм про супергероев",
                "genres": {
                    "favorite": ["фантастика", "боевик"],
                    "hated": ["ужасы", "мелодрама"]
                }
            }
        }


class VoiceResponse(BaseModel):
    answer: str
    audio_base64: str

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Отлично, как могу помочь?",
                "audio_base64": "UklGRlwAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YU4AAAAA..."  # сокращенный пример
            }
        }
