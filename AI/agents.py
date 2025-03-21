from langgraph.prebuilt import create_react_agent
from AI.tools import tavily_tool, movie_stats_tool
from setup import llm
from langchain_core.prompts import ChatPromptTemplate


stats_prompt = ChatPromptTemplate.from_messages([
    (
        'system',
        "Твоя задача исключительно подсчет статистики. "
        "Если в пользовательском запросе нет упоминания статистики или ползователь в ней не нуждается, отвечай пустой "
        "строкой: ''."
        f"Если ты понял, что пользователю нужна дополнительная оинформация о статистике тогда с помощью своих "
        f"инструментов посчитай количество фильмов в жанрах которые упоминал пользователь и их средний рейтинг в "
        f"каждом жанре по кинопоиску и по IMDB"),
        ("placeholder", "{query}"),
    ])


search_prompt = ChatPromptTemplate.from_messages([
        (
            'system',
            "Твоя задача поиск фильмов в интернете по предпочтениям пользователя. "
            f"Если ты не нашел фильмов подходящих под запрос пользователя, то отвечай: 'К сожалению я не смог найти "
            f"подходящих фильмов в интернете'"
        ),
        ("placeholder", "{query}"),
    ]
)


# initialize the agent
search_agent = create_react_agent(
    llm,
    tools=[tavily_tool],
    prompt=search_prompt,
    # response_format=
)

movie_stats_agent = create_react_agent(
    llm,
    tools=[movie_stats_tool],
    prompt=stats_prompt,
    # response_format=
)
