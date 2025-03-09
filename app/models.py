from pydantic import BaseModel
from fastapi import UploadFile, Form, File
from typing import Optional

# Model for user registration and login
class User(BaseModel):
    username: str
    password: str

# Model for clothing item upload with description
class ClothingDescription(BaseModel):
    userId: str
    description: str

# Model for clothing item upload with image
class ClothingImage(BaseModel):
    userId: str
    image: UploadFile

    @classmethod
    def as_form(
        cls,
        userId: str = Form(...),
        image: UploadFile = File(...)
    ) -> "ClothingImage":
        return cls(userId=userId, image=image)


# Model for outfit suggestion request
class OutfitRequest(BaseModel):
    userId: str
    occasion: Optional[str] = None
    age: Optional[str] = None
    style_preferences: Optional[str] = None
    location: Optional[str] = None