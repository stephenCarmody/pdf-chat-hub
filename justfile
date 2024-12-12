serve-frontend:
    cd web_app && npm run dev

serve-backend:
    cd backend && uvicorn routers.router:app --reload

get-frontend-url:
    cd infrastructure && terraform output cloudfront_domain

