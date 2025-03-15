import logging

from requests import RequestException, get

from setup import kinopoisk_api_key

api_url = "https://api.kinopoisk.dev/v1.4/"


def get_movies(pages_start=1, pages_count=1):
    get_movies_url = api_url + "movie?page=1&limit=250&selectFields=id&selectFields=name&selectFields=shortDescription&selectFields=type&selectFields=year&selectFields=rating&selectFields=status&selectFields=genres&selectFields=countries&selectFields=persons&selectFields=similarMovies&notNullFields=name&notNullFields=shortDescription&notNullFields=rating.kp&notNullFields=genres.name&notNullFields=persons.name&year=1990-2025&rating.kp=6-10"
    all_movies = []
    all_count = 0

    for i in range(pages_start, pages_start + pages_count):
        try:
            response = get(get_movies_url, headers={"X-API-KEY": kinopoisk_api_key})
            response.raise_for_status()

            movies = response.json()

            all_movies += movies['docs']
            all_count += movies['total']

        except RequestException as e:
            logging.error(f"Request failed for page {i}: {str(e)}")
            break  # или continue для пропуска ошибки

        except ValueError as e:
            logging.error(f"JSON parsing error for page {i}: {str(e)}")
            break

        except Exception as e:
            logging.error(f"Unexpected error for page {i}: {str(e)}")
            break

    print('====> получено ', all_count, ' фильмов')
    return all_movies, all_count


# {'id': 7238541, 'name': 'Триумф любви', 'type': 'tv-series', 'year': 2024,
# 'shortDescription': 'Сын губернатора узнает о предательстве невесты и покойного отца. Страстная дорама режиссера «Юность, подожди!»',
# 'status': 'completed',
# 'rating': {'kp': 6.955, 'imdb': 7.5, 'filmCritics': 0, 'russianFilmCritics': 0, 'await': None},
# 'genres': [{'name': 'мелодрама'}],
# 'countries': [{'name': 'Китай'}],
# 'persons': [{'id': 7201344, 'photo': 'https://image.openmoviedb.com/kinopoisk-st-images//actor_iphone/iphone360_7201344.jpg', 'name': 'Ли Жотянь', 'enName': 'Li Ruotian', 'description': 'Xue Dongfeng', 'profession': 'актеры', 'enProfession': 'actor'}]}
