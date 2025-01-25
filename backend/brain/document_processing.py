from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader


class DocumentProcessor:
    DEFAULT_SPLITTER_KWARGS = {
        "chunk_size": 500,
        "separators": [".", "?", "!"],
        "chunk_overlap": 200,
    }

    def __init__(
        self,
        document_loader=PyMuPDFLoader,
        text_splitter=RecursiveCharacterTextSplitter,
        text_splitter_kwargs=None,
    ) -> None:
        self.document_loader = document_loader
        self.text_splitter = text_splitter

        # Merge default kwargs with any provided kwargs, preferring provided ones
        self.text_splitter_kwargs = {
            **self.DEFAULT_SPLITTER_KWARGS,
            **(text_splitter_kwargs or {}),
        }

    def load_pdf(self, file_path: str) -> list:
        """Load a PDF file into a list of pages."""
        loader_py = self.document_loader(file_path)
        pages_py = loader_py.load()
        return pages_py

    def chunk_docs(self, pages: list) -> list:
        """Chunk a list of pages into a list of documents."""
        text_splitter = self.text_splitter(**self.text_splitter_kwargs)
        docs = text_splitter.split_documents(pages)
        return docs
