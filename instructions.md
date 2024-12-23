# Project Overview

This project is a chatbot website that allows users to chat with a PDF file. They should be able to  multiple PDFs, maintaining a separate chat for each, and be able to upload new PDFs or switch between them. 

# Core Functionality 

- [ ] Users should be able to upload a PDF file and chat with it.
- [ ] Users should be able to upload multiple PDFs and chat with them separately.
- [ ] Users should be able to switch between PDFs and continue their conversations.
- [ ] Users should be able to upload new PDFs or switch between them.

# Current File Structure 
 README.md
├── TODO.md
├── backend
│   ├── Dockerfile
│   ├── app.py
│   ├── brain
│   ├── debug.py
│   ├── dependencies
│   ├── docs
│   ├── justfile
│   ├── lambda_handler.py
│   ├── models
│   ├── poetry.lock
│   ├── pyproject.toml
│   ├── repositories
│   ├── routers
│   ├── services
│   └── tests
├── infrastructure
│   ├── cloudfront.tf
│   ├── ecr.tf
│   ├── iam.tf
│   ├── lambda.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── s3.tf
│   ├── secrets.tf
│   ├── terraform.tfstate
│   ├── terraform.tfstate.1734037391.backup
│   └── terraform.tfstate.backup
├── instructions.md
├── justfile
├── test_payloads
│   ├── query-request.json
│   └── root-request.json
└── web_app
    ├── dist
    ├── index.html
    ├── jsconfig.json
    ├── justfile
    ├── node_modules
    ├── package-lock.json
    ├── package.json
    ├── public
    ├── vite.config.js
    └── src
        ├── App.vue
        ├── assets
        │   ├── base.css
        │   ├── logo.svg
        │   └── main.css
        ├── components
        │   └── icons
        ├── main.js
        ├── router
        │   └── index.js
        ├── services
        │   └── api.js
        └── views
    