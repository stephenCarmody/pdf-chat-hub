import os

import dotenv
import yaml
from langchain_core.documents import Document

from brain.document_processing import chunk_docs, load_pdf
from brain.model_router import create_router
from brain.rag import create_rag_chain
from brain.summariser import create_summary_chain
from brain.vector_db import create_db, create_retriever

dotenv.load_dotenv()

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

file_path = os.path.join(os.path.dirname(__file__), config['DOCS_DIR'], config['TEST_FILE'])

if __name__ == "__main__":
    print("Hello, World!")

    pages = load_pdf(file_path)
    docs = chunk_docs(pages)
    
    db = create_db(docs)
    retriever = create_retriever(db)

    rag_chain = create_rag_chain(retriever)

    
    router = create_router()

    while True:
        query = input("Enter a question (or 'quit' to exit): ")
        
        if query.lower() == 'quit':
            print("Goodbye!")
            break
            
        result = router.invoke(query)
        
        if result.task.lower() == "q_and_a":
            result = rag_chain.invoke(query)
        elif result.task.lower() == "summary":
            full_text = "\n".join([page.page_content for page in pages])
            document = [Document(page_content=full_text, metadata={})]

            # Create and use the summary chain
            summary_chain = create_summary_chain()
            result = summary_chain.invoke({"context": document})
        else:
            print("Invalid task")
            continue

        print(result)
        print("\n" + "-"*50 + "\n")  # Add separator between questions
