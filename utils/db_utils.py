# utils/db_utils.py
import os
import sqlite3
from fastapi import HTTPException

# Set the database file path
DATABASE_PATH = os.getenv("SQLITE_DB_PATH", "faishion.db")

def get_db_connection():
    """
    Creates and returns a database connection to SQLite
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # Enable foreign keys support
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

def create_users_table():
    """
    Creates the Users table if it doesn't exist
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Creating Users table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """)
        conn.commit()
        print("Users table creation successful")
    except Exception as e:
        print(f"Error creating Users table: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def create_clothing_tables():
    """
    Creates the clothing item tables if they don't exist
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = [
        # Tops table
        """
        CREATE TABLE IF NOT EXISTS Tops (
            id TEXT PRIMARY KEY,
            userId TEXT NOT NULL,
            description TEXT,
            color TEXT,
            season TEXT,
            occasion TEXT,
            imageUrl TEXT,
            FOREIGN KEY (userId) REFERENCES Users(id)
        )
        """,
        
        # Bottoms table
        """
        CREATE TABLE IF NOT EXISTS Bottoms (
            id TEXT PRIMARY KEY,
            userId TEXT NOT NULL,
            description TEXT,
            color TEXT,
            season TEXT,
            occasion TEXT,
            imageUrl TEXT,
            FOREIGN KEY (userId) REFERENCES Users(id)
        )
        """,
        
        # Dresses table
        """
        CREATE TABLE IF NOT EXISTS Dresses (
            id TEXT PRIMARY KEY,
            userId TEXT NOT NULL,
            description TEXT,
            color TEXT,
            season TEXT,
            occasion TEXT,
            length TEXT,
            imageUrl TEXT,
            FOREIGN KEY (userId) REFERENCES Users(id)
        )
        """,
        
        # Shoes table
        """
        CREATE TABLE IF NOT EXISTS Shoes (
            id TEXT PRIMARY KEY,
            userId TEXT NOT NULL,
            description TEXT,
            color TEXT,
            type TEXT,
            occasion TEXT,
            imageUrl TEXT,
            FOREIGN KEY (userId) REFERENCES Users(id)
        )
        """,
        
        # Accessories table
        """
        CREATE TABLE IF NOT EXISTS Accessories (
            id TEXT PRIMARY KEY,
            userId TEXT NOT NULL,
            description TEXT,
            type TEXT,
            color TEXT,
            occasion TEXT,
            imageUrl TEXT,
            FOREIGN KEY (userId) REFERENCES Users(id)
        )
        """
    ]
    
    for i, table_query in enumerate(tables):
        try:
            print(f"Creating table {i+1}/{len(tables)}...")
            cursor.execute(table_query)
            conn.commit()
            print(f"Table {i+1} created successfully")
        except Exception as e:
            print(f"Error creating table {i+1}: {str(e)}")
            conn.rollback()
    
    conn.close()

def init_db():
    """
    Initialize all database tables with better error handling
    """
    print("Starting database initialization...")
    try:
        # First check connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        print("Database connection successful")
        
        # Create tables
        create_users_table()
        create_clothing_tables()
        
        print("Database initialization completed")
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")

def get_tables():
    """
    Get a list of all tables in the database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"tables": tables}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Error getting tables: {str(e)}")

def check_db_connection():
    """
    Check if database connection is working
    """
    print("Checking database connection...")
    try:
        # First check if the database file exists
        if os.path.exists(DATABASE_PATH):
            print(f"Database file exists at {DATABASE_PATH}")
        else:
            print(f"Database file does not exist at {DATABASE_PATH}")
            return {"status": "error", "error_message": f"Database file not found at {DATABASE_PATH}"}
        
        # Try to open a connection
        print("Attempting to connect to database...")
        conn = get_db_connection()
        print("Connection established, executing test query...")
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        print(f"Query result: {result}")
        return {"status": "connected" if result and result[0] == 1 else "error"}
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return {"status": "error", "error_message": str(e)}