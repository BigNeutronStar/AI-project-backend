import psycopg2
from psycopg2.extras import RealDictCursor
from DB.sql_query import CREATE_TABLE_QUERY, INSERT_MOVIE_QUERY, STATS_MOVIE_BY_GENRE_QUERY
from setup import db_password

DB_CONFIG = {
    "dbname": "Film_Recomendation_Ai",
    "user": "postgres",
    "password": db_password,
    "host": "localhost",
    "port": 5432
}


def get_db_connection():
    """Создаёт и возвращает подключение к БД"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def init_db():
    """Создаёт таблицы в БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_QUERY)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized.")


def add_movie(movie):
    """Добавляет фильм в БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(INSERT_MOVIE_QUERY, movie)

    conn.commit()
    cursor.close()
    conn.close()


def fetch_movies():
    """Получает все фильмы из БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_movies_stats_by_genres(genre):
    """Возвращает количество фильмов, средний рейтинг по rating_kp и rating_imdb"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(STATS_MOVIE_BY_GENRE_QUERY, genre)
    result = cursor.fetchone()  # Получаем одну строку

    cursor.close()
    conn.close()

    return {
        "movie_count": result[0] or 0,
        "avg_rating_kp": round(result[1], 2) if result[1] else None,
        "avg_rating_imdb": round(result[2], 2) if result[2] else None
    }


def add_movies_from_metadata(metadata):
    print('====> ', 'Началось добавление данных в базу')

    for movie in metadata:
        add_movie(tuple(movie.values()))

    print('====> ', 'Закончилось добавление данных в базу')

