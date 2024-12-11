from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from langchain_community.vectorstores import FAISS



def create_rag_chain(retriever: FAISS) -> RunnablePassthrough:
    """Create a RAG chain from a retriever."""
    template = """
    Answer the question based on the following context:
    
    Context: {context}
    Question: {question}
    
    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt 
        | llm 
        | StrOutputParser()
    )

    return chain