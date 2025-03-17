from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

from setup import openai_api_key
from vector import vector_store


def create_retrieval_chain():
    """
    Создаем цепочку RetrievalQA, которая использует OpenAI (через langchain-community) и FAISS для RAG.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    llm = ChatOpenAI(model_name="o3-mini", openai_api_key=openai_api_key)
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return chain


retrieval_chain = create_retrieval_chain()
