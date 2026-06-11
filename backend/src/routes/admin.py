# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from src.middleware.auth import get_current_user
from src.config.database import get_connection

router = APIRouter()

def require_admin(current_user=Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM LCD_USERS WHERE id = %s", (current_user["user_id"],))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=403, detail="Acces admin requis")
    return current_user

@router.get("/users")
def get_users(current_user=Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, first_name, last_name, phone,
               is_verified, is_admin, subscription_status,
               rating, nb_ratings, created_at, trial_end
        FROM LCD_USERS ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"users": [{
        "id": r[0], "email": r[1],
        "first_name": r[2], "last_name": r[3],
        "phone": r[4], "is_verified": r[5],
        "is_admin": r[6], "subscription_status": r[7],
        "rating": float(r[8]) if r[8] else None,
        "nb_ratings": r[9], "created_at": str(r[10]),
        "trial_end": str(r[11]) if r[11] else None
    } for r in rows]}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user=Depends(require_admin)):
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM LCD_USERS WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")

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
        return {"message": "Utilisateur supprime avec succes"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.patch("/users/{user_id}/verify")
def verify_user(user_id: int, current_user=Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE LCD_USERS SET is_verified = 1 WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Utilisateur verifie"}

@router.patch("/users/{user_id}/block")
def block_user(user_id: int, current_user=Depends(require_admin)):
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous bloquer vous-meme")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE LCD_USERS SET is_verified = 0 WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Utilisateur bloque"}

@router.patch("/users/{user_id}/stop-trial")
def stop_trial(user_id: int, current_user=Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE LCD_USERS SET subscription_status = 'CANCELLED', trial_end = CURDATE()
        WHERE id = %s
    """, (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Periode d'essai arretee"}