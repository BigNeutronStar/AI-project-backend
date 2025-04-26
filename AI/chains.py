from langchain.chains import RetrievalQA

from setup import llm
from AI.vector import vector_store


def create_retrieval_chain():
    """
    Создаем цепочку RetrievalQA, которая использует OpenAI (через langchain-community) и FAISS для RAG.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    return chain


retrieval_chain = create_retrieval_chain()
