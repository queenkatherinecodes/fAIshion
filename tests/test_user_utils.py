# tests/test_user_utils.py
import pytest
import hashlib
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import user_utils


def test_hash_password():
    # Arrange
    password = "test_password"
    expected_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Act
    result = user_utils.hash_password(password)
    
    # Assert
    assert result == expected_hash


@patch('utils.db_utils.get_db_connection')
def test_register_user_success(mock_get_connection):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    mock_cursor.fetchone.return_value = None
    username = "new_user"
    password = "secure_password"
    
    # Act
    with patch('uuid.uuid4', return_value='test-uuid'):
        result = user_utils.register_user(username, password)
    
    # Assert
    mock_cursor.execute.assert_any_call("SELECT * FROM Users WHERE username = ?", (username,))
    mock_cursor.execute.assert_any_call(
        "INSERT INTO Users (id, username, password) VALUES (?, ?, ?)",
        ('test-uuid', username, user_utils.hash_password(password))
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()
    assert result["username"] == username
    assert result["id"] == 'test-uuid'
    assert result["message"] == "User registered successfully"


@patch('utils.db_utils.get_db_connection')
def test_register_user_already_exists(mock_get_connection):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    mock_cursor.fetchone.return_value = {"id": "existing-id", "username": "existing_user"}
    username = "existing_user"
    password = "secure_password"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        user_utils.register_user(username, password)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Username already registered"
    mock_conn.close.assert_called_once()


@patch('utils.db_utils.get_db_connection')
def test_register_user_database_error(mock_get_connection):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    mock_cursor.fetchone.return_value = None
    db_error = Exception("Database connection failed")
    mock_cursor.execute.side_effect = [None, db_error]
    username = "new_user"
    password = "secure_password"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        user_utils.register_user(username, password)
    
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Database error: Database connection failed"
    mock_conn.close.assert_called_once()


@patch('utils.db_utils.get_db_connection')
def test_verify_user_success(mock_get_connection):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    mock_cursor.fetchone.return_value = ("user-123",)
    username = "existing_user"
    password = "correct_password"
    
    # Act
    result = user_utils.verify_user(username, password)
    
    # Assert
    hashed_password = user_utils.hash_password(password)
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM Users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    mock_conn.close.assert_called_once()
    assert result["status"] == "success"
    assert result["userId"] == "user-123"
    assert result["message"] == "Login successful"


@patch('utils.db_utils.get_db_connection')
def test_verify_user_invalid_credentials(mock_get_connection):
    # Arrange
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    mock_cursor.fetchone.return_value = None
    username = "existing_user"
    password = "wrong_password"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        user_utils.verify_user(username, password)
    
    hashed_password = user_utils.hash_password(password)
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM Users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    mock_conn.close.assert_called_once()
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid username or password"