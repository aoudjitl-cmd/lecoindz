from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from src.models.user import find_user_by_email, create_user
from src.middleware.auth import hash_password, verify_password, create_token

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    if find_user_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    hashed = hash_password(data.password)
    user = create_user(data.email, hashed, data.first_name, data.last_name, data.phone)
    token = create_token({"user_id": user["id"], "email": user["email"]})
    return {
        "message": "Compte créé avec succès",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    }

@router.post("/login")
def login(data: LoginRequest):
    user = find_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    token = create_token({"user_id": user["id"], "email": user["email"]})
    return {
        "message": "Connexion réussie",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    }