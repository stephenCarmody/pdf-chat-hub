from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader

# TODO: Finish class for DocumentParser


class PDFParser:
    def __init__(self, pdf_loader, text_splitter) -> None:
        self.pdf_loader = pdf_loader
        self.text_splitter = text_splitter

    def load_pdf(self, file_path: str) -> list:
        """Load a PDF file into a list of pages."""
        loader_py = PyMuPDFLoader(
            file_path
        )  # TODO: see if I can do this in the constructor and use the path later ?
        pages_py = loader_py.load()
        return pages_py

    def chunk_docs(pages: list) -> list:
        """Chunk a list of pages into a list of documents."""
        pass


def load_pdf(file_path: str) -> list:
    """Load a PDF file into a list of pages."""
    loader_py = PyMuPDFLoader(file_path)
    pages_py = loader_py.load()
    return pages_py


def chunk_docs(pages: list) -> list:
    """Chunk a list of pages into a list of documents."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, separators=[".", "?", "!"], chunk_overlap=200
    )
    docs = text_splitter.split_documents(pages)
    return docs
