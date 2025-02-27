from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.models import Base  # Imports Base and models from __init__.py

# Create all tables (for development/demo purposes).
# In production, use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# Add CORS middleware (allow all origins for simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
