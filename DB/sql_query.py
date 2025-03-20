CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    genres TEXT[] NOT NULL,
    rating_kp FLOAT,
    rating_imdb FLOAT,
    year INTEGER,
    actors TEXT[],
    countries TEXT[]
);
"""

INSERT_MOVIE_QUERY = """
INSERT INTO movies (name, type, genres, rating_kp, rating_imdb, year, actors, countries)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING id;
"""
