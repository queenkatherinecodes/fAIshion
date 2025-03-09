# tests/test_main.py
import io
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app from main.py file
from app.main import app

client = TestClient(app)


# -------------------------
# Dummy Classes for Database
# -------------------------
class DummyCursor:
    def execute(self, sql):
        pass

    def fetchone(self):
        return (1,)

    def close(self):
        pass


class DummyConnection:
    def cursor(self):
        return DummyCursor()

    def close(self):
        pass


def dummy_connect(conn_str):
    return DummyConnection()


# -------------------------
# Test the root endpoint
# -------------------------
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World from fAIshion API!"}


# -------------------------
# Test the health endpoint
# -------------------------
def test_health(monkeypatch):
    # Monkeypatch pyodbc.connect to simulate a successful DB connection.
    import pyodbc
    monkeypatch.setattr(pyodbc, "connect", dummy_connect)

    response = client.get("/health")
    data = response.json()
    assert response.status_code == 200
    # With our dummy connection, the health endpoint should indicate a "connected" status.
    assert data.get("status") == "healthy"
    assert data.get("database_status") == "connected"


# -------------------------
# Test the /upload-clothing endpoint without any input
# -------------------------
def test_upload_clothing_no_input():
    response = client.post("/upload-clothing", data={})
    data = response.json()
    # When neither an image nor a description is provided, an error is returned.
    assert response.status_code == 200
    assert "error" in data
    assert data["error"] == "Provide either an image file or a text description."


# -------------------------
# Test the /upload-clothing endpoint with a text description
# -------------------------
def test_upload_clothing_with_description():
    test_description = "A nice summer dress"
    response = client.post("/upload-clothing", data={"description": test_description})
    data = response.json()
    assert response.status_code == 200
    assert data.get("message") == "Clothing item uploaded successfully"
    # Since no file was provided, the endpoint uses the description as is.
    assert data.get("description") == test_description


# -------------------------
# Test the /upload-clothing endpoint with an image file
# -------------------------
def test_upload_clothing_with_file(monkeypatch):
    # Monkeypatch the caption_image function so that we avoid actually processing an image.
    monkeypatch.setattr("services.caption_image", lambda file: "Test caption from image")

    # Create a dummy image file (using io.BytesIO).
    dummy_image = io.BytesIO(b"fake image data")
    dummy_image.name = "test.jpg"

    response = client.post(
        "/upload-clothing",
        data={"description": ""},
        files={"file": ("test.jpg", dummy_image, "image/jpeg")},
    )
    data = response.json()
    assert response.status_code == 200
    assert data.get("message") == "Clothing item uploaded successfully"
    assert data.get("description") == "Test caption from image"


# -------------------------
# Test the /suggest-outfit endpoint
# -------------------------
def test_suggest_outfit(monkeypatch):
    # The endpoint expects a function get_all_clothing_descriptions() to be available.
    # Since the database is not implemented, we monkeypatch it to return dummy clothing items.
    monkeypatch.setattr("main.get_all_clothing_descriptions", lambda: ["Red Shirt", "Blue Jeans"])

    # Monkeypatch the weather fetching function in services to avoid an external API call.
    monkeypatch.setattr("services.fetch_weather", lambda location: {"temperature": 22, "description": "sunny"})

    # Monkeypatch the outfit suggestion function to return a fixed suggestion.
    monkeypatch.setattr(
        "services.get_outfit_suggestion",
        lambda descriptions, occasion, age, style, location, weather: "Outfit: Red Shirt with Blue Jeans.",
    )

    # Provide form data for the suggestion.
    form_data = {
        "occasion": "casual",
        "age": "25",
        "style_preferences": "modern",
        "location": "New York",
    }

    response = client.post("/suggest-outfit", data=form_data)
    data = response.json()
    assert response.status_code == 200
    # Check that the response contains the expected keys and the fixed suggestion.
    assert "weather" in data
    assert "clothing_items" in data
    assert "outfit_suggestion" in data
    assert data["outfit_suggestion"] == "Outfit: Red Shirt with Blue Jeans."
