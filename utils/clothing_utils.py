# utils/clothing_utils.py
import uuid
import logging  # added import for logging
from fastapi import HTTPException
from utils import db_utils

logger = logging.getLogger(__name__)  # initialize logger

def add_clothing_item(user_id: str, description: str):
    """
    Add a clothing item to the appropriate table
    """
    conn = None
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM Users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate a unique ID for the item
        item_id = str(uuid.uuid4())
        
        cursor.execute(
            "INSERT INTO Clothing (id, userId, description) VALUES (?, ?, ?)",
            (item_id, user_id, description)
        )

        conn.commit()
        logger.info(f"Clothing item added: {item_id}")
        
        return {
            "id": item_id,
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