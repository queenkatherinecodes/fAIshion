#app/services.py
import requests
import openai
from transformers import pipeline
from PIL import Image
from app.config import WEATHER_API_KEY, OPENAI_API_KEY

# Initialize OpenAI and the image captioning pipeline
openai.api_key = OPENAI_API_KEY
captioner = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")

def fetch_weather(location: str) -> dict:
    """Fetch current weather data for a given location using the OpenWeatherMap API."""
    weather_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(weather_url, params=params)
    if response.status_code != 200:

        raise Exception(f"Failed to fetch weather: {response.text}")
    weather_data = response.json()
    temperature = weather_data.get("main", {}).get("temp")
    description = weather_data.get("weather", [{}])[0].get("description", "No description available")
    return {"temperature": temperature, "description": description}

def caption_image(file) -> str:
    """
    Generate a description for the clothing item using the Hugging Face image captioning pipeline.
    """
    try:
        image = Image.open(file)
        file.seek(0)  # Reset file pointer for further use if needed
        caption_output = captioner(image)
        return caption_output[0]['generated_text']
    except Exception as e:
        return f"Unable to generate caption: {str(e)}"

def get_outfit_suggestion(clothing_descriptions: str, occasion: str, age: int, style_preferences: str,
                          location: str, weather: dict) -> str:
    """
    Build a prompt that includes all clothing descriptions plus additional details,
    then call OpenAI's API to generate an outfit suggestion.
    """
    prompt = (
        f"Based on the following clothing items:\n"
        f"{clothing_descriptions}\n\n"
        f"And additional details:\n"
        f"- Occasion: {occasion}\n"
        f"- Age: {age if age is not None else 'N/A'}\n"
        f"- Style preferences: {style_preferences if style_preferences else 'N/A'}\n"
        f"- Current weather in {location}: {weather['temperature']}°C, {weather['description']}\n\n"
        f"Please suggest a complete outfit that would be suitable."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful fashion stylist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        suggestion = response["choices"][0]["message"]["content"].strip()
        return suggestion
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")
