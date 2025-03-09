# app/services.py
import requests
import os
from openai import OpenAI
from transformers import pipeline
from PIL import Image
import logging
import base64

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

def convert_img(file) -> str:
    """
    Convert an image file to a base64 string.
    """
    try:
        file.seek(0)
        encoded_image = base64.b64encode(file.read()).decode("utf-8")
        # Create a data URL for the image
        image_data_url = f"data:image/jpeg;base64,{encoded_image}"
    except Exception as e:
        logger.error(f"Image conversion error: {str(e)}")
        return f"Unable to convert image: {str(e)}"
    return image_data_url


def caption_image(img_url) -> str:
    prompt = (
        "Provided with an image give a short description of the clothing item."
        )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": img_url}
                        }
                    ]
                }
            ],
            max_tokens=300,
        )
    except Exception as e:
        logger.error(f"Image caption error: {str(e)}")
        return f"Unable to generate caption: {str(e)}"

    return response.choices[0].message.content.strip()


def get_outfit_suggestion(clothing_descriptions: str, occasion: str, age: int, style_preferences: str,
                          location: str, weather: dict) -> str:
    """
    Build a prompt that includes all clothing descriptions plus additional details,
    then call OpenAI's API to generate an outfit suggestion.
    """
    prompt = (
        "Based on the following clothing items:\n"
        f"{clothing_descriptions}\n\n"
        "Additional details:\n"
        f"- Occasion: {occasion}\n"
        f"- Age: {age if age is not None else 'N/A'}\n"
        f"- Style preferences: {style_preferences if style_preferences else 'N/A'}\n"
        f"- Current weather in {location}: {weather['temperature']}°C, {weather['description']}\n\n"
        "Suggest a complete outfit using only the provided clothing items."
        "Format your response as bullet points, with each item labeled (e.g., Top, Bottom, Accessories)"
        "just give a raw suggestion."
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
