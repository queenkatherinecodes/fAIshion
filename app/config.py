# app/config.py
import os

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your_default_weather_api_key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_default_openai_api_key")