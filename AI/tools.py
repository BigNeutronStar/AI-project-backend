from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain.agents import Tool

from DB.db import get_movies_stats_by_genres

search = TavilySearchAPIWrapper()
tavily_tool = TavilySearchResults(api_wrapper=search, max_results=10, include_answer=True)


#################################################################
# print(f"Name: {tavily_tool.name}")
# print(f"Description: {tavily_tool.description}")
# print(f"args schema: {tavily_tool.args}")
# print(f"returns directly?: {tavily_tool.return_direct}")
#################################################################


def compute_movie_stats(genre: str) -> str:
    """
    Функция принимает жанр и возвращает строку с количеством фильмов и средним рейтингом.
    Фильтрация осуществляется по вхождению жанра в поле 'genre'.
    """

    stats = get_movies_stats_by_genres(genre)

    if stats['movie_count'] == 0:
        return f"По жанру '{genre}' не найдено фильмов."

    return (f"По жанру '{genre}' найдено {stats['movie_count']} фильмов, средний рейтинг по кинопоиску: {stats['avg_rating_kp']}, "
            f"средний рейтинг по IMDB: {stats['avg_rating_imdb']}")


# Создаём tool для получения статистики
movie_stats_tool = Tool(
    name="MovieStatsTool",
    func=compute_movie_stats,
    description=(
        "Принимает в качестве входных данных название жанра и возвращает количество фильмов "
        "и средний рейтинг для этого жанра по кинопоиску и по IMDB. Если в запросе пользователя присутствуют слова "
        "'статистика', 'средний рейтинг', 'количество фильмов' или упоминания жанров, связанных с "
        "агрегированием, вызовите этот инструмент с нужным жанром. "
        "Если запрос подразумевает агрегирование по нескольким жанрам, можно вызывать инструмент для каждого жанра."
    )
)
