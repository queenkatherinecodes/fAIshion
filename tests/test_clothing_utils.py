import os
import uuid
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.clothing_utils import add_clothing_item, get_all_clothing_descriptions
from utils.db_utils import get_db_connection, create_users_table, create_clothing_table

def get_test_db_path():
    return f"test_faishion_{uuid.uuid4()}.db"

def get_unique_username():
    return f"testuser_{uuid.uuid4().hex[:8]}"

@pytest.fixture(scope="function")
def test_db():
    test_db_path = get_test_db_path()
    test_username = get_unique_username()
    test_user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    
    old_db_path = os.environ.get("SQLITE_DB_PATH")
    
    os.environ["SQLITE_DB_PATH"] = test_db_path
    
    create_users_table()
    create_clothing_table()
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Users (id, username, password) VALUES (?, ?, ?)",
            (test_user_id, test_username, "password123")
        )
        conn.commit()
    except Exception as e:
        print(f"Setup error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
    
    yield {"db_path": test_db_path, "user_id": test_user_id, "username": test_username}
    
    try:
        time.sleep(0.1)
        
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except PermissionError:
                print(f"Could not remove {test_db_path} - file may be locked")
    finally:
        if old_db_path:
            os.environ["SQLITE_DB_PATH"] = old_db_path
        else:
            os.environ.pop("SQLITE_DB_PATH", None)


def test_add_clothing_item_success(test_db):
    # Arrange
    user_id = test_db["user_id"]
    description = "Blue jeans"
    
    # Act
    result = add_clothing_item(user_id, description)
    
    # Assert
    assert "message" in result
    assert "Added item successfully" in result["message"]
    assert "id" in result
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM Clothing WHERE userId = ?", (user_id,))
        db_result = cursor.fetchone()
        assert db_result is not None
        assert db_result[0] == "Blue jeans"
    finally:
        if conn:
            conn.close()


def test_add_clothing_item_nonexistent_user(test_db):
    # Arrange
    nonexistent_user_id = f"nonexistent-user-{uuid.uuid4().hex[:8]}"
    description = "Red shirt"
    
    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        add_clothing_item(nonexistent_user_id, description)
    
    assert excinfo.value.status_code == 500
    assert "User not found" in excinfo.value.detail


def test_add_clothing_item_database_error(test_db):
    # Arrange
    user_id = test_db["user_id"]
    description = "Green sweater"
    
    with patch('utils.db_utils.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": user_id}
        mock_cursor.execute.side_effect = [None, Exception("Test database error")]
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        
        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            add_clothing_item(user_id, description)
        
        assert excinfo.value.status_code == 500
        assert "Database error" in excinfo.value.detail
        
        mock_connection.rollback.assert_called_once()
        mock_connection.close.assert_called_once()


def test_get_all_clothing_descriptions_success(test_db):
    # Arrange
    user_id = test_db["user_id"]
    descriptions = ["Blue jeans", "Red shirt", "Green sweater"]
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for desc in descriptions:
            cursor.execute(
                "INSERT INTO Clothing (id, userId, description) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), user_id, desc)
            )
        conn.commit()
    finally:
        if conn:
            conn.close()
    
    # Act
    result = get_all_clothing_descriptions(user_id)
    
    # Assert
    assert len(result) == 3
    for desc in descriptions:
        assert desc in result


def test_get_all_clothing_descriptions_no_items(test_db):
    # Arrange
    user_id = test_db["user_id"]
    
    # Act
    result = get_all_clothing_descriptions(user_id)
    
    # Assert
    assert result == []


def test_get_all_clothing_descriptions_database_error(test_db):
    # Arrange
    user_id = test_db["user_id"]
    
    with patch('utils.db_utils.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Test database error")
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        
        # Act
        result = get_all_clothing_descriptions(user_id)
        
        # Assert
        assert result == []
        mock_connection.close.assert_called_once()