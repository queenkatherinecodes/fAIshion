# app/config.py
import os

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your_default_weather_api_key")
