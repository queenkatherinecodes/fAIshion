from pydantic import BaseModel
from fastapi import UploadFile
from typing import Optional

# Model for user registration and login
class User(BaseModel):
    username: str
    password: str

# Model for clothing item upload
class ClothingItem(BaseModel):
    userId: str
    description: Optional[str] = None
    file: Optional[UploadFile] = None

# Model for outfit suggestion request
class OutfitRequest(BaseModel):
    userId: str
    occasion: Optional[str] = None
    age: Optional[str] = None
    style_preferences: Optional[str] = None
    location: Optional[str] = None