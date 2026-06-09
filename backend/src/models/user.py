# -*- coding: utf-8 -*-
from src.config.database import get_connection

def find_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, password, first_name, last_name, phone, is_verified, rating FROM CG_USERS WHERE email = %s",
        (email,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "id": row[0], "email": row[1], "password": row[2],
            "first_name": row[3], "last_name": row[4],
            "phone": row[5], "is_verified": row[6], "rating": row[7]
        }
    return None

def create_user(email: str, password: str, first_name: str, last_name: str,
                phone: str = None, cgu_accepted_at: str = None, cgu_version: str = "1.0"):
    # Convertir le format ISO (2026-06-09T15:13:18.397Z) en format MySQL (2026-06-09 15:13:18)
    cgu_dt = None
    if cgu_accepted_at:
        try:
            from datetime import datetime
            cgu_dt = datetime.fromisoformat(cgu_accepted_at.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            cgu_dt = None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO CG_USERS (email, password, first_name, last_name, phone, cgu_accepted_at, cgu_version, is_verified)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0)""",
        (email, password, first_name, last_name, phone, cgu_dt, cgu_version)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return find_user_by_email(email)

def set_verification_token(user_id: int, token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE CG_USERS SET verification_token = %s WHERE id = %s",
        (token, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def verify_user_token(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, first_name, last_name FROM CG_USERS WHERE verification_token = %s AND is_verified = 0",
        (token,)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None
    # Activer le compte et supprimer le token
    cursor.execute(
        "UPDATE CG_USERS SET is_verified = 1, verification_token = NULL WHERE id = %s",
        (row[0],)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": row[0], "email": row[1], "first_name": row[2], "last_name": row[3]}