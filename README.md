# Chat with PDFs

[https://www.pdfchathub.com/](https://www.pdfchathub.com/)

This is a simple chatbot that can answer questions about a PDF file.

## Warning

As this is a serverless application, it may take a few seconds to warm up (The Upload PDF button is disable until the lambda is ready) and the first document upload may take a few seconds to complete (as the database needs to be warmed up).

## Setup

1. Clone the repository
2. Install the dependencies
3. Run the script

# Notes

- After the postgres rds db is created, you need to run the following command to create the vector store:

- Requires psql cli to be installed.