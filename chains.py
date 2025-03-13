from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA

from setup import openai_api_key
from vector import vector_store


def create_retrieval_chain():
    """
    Создаем цепочку RetrievalQA, которая использует OpenAI (через langchain-community) и FAISS для RAG.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return chain


retrieval_chain = create_retrieval_chain()
