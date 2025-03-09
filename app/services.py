# app/services.py
import requests
import os
from openai import OpenAI
from transformers import pipeline
from PIL import Image
import logging

logger = logging.getLogger(__name__)  # initialize logger

# Initialize OpenAI and the image captioning pipeline
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
)
captioner = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")

def fetch_weather(location: str) -> dict:
    """Fetch current weather data for a given location using the OpenWeatherMap API."""
    weather_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": os.getenv("WEATHER_API_KEY"),
        "units": "metric"
    }
    response = requests.get(weather_url, params=params)
    if response.status_code != 200:
        logger.error(f"Failed to fetch weather for {location}: {response.text}") 
        raise Exception(f"Failed to fetch weather: {response.text}")
    weather_data = response.json()
    temperature = weather_data.get("main", {}).get("temp")
    description = weather_data.get("weather", [{}])[0].get("description", "No description available")
    logger.info(f"Weather fetched for {location}: {temperature}°C, {description}")
    return {"temperature": temperature, "description": description}

def caption_image(file: IO) -> str:
    try:
        with Image.open(file) as image:
            file.seek(0)
            caption_output = captioner(image)
        logger.info("Image caption generated")
        return caption_output[0]['generated_text']
    except Exception as e:
        logger.error(f"Caption image error: {str(e)}")
        raise RuntimeError(f"Unable to generate caption: {str(e)}")


def get_outfit_suggestion(clothing_descriptions: str, occasion: str, age: int, style_preferences: str,
                          location: str, weather: dict) -> str:
    """
    Build a prompt that includes all clothing descriptions plus additional details,
    then call OpenAI's API to generate an outfit suggestion.
    The suggestion is forced into a consistent format with:
      Shirt: <...>
      Pants: <...>
      Accessories: <...>
      Shoes: <...>
    """
    prompt = (
        f"Based on the following clothing items:\n"
        f"{clothing_descriptions}\n\n"
        f"And additional details:\n"
        f"- Occasion: {occasion}\n"
        f"- Age: {age if age is not None else 'N/A'}\n"
        f"- Style preferences: {style_preferences if style_preferences else 'N/A'}\n"
        f"- Current weather in {location}: {weather['temperature']}°C, {weather['description']}\n\n"
        "Please suggest a complete outfit that would be suitable, and return your answer in exactly the following format:\n"
        "Shirt: <your suggestion for a shirt>\n"
        "Pants: <your suggestion for pants>\n"
        "Accessories: <your suggestion for accessories>\n"
        "Shoes: <your suggestion for shoes>\n"
    )
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful fashion stylist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        raw_suggestion = completion.choices[0].message.content.strip()
        # Normalize the output: remove extra spaces and ensure one line per label.
        lines = raw_suggestion.splitlines()
        normalized_lines = [line.strip() for line in lines if line.strip()]
        final_output = "\n".join(normalized_lines)
        return final_output
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")
