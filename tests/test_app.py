# tests/test_app.py
import pytest
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    json_resp = response.json()
    assert "Hello World" in json_resp.get("message", "")


def test_health(monkeypatch):
    # Override the check_db_connection method to simulate a healthy DB
    from utils import db_utils
    monkeypatch.setattr(db_utils, "check_db_connection", lambda: {"status": "connected"})
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "connected"


def test_tables(monkeypatch):
    # Override get_tables to simulate table listing
    from utils import db_utils
    fake_tables = {"tables": ["Users", "Tops", "Bottoms", "Dresses", "Shoes", "Accessories"]}
    monkeypatch.setattr(db_utils, "get_tables", lambda: fake_tables)
    
    response = client.get("/tables")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "Users" in data["tables"]


def test_init_db(monkeypatch):
    # Override init_db to simulate successful initialization
    from utils import db_utils
    monkeypatch.setattr(db_utils, "init_db", lambda: None)
    
    response = client.post("/init-db")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Database initialization triggered" in data["message"]


def test_register(monkeypatch):
    # Fake user registration
    from utils import user_utils

    def fake_register(username, password):
        return {"id": "fake-id", "username": username, "message": "User registered successfully"}

    monkeypatch.setattr(user_utils, "register_user", fake_register)
    
    payload = {"username": "testuser", "password": "testpass"}
    response = client.post("/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["message"] == "User registered successfully"


def test_login(monkeypatch):
    # Fake login verification
    from utils import user_utils

    def fake_verify(username, password):
        return {"status": "success", "userId": "fake-id", "message": "Login successful"}

    monkeypatch.setattr(user_utils, "verify_user", fake_verify)
    
    payload = {"username": "testuser", "password": "testpass"}
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Login successful"


def test_add_clothing(monkeypatch):
    # Fake clothing item insertion
    from utils import clothing_utils

    def fake_add_clothing_item(user_id, description, clothing_type=None, color=None,
                                 season=None, occasion=None, style=None, length=None):
        return {"id": "clothing-fake-id", "type": "Tops", "message": "Added Tops item successfully"}

    monkeypatch.setattr(clothing_utils, "add_clothing_item", fake_add_clothing_item)
    
    payload = {
        "userId": "fake-user-id",
        "description": "A stylish top",
        "type": "top"
    }
    response = client.post("/api/clothing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "Tops"
    assert data["message"] == "Added Tops item successfully"


def test_upload_clothing_with_description(monkeypatch):
    # Test upload endpoint using a text description (no file)
    from utils import clothing_utils

    # Define a fake function matching the signature of add_clothing_item
    def fake_add_clothing_item(user_id, description, clothing_type=None, **kwargs):
        return {
            "id": "clothing-fake-id",
            "type": "Accessories",
            "message": "Added Accessories item successfully"
        }

    monkeypatch.setattr(clothing_utils, "add_clothing_item", fake_add_clothing_item)
    
    payload = {
        "userId": "fake-user-id",
        "description": "A fancy accessory"
    }
    response = client.post("/upload-clothing", data=payload)
    assert response.status_code == 200
    data = response.json()
    # Expect the result to be returned within the response JSON
    assert "result" in data
    assert data["result"]["message"] == "Added Accessories item successfully"


def test_upload_clothing_with_file(monkeypatch):
    # Test upload endpoint with a file upload.
    # Patch caption_image in app/main (which was imported there) and add_clothing_item in utils.clothing_utils.
    from utils import clothing_utils

    # Patch the caption_image function used in the endpoint (imported into app/main)
    monkeypatch.setattr("app.main.caption_image", lambda file: "A generated description from image")
    
    # Define a fake add_clothing_item function with an explicit signature
    monkeypatch.setattr(
        clothing_utils,
        "add_clothing_item",
        lambda user_id, description, clothing_type=None, **kwargs: {
            "id": "clothing-fake-id",
            "type": "Tops",
            "message": "Added Tops item successfully"
        }
    )

    fake_image = BytesIO(b"fake image data")
    response = client.post(
        "/upload-clothing",
        data={"userId": "fake-user-id"},
        files={"file": ("test.jpg", fake_image, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["message"] == "Added Tops item successfully"


def test_upload_clothing_missing_input():
    # Test upload endpoint error when neither file nor description is provided.
    response = client.post("/upload-clothing", data={"userId": "fake-user-id"})
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "Provide either an image file or a text description" in data["error"]


def test_suggest_outfit(monkeypatch):
    # Fake functions for outfit suggestion.
    from utils import clothing_utils
    import app.services as services

    # Simulate two clothing items.
    monkeypatch.setattr(clothing_utils, "get_all_clothing_descriptions", lambda: ["Red shirt", "Blue jeans"])
    
    # Override fetch_weather to return fake weather data.
    monkeypatch.setattr(services, "fetch_weather", lambda location: {"temperature": 20, "description": "clear sky"})
    
    # Define a fixed, formatted outfit suggestion.
    formatted_suggestion = (
        "Shirt: Red shirt\n"
        "Pants: Blue jeans\n"
        "Accessories: None\n"
        "Shoes: None"
    )
    # Override get_outfit_suggestion to return the fixed formatted string.
    monkeypatch.setattr(
        services, 
        "get_outfit_suggestion", 
        lambda desc, occasion, age, style, location, weather: formatted_suggestion
    )
    
    payload = {
        "occasion": "casual",
        "age": "25",  # FastAPI will convert this to int
        "style_preferences": "modern",
        "location": "New York"
    }
    # Using GET with query parameters.
    response = client.get("/suggest-outfit", params=payload)
    assert response.status_code == 200
    data = response.json()
    assert "weather" in data
    assert "clothing_items" in data
    assert "outfit_suggestion" in data
    assert data["outfit_suggestion"] == formatted_suggestion
