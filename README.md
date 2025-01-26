# PDF Chat Hub

[https://www.pdfchathub.com/](https://www.pdfchathub.com/)

A simple chatbot application that enables intelligent conversations with PDF documents through RAG (Retrieval Augmented Generation) techniques. The system supports multiple document management, separate conversation threads, and is optimized for production use through serverless architecture.

## Features

- 🚀 Multi-document chat support with separate conversation threads
- 📊 Research-backed RAG pipeline with tuned retrieval parameters
- ⚡ Serverless architecture optimized for cost and scalability
- 🔄 Warm-up endpoint to mitigate cold starts
- 📈 Evaluation metrics for retrieval quality

## Architecture Highlights

### Why Serverless?

- Cost-effective for personal projects with pay-per-use model
- Automatic scaling based on demand
- Zero maintenance overhead
- Built-in high availability

### Cold Start Mitigation

Implemented a `/warm-up` endpoint for faster response times that is called when the user first loads the page to warm up the database. 


## Development Setup

### Prerequisites

1. Clone the repository
    ```bash
    git clone https://github.com/yourusername/pdf-chat-hub.git
    cd pdf-chat-hub
    ```

2. Install dependencies
    ```bash
    just init
    ```

3. Set OpenAI API key in `backend/.env`, copy `backend/.env_template` to `.env` and add your key

### Running Locally

```bash
just serve-local
```

Then navigate to [http://localhost:5173](http://localhost:5173) to use the application.

## Research & RAG Pipeline

The project includes a comprehensive research component for tuning and evaluating the RAG pipeline:

### Evaluation Metrics
- Retrieval precision and recall
- Mean Reciprocal Rank (MRR)
- Generation quality assessment

### Tuning Parameters
- Chunk size optimization
- Embedding model selection
- Retrieval strategy comparison

See the `/research` directory for notebooks and evaluation scripts.

## Deployment

### Infrastructure Setup

1. Add AWS credentials to `infrastructure/.env_template` and rename to `.env`

2. Initialize Terraform

    ```bash
    cd infrastructure
    terraform init
    ```

3. Apply infrastructure

    ```bash
    just apply
    ```

4. Deploy the application

    Option A: Deploy from local

        just build-and-sync-frontend
        just lambda-deploy

    Option B: Deploy using the CI/CD pipeline in GitHub Actions


## Notes

- The first document upload may take a few seconds as the database warms up
- The Upload PDF button is disabled until the lambda is ready
