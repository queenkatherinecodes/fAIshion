#app/main.py
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
import uvicorn
from app.services import caption_image, get_outfit_suggestion, fetch_weather

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

@app.post("/upload-clothing")
async def upload_clothing(
    description: str = Form(None),
    file: UploadFile = File(None)
):
    """
    Upload a clothing item.
    - If an image file is provided, generate a description using the Hugging Face captioning pipeline.
    - Otherwise, use the provided text description.
    The description is then saved to the database.
    """
    if file:
        clothing_description = caption_image(file.file)
    else:
        if not description:
            return {"error": "Provide either an image file or a text description."}
        clothing_description = description

    try:
        """
        save_clothing_item(clothing_description)"
        """
    except Exception as e:
        return {"error": "Failed to save clothing item", "details": str(e)}

    return {"message": "Clothing item uploaded successfully", "description": clothing_description}

@app.post("/suggest-outfit")
async def suggest_outfit(
    occasion: str = Form(...),
    age: int = Form(None),
    style_preferences: str = Form(None),
    location: str = Form("New York")
):
    """
    Generate an outfit suggestion based on:
      - All clothing items stored in the database
      - The provided occasion, age, style preferences, and current weather
    """
    try:
        
        clothing_items = get_all_clothing_descriptions()
    except Exception as e:
        return {"error": "Failed to fetch clothing items", "details": str(e)}

    if not clothing_items:
        return {"error": "No clothing items found. Upload clothing items first."}

    # Combine all clothing descriptions into one text block
    all_descriptions = "\n".join(f"- {desc}" for desc in clothing_items)

    try:
        weather = fetch_weather(location)
    except Exception as e:
        return {"error": "Failed to fetch weather", "details": str(e)}

    try:
        outfit = get_outfit_suggestion(all_descriptions, occasion, age, style_preferences, location, weather)
    except Exception as e:
        return {"error": "Failed to get outfit suggestion", "details": str(e)}

    return {
        "weather": weather,
        "clothing_items": clothing_items,
        "outfit_suggestion": outfit
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)