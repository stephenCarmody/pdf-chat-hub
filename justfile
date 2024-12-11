serve-frontend:
    cd web_app && npm run dev

serve-backend:
    cd backend && uvicorn routers.router:app --reload
