from langgraph.prebuilt import create_react_agent
from AI.tools import tavily_tool, movie_stats_tool
from setup import llm


# initialize the agent
search_agent = create_react_agent(llm, tools=[tavily_tool])

movie_stats_agent = create_react_agent(llm, tools=[movie_stats_tool])
