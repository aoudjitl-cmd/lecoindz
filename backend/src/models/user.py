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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO CG_USERS (email, password, first_name, last_name, phone, cgu_accepted_at, cgu_version)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (email, password, first_name, last_name, phone, cgu_accepted_at, cgu_version)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return find_user_by_email(email)