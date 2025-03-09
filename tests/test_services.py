# tests/test_services.py
import unittest
from unittest.mock import patch, Mock, MagicMock
import os
import json
import io
from PIL import Image
import pytest

from app.services import fetch_weather, caption_image, get_outfit_suggestion

class TestFetchWeather(unittest.TestCase):
    @patch('app.services.requests.get')
    def test_fetch_weather_success(self, mock_get):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 21.5
            },
            "weather": [
                {
                    "description": "clear sky"
                }
            ]
        }
        mock_get.return_value = mock_response
        location = "London"

        # Act
        result = fetch_weather(location)

        # Assert
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs['params']['q'] == location
        assert result == {"temperature": 21.5, "description": "clear sky"}

    @patch('app.services.requests.get')
    def test_fetch_weather_api_error(self, mock_get):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "City not found"
        mock_get.return_value = mock_response
        location = "NonExistentCity"

        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            fetch_weather(location)
        
        assert "Failed to fetch weather" in str(excinfo.value)

    @patch('app.services.requests.get')
    def test_fetch_weather_missing_data(self, mock_get):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{}]
        }
        mock_get.return_value = mock_response
        location = "Berlin"

        # Act
        result = fetch_weather(location)

        # Assert
        assert result == {"temperature": None, "description": "No description available"}


class TestCaptionImage(unittest.TestCase):
    @patch('app.services.pipeline')
    def test_caption_image_success(self, mock_pipeline):
        # Arrange
        mock_captioner = MagicMock()
        mock_captioner.return_value = [{'generated_text': 'a red t-shirt'}]
        test_img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Act
        with patch('app.services.captioner', mock_captioner):
            result = caption_image(img_bytes)
            
        # Assert
        mock_captioner.assert_called_once()
        assert result == "a red t-shirt"

    def test_caption_image_error(self):
        # Arrange
        invalid_file = io.BytesIO(b"not an image")
        
        # Act
        result = caption_image(invalid_file)
        
        # Assert
        assert "Unable to generate caption" in result


class TestGetOutfitSuggestion(unittest.TestCase):
    @patch('app.services.client.chat.completions.create')
    def test_get_outfit_suggestion_success(self, mock_create):
        # Arrange
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = """
        Shirt: White cotton button-down shirt
        Pants: Navy blue chinos
        Accessories: Silver watch and brown leather belt
        Shoes: Brown leather loafers
        """
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        clothing_descriptions = "White shirt, blue jeans, black dress shoes, brown belt"
        occasion = "Business casual"
        age = 30
        style_preferences = "Classic and minimalist"
        location = "New York"
        weather = {"temperature": 18, "description": "partly cloudy"}

        # Act
        result = get_outfit_suggestion(
            clothing_descriptions, occasion, age, style_preferences, location, weather
        )

        # Assert
        mock_create.assert_called_once()
        expected_lines = [
            "Shirt: White cotton button-down shirt",
            "Pants: Navy blue chinos",
            "Accessories: Silver watch and brown leather belt",
            "Shoes: Brown leather loafers"
        ]
        result_lines = [line.strip() for line in result.strip().split('\n')]
        assert result_lines == expected_lines

    @patch('app.services.client.chat.completions.create')
    def test_get_outfit_suggestion_api_error(self, mock_create):
        # Arrange
        mock_create.side_effect = Exception("Rate limit exceeded")
        clothing_descriptions = "White shirt, blue jeans"
        occasion = "Casual"
        age = 25
        style_preferences = "Relaxed"
        location = "Miami"
        weather = {"temperature": 30, "description": "sunny"}

        # Act
        with pytest.raises(Exception) as excinfo:
            get_outfit_suggestion(
                clothing_descriptions, occasion, age, style_preferences, location, weather
            )
        
        # Assert
        assert "OpenAI API error" in str(excinfo.value)

    @patch('app.services.client.chat.completions.create')
    def test_get_outfit_suggestion_with_none_values(self, mock_create):
        # Arrange
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = """
        Shirt: Casual T-shirt
        Pants: Jeans
        Accessories: None
        Shoes: Sneakers
        """
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response

        clothing_descriptions = "T-shirt, jeans, sneakers"
        occasion = "Casual outing"
        age = None
        style_preferences = None
        location = "Seattle"
        weather = {"temperature": 15, "description": "rainy"}

        # Act
        result = get_outfit_suggestion(
            clothing_descriptions, occasion, age, style_preferences, location, weather
        )

        # Assert
        mock_create.assert_called_once()
        assert "Shirt:" in result
        assert "Pants:" in result