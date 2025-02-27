from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to use in FastAPI endpoints for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
