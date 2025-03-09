# app/services.py
import requests
import os
from openai import OpenAI
from transformers import pipeline
from PIL import Image
import logging
import base64
from ml.outfit_suggester import OutfitSuggester
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)  # initialize logger

# Initialize OpenAI and the image captioning pipeline
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), 
)
captioner = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")

# Initialize the ML Outfit Suggestor
outfit_suggester = OutfitSuggester()

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
    Generate an outfit suggestion using ML approach exclusively.
    
    Args:
        clothing_descriptions: String with clothing items, one per line prefixed with "- "
        occasion: String describing the event or situation
        age: Integer representing user's age
        style_preferences: String with comma-separated style preferences
        location: String with location name for weather
        weather: Dictionary with 'temperature' and 'description' keys
        
    Returns:
        String with formatted outfit suggestion
    """
    logger.info(f"Generating ML-based outfit suggestion for occasion: {occasion}")
    
    # Parse clothing descriptions into a list
    clothing_items = [desc.strip() for desc in clothing_descriptions.split('\n') if desc.strip()]
    
    # Extract descriptions without the leading "- "
    cleaned_items = [item[2:] if item.startswith('- ') else item for item in clothing_items]
    
    # Generate outfit using the ML model
    outfit = outfit_suggester.suggest_outfit(
        clothing_descriptions=cleaned_items,
        occasion=occasion,
        weather_description=weather['description'],
        temperature=weather['temperature']
    )
    
    # Format the result
    outfit_suggestion = outfit_suggester.format_outfit_suggestion(outfit)
    
    logger.info("ML-based outfit suggestion generated successfully")
    return outfit_suggestion


def parse_outfit_suggestion(outfit_text: str) -> Dict[str, str]:
    """
    Parse the outfit suggestion text into a structured dictionary.
    
    Args:
        outfit_text: String with the outfit suggestion (e.g., "Top: white shirt\nBottom: black pants")
        
    Returns:
        Dictionary with clothing categories as keys and descriptions as values
    """
    outfit_dict = {}
    
    # Split by lines and process each line
    lines = outfit_text.strip().split('\n')
    for line in lines:
        if ':' in line:
            # Split by the first colon
            parts = line.split(':', 1)
            category = parts[0].strip().lower()
            item = parts[1].strip()
            outfit_dict[category] = item
    
    return outfit_dict


def get_user_photo_as_base64(user_id: str) -> Optional[str]:
    """
    Get the user's photo as a base64 string from the uploads directory.
    
    Args:
        user_id: User ID to find the photo
        
    Returns:
        Base64-encoded image or None if not found
    """
    photo_path = f"uploads/{user_id}.jpeg"
    
    if not os.path.exists(photo_path):
        logger.warning(f"User photo not found at {photo_path}")
        return None
    
    try:
        with open(photo_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded_image}"
    except Exception as e:
        logger.error(f"Error reading user photo: {str(e)}")
        return None


def generate_outfit_avatar(outfit_suggestion: str, user_id: str = None, gender: str = "neutral") -> str:
    """
    Generate an avatar image based on the outfit suggestion, optionally using the user's photo.
    
    Args:
        outfit_suggestion: String with the outfit suggestion text
        user_id: User ID to find their photo (if None, generic avatar is created)
        gender: String indicating avatar gender preference if no photo is available
        
    Returns:
        Base64-encoded image data URL for the generated avatar
    """
    logger.info("Generating avatar for outfit")
    
    # Parse the outfit suggestion into a structured format
    outfit_parts = parse_outfit_suggestion(outfit_suggestion)
    
    # Construct the outfit description from the parsed parts
    outfit_description = ""
    for category, item in outfit_parts.items():
        outfit_description += f"{item}, "
    
    # Remove trailing comma and space
    outfit_description = outfit_description.rstrip(", ")
    
    # Check if we have a user photo
    user_photo = None if user_id is None else get_user_photo_as_base64(user_id)
    
    try:
        # Create the prompt based on whether we have a user photo
        if user_photo:
            prompt = (
                f"Create a realistic full-body digital avatar wearing the following outfit: {outfit_description}. "
                f"Use this base user's face/head image to create a personalized avatar. "
                f"The avatar should be shown in a natural pose against a plain white background, "
                f"with the outfit clearly visible. Style should be realistic but slightly stylized, "
                f"like a fashion app illustration."
            )
            
            # Generate the image using DALL-E with the user photo included
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
                user_image=user_photo
            )
        else:
            # Use a store mannequin as fallback
            mannequin_type = "neutral store mannequin"
            if gender.lower() == "male":
                mannequin_type = "male store mannequin"
            elif gender.lower() == "female":
                mannequin_type = "female store mannequin"
                
            prompt = (
                f"Create a realistic image of a {mannequin_type} wearing the following outfit: "
                f"{outfit_description}. The mannequin should be shown from the front against a clean white background. "
                f"The mannequin should be in a standard store display pose, with the outfit presented clearly. "
                f"Use a realistic retail store display style with professional lighting to highlight the clothing details."
            )
            
            # Generate the image using DALL-E without a user photo
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
        
        # Get the base64-encoded image data
        image_b64 = response.data[0].b64_json
        
        # Create a data URL
        image_data_url = f"data:image/png;base64,{image_b64}"
        
        logger.info("Avatar generated successfully")
        return image_data_url
        
    except Exception as e:
        logger.error(f"Avatar generation error: {str(e)}")
        # If DALL-E fails, return a placeholder or error message
        return f"Error generating avatar: {str(e)}"


def get_outfit_with_avatar(clothing_descriptions: str, occasion: str, age: int, style_preferences: str,
                          location: str, weather: dict, user_id: str = None, gender: str = "neutral") -> Dict[str, Any]:
    """
    Generate an outfit suggestion and corresponding avatar.
    
    Args:
        clothing_descriptions: String with clothing items
        occasion: String describing the event
        age: Integer representing user's age
        style_preferences: String with style preferences
        location: String with location name
        weather: Dictionary with weather information
        user_id: Optional user ID to find their photo
        gender: String indicating avatar gender preference if no photo is available
        
    Returns:
        Dictionary with outfit suggestion text and avatar image
    """
    # Get the outfit suggestion
    outfit_suggestion = get_outfit_suggestion(
        clothing_descriptions, occasion, age, style_preferences, location, weather
    )
    
    # Generate the avatar for the outfit
    avatar_image = generate_outfit_avatar(outfit_suggestion, user_id, gender)
    
    # Return both the suggestion and the avatar
    return {
        "outfit_suggestion": outfit_suggestion,
        "avatar_image": avatar_image
    }