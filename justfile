serve-frontend-local:
    cd web_app && npm run dev

serve-backend-local:
    cd backend && uvicorn routers.router:app --reload


build-and-sync-frontend:
    cd web_app && just build
    cd web_app && just sync-s3

get-frontend-url:
    cd infrastructure && terraform output cloudfront_domain

