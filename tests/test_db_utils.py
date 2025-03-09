import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import (
    get_db_connection,
    create_users_table,
    create_clothing_table,
    init_db,
    get_tables,
    check_db_connection
)

TEST_DB_PATH = "test_faishion.db"


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Arrange
    old_db_path = os.environ.get("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = TEST_DB_PATH
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    if old_db_path:
        os.environ["SQLITE_DB_PATH"] = old_db_path
    else:
        os.environ.pop("SQLITE_DB_PATH", None)


def test_get_db_connection():
    # Act
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys")
    foreign_keys_status = cursor.fetchone()[0]
    
    # Assert
    assert conn is not None
    assert foreign_keys_status == 1
    assert conn.row_factory == sqlite3.Row
    
    conn.close()


def test_get_db_connection_error():
    # Arrange
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = Exception("Test connection error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            get_db_connection()
        assert excinfo.value.status_code == 500
        assert "Database connection error" in excinfo.value.detail


def test_create_users_table():
    # Act
    create_users_table()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
    table_exists = cursor.fetchone()
    
    cursor.execute("PRAGMA table_info(Users)")
    columns = {row['name']: row['type'] for row in cursor.fetchall()}
    
    # Assert
    assert table_exists is not None
    assert 'id' in columns
    assert 'username' in columns
    assert 'password' in columns
    
    conn.close()


def test_create_clothing_table():
    # Arrange
    create_users_table()
    
    # Act
    create_clothing_table()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Clothing'")
    table_exists = cursor.fetchone()
    
    cursor.execute("PRAGMA table_info(Clothing)")
    columns = {row['name']: row['type'] for row in cursor.fetchall()}
    
    cursor.execute("PRAGMA foreign_key_list(Clothing)")
    fk_info = cursor.fetchone()
    
    # Assert
    assert table_exists is not None
    assert 'id' in columns
    assert 'userId' in columns
    assert 'description' in columns
    assert 'image' in columns
    assert fk_info is not None
    assert fk_info['table'] == 'Users'
    assert fk_info['from'] == 'userId'
    assert fk_info['to'] == 'id'
    
    conn.close()


def test_init_db():
    # Act
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Users', 'Clothing')")
    tables = cursor.fetchall()
    
    # Assert
    assert len(tables) == 2
    
    conn.close()


def test_get_tables():
    # Arrange
    init_db()
    
    # Act
    tables_info = get_tables()
    
    # Assert
    assert 'tables' in tables_info
    assert 'Users' in tables_info['tables']
    assert 'Clothing' in tables_info['tables']


def test_get_tables_error():
    # Arrange
    with patch('utils.db_utils.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Test error")
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        
        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            get_tables()
        assert excinfo.value.status_code == 500
        assert "Error getting tables" in excinfo.value.detail


def test_check_db_connection_success():
    # Arrange
    conn = get_db_connection()
    conn.close()
    
    # Act
    result = check_db_connection()
    
    # Assert
    assert result['status'] == 'connected'