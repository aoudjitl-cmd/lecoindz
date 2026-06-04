from src.config.database import get_connection

def send_message(booking_id, sender_id, content):
    """Envoie un message dans une réservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_MESSAGES (booking_id, sender_id, content)
        VALUES (%(booking_id)s, %(sender_id)s, %(content)s)
    """, {"booking_id": booking_id, "sender_id": sender_id, "content": content})
    conn.commit()
    cursor.close()
    conn.close()

def get_messages(booking_id):
    """Récupère tous les messages d'une réservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.booking_id, m.sender_id, m.content,
               m.is_read, m.created_at,
               u.first_name, u.last_name
        FROM CG_MESSAGES m
        JOIN CG_USERS u ON m.sender_id = u.id
        WHERE m.booking_id = %(booking_id)s
        ORDER BY m.created_at ASC
    """, {"booking_id": booking_id})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_message(row) for row in rows]

def mark_as_read(booking_id, user_id):
    """Marque les messages comme lus pour un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_MESSAGES
        SET is_read = 1
        WHERE booking_id = %(booking_id)s
        AND sender_id != %(user_id)s
        AND is_read = 0
    """, {"booking_id": booking_id, "user_id": user_id})
    conn.commit()
    cursor.close()
    conn.close()

def count_unread(user_id):
    """Compte les messages non lus pour un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM CG_MESSAGES m
        JOIN CG_BOOKINGS b ON m.booking_id = b.id
        WHERE (b.sender_id = %(user_id)s OR b.carrier_id = %(user_id)s)
        AND m.sender_id != %(user_id)s
        AND m.is_read = 0
    """, {"user_id": user_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else 0

def _format_message(row):
    return {
        "id": row[0],
        "booking_id": row[1],
        "sender_id": row[2],
        "content": row[3],
        "is_read": row[4],
        "created_at": str(row[5]),
        "sender": {"first_name": row[6], "last_name": row[7]}
    }