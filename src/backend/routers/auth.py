"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from backend.database import teachers_collection

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# Initialize password hasher
ph = PasswordHasher()

@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})
    
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    try:
        # Verify the password using Argon2
        ph.verify(teacher["password"], password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Return teacher information (excluding password)
    return {
        "username": username,
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }

@router.get("/check-session")
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.find_one({"_id": username})
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {
        "username": username,
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }