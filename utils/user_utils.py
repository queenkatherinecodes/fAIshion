# utils/user_utils.py
import hashlib
import uuid
import logging  # added import for logging
from fastapi import HTTPException
from utils import db_utils

logger = logging.getLogger(__name__)  # initialize logger

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str):
    """
    Register a new user
    """
    conn = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    # Check if username already exists
    cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        logger.warning(f"Attempt to register already existing username: {username}")  # added logging
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Generate a unique ID for the user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(password)
    
    # Insert new user
    try:
        cursor.execute(
            "INSERT INTO Users (id, username, password) VALUES (?, ?, ?)",
            (user_id, username, hashed_password)
        )
        conn.commit()
        logger.info(f"User registered successfully: {username}")  # added logging
        conn.close()
        return {"id": user_id, "username": username, "message": "User registered successfully"}
    except Exception as e:
        conn.close()
        logger.error(f"Error registering user {username}: {str(e)}")  # added logging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def verify_user(username: str, password: str):
    """
    Verify user credentials
    """
    conn = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    # Check credentials
    cursor.execute(
        "SELECT id FROM Users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        logger.info(f"User verified successfully: {username}")  # added logging
        return {"status": "success", "userId": result[0], "message": "Login successful"}
    else:
        logger.warning(f"Failed login attempt for username: {username}")  # added logging
        raise HTTPException(status_code=401, detail="Invalid username or password")