import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pyodbc

# Initialize FastAPI app
app = FastAPI(title="fAIshion API", description="Minimal Hello World")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get database connection string from environment
DATABASE_SERVER = os.getenv("SQL_SERVER", "faishion-dev-sql.database.windows.net")
DATABASE_NAME = os.getenv("SQL_DATABASE", "faishionDb")
DATABASE_USER = os.getenv("SQL_USER", "faishionadmin")
DATABASE_PASSWORD = os.getenv("SQL_PASSWORD", "Fai$hion2025Complex!Pwd")

# Basic routes
@app.get("/")
async def hello_world():
    return {"message": "Hello World from fAIshion API!"}

@app.get("/health")
async def health():
    db_status = "unknown"
    error_message = None
    
    try:
        # Try connecting to the database
        connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DATABASE_SERVER};DATABASE={DATABASE_NAME};UID={DATABASE_USER};PWD={DATABASE_PASSWORD}"
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        db_status = "connected" if result and result[0] == 1 else "error"
    except Exception as e:
        db_status = "error"
        error_message = str(e)
    
    return {
        "status": "healthy",
        "database_status": db_status,
        "error": error_message
    }