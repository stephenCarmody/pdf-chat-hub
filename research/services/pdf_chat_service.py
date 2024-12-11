
class PDFChatService:
    def __init__(self):
        pass

    def query(self, query: str):
        """
        Query the document with a question / task.
        """
        return "Hello, World!, " + query

    def upload(self, file: bytes) -> None:
        """
        Upload a PDF file to the service. Resets the chat history.
        """
        pass