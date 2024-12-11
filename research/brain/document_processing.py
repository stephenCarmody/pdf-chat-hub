from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader


def load_pdf(file_path: str) -> list:
    """Load a PDF file into a list of pages."""
    loader_py = PyMuPDFLoader(file_path)
    pages_py = loader_py.load()
    return pages_py


def chunk_docs(pages: list) -> list:
    """Chunk a list of pages into a list of documents."""
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=150, separator="\n")
    docs = text_splitter.split_documents(pages)
    return docs
