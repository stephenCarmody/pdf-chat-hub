ECR_URL := "031421732210.dkr.ecr.eu-west-1.amazonaws.com"

VERSION := `git rev-parse --short HEAD`

clean:
    # remove all pycache
    find . -type d -name "__pycache__" -exec rm -rf {} +

serve-frontend-local:
    cd web_app && npm run dev

serve-backend-local:
    cd backend && uvicorn app:app --reload --log-level debug

build-and-sync-frontend:
    cd web_app && just build
    cd web_app && just sync-s3

get-frontend-url:
    cd infrastructure && terraform output cloudfront_domain

lambda-build:
    cd backend && docker build --platform linux/x86_64 -t {{ECR_URL}}/pdf-chat-api:{{VERSION}} .

lambda-push: lambda-build
    aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin {{ECR_URL}}
    docker push {{ECR_URL}}/pdf-chat-api:{{VERSION}}

lambda-deploy:
    cd infrastructure && terraform apply \
        -replace="aws_lambda_function.api" \
        -target="aws_lambda_function.api" \
        -target="aws_lambda_permission.api_gateway" \
        -target="aws_lambda_permission.api_gateway_root"

lambda-run-local:
    cd backend && docker build --platform linux/amd64 --build-arg PLATFORM=linux/arm64 -t pdf-chat-api . 
    cd backend && docker run -p 9000:8080 \
        -e OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2 | tr -d ' "') \
        -e OPENAI_SECRET_NAME="pdf-chat/openai-api-key" \
        -e SESSION_STATE_BUCKET="pdf-chat-lambda-state" \
        -e AWS_REGION="eu-west-1" \
        -e AWS_DEFAULT_REGION="eu-west-1" \
        -e AWS_ACCESS_KEY_ID="$(aws configure get aws_access_key_id)" \
        -e AWS_SECRET_ACCESS_KEY="$(aws configure get aws_secret_access_key)" \
        -e AWS_SESSION_TOKEN="$(aws configure get aws_session_token)" \
        pdf-chat-api

lambda-endpoint:
    cd infrastructure && terraform output api_gateway_url

lambda-logs:
    aws logs tail /aws/lambda/pdf-chat-api --follow

# SECRETS

secrets-put:
    #!/usr/bin/env bash
    API_KEY=$(grep OPENAI_API_KEY backend/.env | cut -d '=' -f2 | tr -d ' "')
    aws secretsmanager put-secret-value \
        --secret-id pdf-chat/openai-api-key \
        --secret-string "{\"OPENAI_API_KEY\":\"$API_KEY\"}" \
        --region eu-west-1

# TESTING

test-local-root:
    curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test_payloads/root-request.json | jq

test-local-query:
    curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test_payloads/query-request.json | jq

test-lambda-root:
    curl https://li6a6mcfp4.execute-api.eu-west-1.amazonaws.com/prod/

test-lambda-query:
    curl -X POST https://li6a6mcfp4.execute-api.eu-west-1.amazonaws.com/prod/query \
        -H "Content-Type: application/json" \
        -d '{"query":"What is this document about?", "session_id": "test-session"}'

test-lambda-upload:
    #!/usr/bin/env bash
    API_URL=$(just lambda-endpoint | tr -d '"\n') && \
    curl -X POST "${API_URL}/prod/upload" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@backend/docs/Bitcoin - A Peer-to-Peer Electronic Cash System.pdf" \
        -F "session_id=test-session"

lambda-deploy-ci: lambda-test lambda-push
    cd infrastructure && terraform init
    cd infrastructure && terraform apply -auto-approve \
        -var="lambda_image_tag={{VERSION}}" \
        -target="aws_lambda_function.api" \
        -target="aws_lambda_permission.api_gateway" \
        -target="aws_lambda_permission.api_gateway_root"