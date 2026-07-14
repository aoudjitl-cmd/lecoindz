# -*- coding: utf-8 -*-
from src.config.database import get_connection

def find_user_by_email(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, password, first_name, last_name, phone, is_verified, rating FROM LCD_USERS WHERE email = %s",
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

def create_user(email, password, first_name, last_name,
                phone=None, cgu_accepted_at=None, cgu_version="1.0"):
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
        """INSERT INTO LCD_USERS (email, password, first_name, last_name, phone,
           cgu_accepted_at, cgu_version, is_verified, subscription_status,
           trial_end)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 'TRIAL',
           DATE_ADD(CURDATE(), INTERVAL 1 YEAR))""",
        (email, password, first_name, last_name, phone, cgu_dt, cgu_version)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return find_user_by_email(email)

def set_verification_token(user_id, token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE LCD_USERS SET verification_token = %s WHERE id = %s", (token, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def verify_user_token(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, first_name, last_name FROM LCD_USERS WHERE verification_token = %s AND is_verified = 0",
        (token,)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None
    cursor.execute(
        "UPDATE LCD_USERS SET is_verified = 1, verification_token = NULL WHERE id = %s",
        (row[0],)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"id": row[0], "email": row[1], "first_name": row[2], "last_name": row[3]}