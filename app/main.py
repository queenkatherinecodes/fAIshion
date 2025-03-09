# app/main.py
import os
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from utils import db_utils
from utils import user_utils
from utils import clothing_utils
from app import services
from app.models import User, OutfitRequest, ClothingDescription, OutfitWithAvatarRequest
import logging
import base64
import time

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="fAIshion API", description="Fashion API with SQLite Database")

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting...")  # replaced print
    db_utils.init_db()
    logger.info("Database initialization completed.")  # replaced print

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Routes
@app.get("/")
async def hello_world():
    return {"message": "Hello World from fAIshion API!"}

@app.get("/health")
async def health():
    try:
        print("Health check requested")
        db_status = db_utils.check_db_connection()
        print(f"DB status: {db_status}")
        
        return {
            "status": "healthy",
            "database_status": db_status["status"],
            "error": db_status.get("error_message", None)
        }
    except Exception as e:
        print(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}"
        }

# Health check for DB tables
@app.get("/tables")
async def list_tables():
    return db_utils.get_tables()

# User endpoints
@app.post("/register", status_code=201)
async def register(user: User):
    return user_utils.register_user(user.username, user.password)

@app.post("/login")
async def login(user: User):
    return user_utils.verify_user(user.username, user.password)


# Endpoint for uploading clothing by description
@app.post("/upload-clothing/description")
async def upload_clothing(clothingItem: ClothingDescription):
    try:
        result = clothing_utils.add_clothing_item(
            user_id=clothingItem.userId,
            description=clothingItem.description
        )
    except Exception as e:
        return {"error": "Failed to save clothing item", "details": str(e)}

    return {"message": "Clothing item uploaded successfully", "result": result}

# Endpoint for uploading clothing by image
@app.post("/upload-clothing/image")
async def upload_clothing_image(
    userId: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Generate a description for the clothing item using the image file
        img_url = services.convert_img(file.file)
        clothing_description = services.caption_image(img_url)
    except Exception as e:
        return {"error": "Failed to generate description from image", "details": str(e)}

    try:
        result = clothing_utils.add_clothing_item(
            user_id=userId,
            description=clothing_description,
            file=file
        )
    except Exception as e:
        return {"error": "Failed to save clothing item", "details": str(e)}
    
    return {"message": "Clothing item uploaded successfully", "result": result, "description": clothing_description}


# Endpoint for suggesting an outfit
@app.get("/suggest-outfit")
async def suggest_outfit(
    outfitRequest: OutfitRequest
):
    """
    Generate an outfit suggestion based on:
    - All clothing items stored in the database
    - The provided occasion, age, style preferences, and current weather
    """
    try:
        clothing_items = clothing_utils.get_all_clothing_descriptions(outfitRequest.userId)
    except Exception as e:
        return {"error": "Failed to fetch clothing items", "details": str(e)}

    if not clothing_items:
        return {"error": "No clothing items found. Upload clothing items first."}

    # Combine all clothing descriptions into one text block
    all_descriptions = "\n".join(f"- {desc}" for desc in clothing_items)

    try:
        weather = services.fetch_weather(outfitRequest.location)
    except Exception as e:
        return {"error": "Failed to fetch weather", "details": str(e)}

    try:
        outfit = services.get_outfit_suggestion(all_descriptions, outfitRequest.occasion, outfitRequest.age, outfitRequest.style_preferences, outfitRequest.location, weather)
    except Exception as e:
        return {"error": "Failed to get outfit suggestion", "details": str(e)}

    return {
        "weather": weather,
        "clothing_items": clothing_items,
        "outfit_suggestion": outfit
    }

@app.get("/suggest-outfit-with-avatar")
async def suggest_outfit_with_avatar(
    outfitRequest: OutfitWithAvatarRequest
):
    """
    Generate an outfit suggestion with a matching avatar based on:
    - All clothing items stored in the database
    - The provided occasion, age, style preferences, and current weather
    - Optional gender preference for the avatar
    
    The avatar will use the user's photo if available (from uploads/{userId}.jpg)
    or fall back to a mannequin if no photo is available.
    
    The avatar image will be saved to output_avatars/{userId}_{timestamp}.png
    """
    
    try:
        clothing_items = clothing_utils.get_all_clothing_descriptions(outfitRequest.userId)
    except Exception as e:
        return {"error": "Failed to fetch clothing items", "details": str(e)}

    if not clothing_items:
        return {"error": "No clothing items found. Upload clothing items first."}

    # Combine all clothing descriptions into one text block
    all_descriptions = "\n".join(f"- {desc}" for desc in clothing_items)

    try:
        weather = services.fetch_weather(outfitRequest.location)
    except Exception as e:
        return {"error": "Failed to fetch weather", "details": str(e)}

    try:
        # Use the get_outfit_with_avatar function that returns both outfit and avatar
        result = services.get_outfit_with_avatar(
            all_descriptions, 
            outfitRequest.occasion, 
            outfitRequest.age, 
            outfitRequest.style_preferences, 
            outfitRequest.location, 
            weather,
            outfitRequest.userId,  # Pass userId for potential photo lookup
            outfitRequest.gender    # Pass gender preference for avatar
        )
    except Exception as e:
        return {"error": "Failed to get outfit with avatar", "details": str(e)}
    
    # Save the avatar image to a file if it exists and is in base64 format
    avatar_image_path = None
    if "avatar_image" in result and isinstance(result["avatar_image"], str) and result["avatar_image"].startswith("data:image"):
        try:
            # Extract the base64 data (remove the data:image/png;base64, prefix)
            image_data = result["avatar_image"].split(",")[1]
            
            # Create output directory if it doesn't exist
            os.makedirs("output_avatars", exist_ok=True)
            
            # Create a filename with timestamp to avoid overwriting
            timestamp = int(time.time())
            filename = f"{outfitRequest.userId}_{timestamp}.png"
            image_path = os.path.join("output_avatars", filename)
            
            # Save to file
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            logger.info(f"Avatar image saved to {image_path}")
            avatar_image_path = image_path
            
        except Exception as e:
            logger.error(f"Error saving avatar image: {str(e)}")
            # Don't fail the whole request if just the file saving fails
            avatar_image_path = f"Error saving image: {str(e)}"

    return {
        "weather": weather,
        "clothing_items": clothing_items,
        "outfit_suggestion": result["outfit_suggestion"],
        "avatar_image_path": avatar_image_path
    }