from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from setup import openai_api_key
from vector import vector_store

def create_retrieval_chain():
    """
    Создаем ConversationalRetrievalChain, которая использует память для сохранения контекста диалога.
    """
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    llm = ChatOpenAI(model_name="o3-mini", openai_api_key=openai_api_key)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory)
    return chain

retrieval_chain = create_retrieval_chain()
