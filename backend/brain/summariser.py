from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class SummaryChain:
    def __init__(self):
        prompt = ChatPromptTemplate.from_template("Summarize this content: {context}")
        # Define LLM chain
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        self.chain = create_stuff_documents_chain(llm, prompt)

    def run(self, context: str):
        return self.chain.invoke({"context": context})
