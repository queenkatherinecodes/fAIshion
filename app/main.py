import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import db_utils
from utils import user_utils
from utils import clothing_utils
from typing import Optional

# Initialize FastAPI app
app = FastAPI(title="fAIshion API", description="Fashion API with Database Setup")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    print("Application starting...")
    db_utils.init_db()
    print("Database initialization completed.")

# Basic routes
@app.get("/")
async def hello_world():
    return {"message": "Hello World from fAIshion API!"}

@app.get("/health")
async def health():
    db_status = db_utils.check_db_connection()
    
    return {
        "status": "healthy",
        "database_status": db_status["status"],
        "error": db_status.get("error_message", None)
    }

# Add tables endpoint to check if tables are created
@app.get("/tables")
async def list_tables():
    return db_utils.get_tables()

# Add debug endpoint to manually initialize database
@app.post("/init-db")
async def manual_init_db():
    try:
        db_utils.init_db()
        return {"message": "Database initialization triggered manually"}
    except Exception as e:
        return {"error": str(e)}

# Define Pydantic model for user data
class User(BaseModel):
    username: str
    password: str

# User endpoints
@app.post("/register", status_code=201)
async def register(user: User):
    return user_utils.register_user(user.username, user.password)

@app.post("/login")
async def login(user: User):
    return user_utils.verify_user(user.username, user.password)

# Define Pydantic model for clothing items
class ClothingItem(BaseModel):
    userId: str
    description: str
    type: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    style: Optional[str] = None
    length: Optional[str] = None

# Clothing endpoints
@app.post("/api/clothing")
async def add_clothing(item: ClothingItem):
    return clothing_utils.add_clothing_item(
        user_id=item.userId,
        description=item.description,
        clothing_type=item.type,
        color=item.color,
        season=item.season,
        occasion=item.occasion,
        style=item.style,
        length=item.length
    )

@app.get("/api/clothing/{user_id}")
async def get_user_clothing(user_id: str):
    # This is a placeholder - you'll need to implement this function
    # in clothing_utils.py later
    return {"message": "This endpoint is not implemented yet"}