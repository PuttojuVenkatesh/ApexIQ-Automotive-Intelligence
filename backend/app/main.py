from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import documents, chat, compare, vehicles
from app.db.supabase_client import db

app = FastAPI(
    title=settings.APP_NAME,
    description="Automotive AI Assistant: Document Ingestion, Supabase pgvector RAG, and Car Comparison Engine",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(vehicles.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "storage_backend": "supabase" if db.is_connected else "local_fallback",
        "docs_url": "/docs",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_dimension": settings.EMBEDDING_DIMENSION
    }

if __name__ == "__main__":
    import uvicorn
    # Bind to 127.0.0.1 (localhost) to ensure the API is never exposed to the external network
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
