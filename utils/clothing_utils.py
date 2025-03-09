# utils/clothing_utils.py
import uuid
import logging  # added import for logging
from fastapi import HTTPException
from utils import db_utils

logger = logging.getLogger(__name__)  # initialize logger

def add_clothing_item(user_id: str, description: str, clothing_type: str = None, **kwargs):
    """
    Add a clothing item to the appropriate table
    """
    conn = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM Users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    # Determine clothing type if not provided
    if not clothing_type:
        clothing_type = "Tops"  # Default to Tops if not specified
    
    # Generate a unique ID for the item
    item_id = str(uuid.uuid4())
    
    # Extract optional parameters
    color = kwargs.get('color')
    season = kwargs.get('season')
    occasion = kwargs.get('occasion')
    style = kwargs.get('style')
    length = kwargs.get('length')
    
    # Insert into appropriate table based on clothing type
    try:
        if clothing_type.lower() in ["top", "shirt", "blouse", "sweater"]:
            cursor.execute(
                "INSERT INTO Tops (id, userId, description, color, season, occasion) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, user_id, description, color, season, occasion)
            )
            clothing_type = "Tops"
        elif clothing_type.lower() in ["bottom", "pants", "jeans", "shorts", "skirt"]:
            cursor.execute(
                "INSERT INTO Bottoms (id, userId, description, color, season, occasion) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, user_id, description, color, season, occasion)
            )
            clothing_type = "Bottoms"
        elif clothing_type.lower() in ["dress", "gown"]:
            cursor.execute(
                "INSERT INTO Dresses (id, userId, description, color, season, occasion, length) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item_id, user_id, description, color, season, occasion, length)
            )
            clothing_type = "Dresses"
        elif clothing_type.lower() in ["shoes", "sneakers", "boots", "sandals"]:
            cursor.execute(
                "INSERT INTO Shoes (id, userId, description, color, type, occasion) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, user_id, description, color, style, occasion)
            )
            clothing_type = "Shoes"
        else:
            cursor.execute(
                "INSERT INTO Accessories (id, userId, description, type, color, occasion) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, user_id, description, clothing_type, color, occasion)
            )
            clothing_type = "Accessories"
        
        conn.commit()
        logger.info(f"Clothing item added: {item_id} to {clothing_type}")  # added logging
        conn.close()
        
        return {
            "id": item_id,
            "type": clothing_type,
            "message": f"Added {clothing_type} item successfully"
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding clothing item for user {user_id}: {str(e)}")  # added logging
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

def get_all_clothing_descriptions():
    """
    Retrieve all clothing item descriptions from all clothing tables.
    """
    conn = db_utils.get_db_connection()
    cursor = conn.cursor()
    descriptions = []
    tables = ["Clothing"]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT description FROM {table}")
            results = cursor.fetchall()
            descriptions.extend([row[0] for row in results if row and row[0]])
        except Exception as e:
            # Log the error or pass if a particular table is missing
            print(f"Error fetching from {table}: {str(e)}")
            continue
    
    conn.close()
    return descriptions