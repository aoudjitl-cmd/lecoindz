# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.models.user import find_user_by_email, create_user, set_verification_token, verify_user_token
from src.middleware.auth import hash_password, verify_password, create_token, get_current_user
from fastapi import Depends
import resend
import os
import secrets

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str = None
    cgu_accepted_at: Optional[str] = None
    cgu_version: Optional[str] = "1.0"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    if not data.cgu_accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous devez accepter les Conditions Generales d'Utilisation"
        )

    if find_user_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est deja utilise"
        )

    hashed = hash_password(data.password)
    user = create_user(
        data.email, hashed, data.first_name, data.last_name, data.phone,
        cgu_accepted_at=data.cgu_accepted_at,
        cgu_version=data.cgu_version
    )

    token = secrets.token_urlsafe(32)
    set_verification_token(user["id"], token)

    verification_url = f"https://www.lecoindz.com/verify-email.html?token={token}"
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        resend.Emails.send({
            "from": "LeCoinDZ <noreply@lecoindz.com>",
            "to": [data.email],
            "subject": "Verifiez votre adresse email - LeCoinDZ",
            "html": f"""
                <div style="font-family:sans-serif; max-width:500px; margin:0 auto; padding:2rem;">
                    <h2 style="color:#e63946;">Bienvenue sur LeCoinDZ !</h2>
                    <p>Bonjour {data.first_name},</p>
                    <p>Merci de vous etre inscrit sur LeCoinDZ. Cliquez sur le bouton ci-dessous pour verifier votre adresse email :</p>
                    <a href="{verification_url}"
                       style="display:inline-block; background:#e63946; color:white; padding:12px 24px;
                              border-radius:8px; text-decoration:none; font-weight:600; margin:1rem 0;">
                        Verifier mon email
                    </a>
                    <p style="color:#64748b; font-size:0.85rem;">
                        Ce lien expire dans 24h. Si vous n'avez pas cree de compte, ignorez cet email.
                    </p>
                    <hr style="border:none; border-top:1px solid #e2e8f0; margin:1.5rem 0;">
                    <p style="color:#94a3b8; font-size:0.8rem;">LeCoinDZ - Achetez en France, recevez en Algerie</p>
                </div>
            """
        })
    except Exception as e:
        print(f"Erreur envoi email: {e}")

    return {
        "message": "Compte cree. Verifiez votre email pour activer votre compte.",
        "email_sent": True
    }

@router.get("/verify-email")
def verify_email(token: str):
    user = verify_user_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien de verification invalide ou expire"
        )
    jwt_token = create_token({"user_id": user["id"], "email": user["email"]})
    return {
        "message": "Email verifie avec succes",
        "token": jwt_token,
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

    if not user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez verifier votre email avant de vous connecter"
        )

    token = create_token({"user_id": user["id"], "email": user["email"]})
    return {
        "message": "Connexion reussie",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    }

class ChangePasswordRequest(BaseModel):
    password: str

@router.patch("/change-password")
def change_password(data: ChangePasswordRequest, current_user=Depends(get_current_user)):
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 6 caracteres")
    from src.config.database import get_connection
    hashed = hash_password(data.password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE LCD_USERS SET password = %s WHERE id = %s", (hashed, current_user["user_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Mot de passe mis a jour"}

@router.delete("/delete-account")
def delete_account(current_user=Depends(get_current_user)):
    from src.config.database import get_connection
    user_id = current_user["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM LCD_REVIEWS WHERE reviewer_id = %s OR reviewed_id = %s", (user_id, user_id))
        cursor.execute("SELECT id FROM LCD_CONVERSATIONS WHERE user1_id = %s OR user2_id = %s", (user_id, user_id))
        conv_ids = [r[0] for r in cursor.fetchall()]
        if conv_ids:
            placeholders = ",".join(["%s"] * len(conv_ids))
            cursor.execute(f"DELETE FROM LCD_DIRECT_MESSAGES WHERE conversation_id IN ({placeholders})", conv_ids)
        cursor.execute("DELETE FROM LCD_CONVERSATIONS WHERE user1_id = %s OR user2_id = %s", (user_id, user_id))
        cursor.execute("SELECT id FROM LCD_ORDERS WHERE buyer_id = %s OR shopper_id = %s", (user_id, user_id))
        order_ids = [r[0] for r in cursor.fetchall()]
        if order_ids:
            placeholders = ",".join(["%s"] * len(order_ids))
            cursor.execute(f"DELETE FROM LCD_MESSAGES WHERE order_id IN ({placeholders})", order_ids)
            cursor.execute(f"DELETE FROM LCD_ORDERS WHERE id IN ({placeholders})", order_ids)
        cursor.execute("DELETE FROM LCD_PRODUCTS WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM LCD_SHOPPERS WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM LCD_USERS WHERE id = %s", (user_id,))
        conn.commit()
        return {"message": "Compte supprime"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()