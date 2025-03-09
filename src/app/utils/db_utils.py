import os
import pyodbc
from fastapi import HTTPException

# Get database connection string from environment
DATABASE_SERVER = os.getenv("SQL_SERVER", "faishion-dev-sql.database.windows.net")
DATABASE_NAME = os.getenv("SQL_DATABASE", "faishionDb")
DATABASE_USER = os.getenv("SQL_USER", "faishionadmin")
DATABASE_PASSWORD = os.getenv("SQL_PASSWORD", "Fai$hion2025Complex!Pwd")

def get_db_connection():
    """
    Creates and returns a database connection
    """
    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DATABASE_SERVER};DATABASE={DATABASE_NAME};UID={DATABASE_USER};PWD={DATABASE_PASSWORD}"
    try:
        conn = pyodbc.connect(connection_string)
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
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users')
        BEGIN
            CREATE TABLE Users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(100) NOT NULL
            )
            PRINT 'Users table created'
        END
        ELSE
        BEGIN
            PRINT 'Users table already exists'
        END
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
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tops')
        BEGIN
            CREATE TABLE Tops (
                id VARCHAR(36) PRIMARY KEY,
                userId VARCHAR(36) NOT NULL,
                description VARCHAR(500),
                color VARCHAR(50),
                season VARCHAR(20),
                occasion VARCHAR(50),
                imageUrl VARCHAR(255),
                FOREIGN KEY (userId) REFERENCES Users(id)
            )
            PRINT 'Tops table created'
        END
        ELSE
        BEGIN
            PRINT 'Tops table already exists'
        END
        """,
        
        # Bottoms table
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Bottoms')
        BEGIN
            CREATE TABLE Bottoms (
                id VARCHAR(36) PRIMARY KEY,
                userId VARCHAR(36) NOT NULL,
                description VARCHAR(500),
                color VARCHAR(50),
                season VARCHAR(20),
                occasion VARCHAR(50),
                imageUrl VARCHAR(255),
                FOREIGN KEY (userId) REFERENCES Users(id)
            )
            PRINT 'Bottoms table created'
        END
        ELSE
        BEGIN
            PRINT 'Bottoms table already exists'
        END
        """,
        
        # Dresses table
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Dresses')
        BEGIN
            CREATE TABLE Dresses (
                id VARCHAR(36) PRIMARY KEY,
                userId VARCHAR(36) NOT NULL,
                description VARCHAR(500),
                color VARCHAR(50),
                season VARCHAR(20),
                occasion VARCHAR(50),
                length VARCHAR(20),
                imageUrl VARCHAR(255),
                FOREIGN KEY (userId) REFERENCES Users(id)
            )
            PRINT 'Dresses table created'
        END
        ELSE
        BEGIN
            PRINT 'Dresses table already exists'
        END
        """,
        
        # Shoes table
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Shoes')
        BEGIN
            CREATE TABLE Shoes (
                id VARCHAR(36) PRIMARY KEY,
                userId VARCHAR(36) NOT NULL,
                description VARCHAR(500),
                color VARCHAR(50),
                type VARCHAR(50),
                occasion VARCHAR(50),
                imageUrl VARCHAR(255),
                FOREIGN KEY (userId) REFERENCES Users(id)
            )
            PRINT 'Shoes table created'
        END
        ELSE
        BEGIN
            PRINT 'Shoes table already exists'
        END
        """,
        
        # Accessories table
        """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Accessories')
        BEGIN
            CREATE TABLE Accessories (
                id VARCHAR(36) PRIMARY KEY,
                userId VARCHAR(36) NOT NULL,
                description VARCHAR(500),
                type VARCHAR(50),
                color VARCHAR(50),
                occasion VARCHAR(50),
                imageUrl VARCHAR(255),
                FOREIGN KEY (userId) REFERENCES Users(id)
            )
            PRINT 'Accessories table created'
        END
        ELSE
        BEGIN
            PRINT 'Accessories table already exists'
        END
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
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        return {"status": "connected" if result and result[0] == 1 else "error"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}