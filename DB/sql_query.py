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

STATS_MOVIE_BY_GENRE_QUERY = query = """
    SELECT COUNT(*) AS movie_count, 
           AVG(rating_kp) AS avg_rating_kp, 
           AVG(rating_imdb) AS avg_rating_imdb
    FROM movies
    WHERE %s in genres
    """
