# utils/clothing_utils.py
import os
import uuid
import logging  # added import for logging
from fastapi import HTTPException
from utils import db_utils

logger = logging.getLogger(__name__)  # initialize logger
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def add_clothing_item(user_id: str, description: str, file=None):
    """
    Add a clothing item to the appropriate table
    
    Args:
        user_id (str): The ID of the user
        description (str): Description of the clothing item
        file (UploadFile, optional): The uploaded image file
    """
    conn = None
    image_path = None
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM Users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate a unique ID for the item
        item_id = str(uuid.uuid4())
        
        # Handle the file if provided
        if file:
            # Make sure upload directory exists
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # Create the file path - using original extension or default to jpg
            file_extension = os.path.splitext(file.filename)[1] if hasattr(file, 'filename') else ".jpg"
            image_filename = f"{item_id}{file_extension}"
            image_path = os.path.join(UPLOAD_DIR, image_filename)
            
            # Save the file
            try:
                # For UploadFile objects from FastAPI
                if hasattr(file, 'file'):
                    contents = file.file.read()
                # For file-like objects
                else:
                    contents = file.read()
                    
                with open(image_path, "wb") as image_file:
                    image_file.write(contents)
                    
                logger.info(f"Image saved to {image_path}")
            except Exception as e:
                logger.error(f"Error saving image: {str(e)}")
                image_path = None
        
        # Insert into database with image path if available
        if image_path:
            cursor.execute(
                "INSERT INTO Clothing (id, userId, description, image) VALUES (?, ?, ?, ?)",
                (item_id, user_id, description, image_path)
            )
        else:
            cursor.execute(
                "INSERT INTO Clothing (id, userId, description) VALUES (?, ?, ?)",
                (item_id, user_id, description)
            )

        conn.commit()
        logger.info(f"Clothing item added: {item_id}")
        
        return {
            "id": item_id,
            "image": image_path,
            "message": "Added item successfully"
        }
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error adding clothing item for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_all_clothing_descriptions(userId: str):
    """
    Retrieve all clothing item descriptions from all clothing tables.
    """
    conn = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Using ? placeholder which is common in SQLite
        cursor.execute("SELECT description FROM Clothing WHERE userId = ?", (userId,))
        results = cursor.fetchall()
        descriptions = [row[0] for row in results if row and row[0]]
    except Exception as e:
        # Log the error
        print(f"Error fetching clothing descriptions: {str(e)}")
        descriptions = []
    finally:
        conn.close()
    
    return descriptions