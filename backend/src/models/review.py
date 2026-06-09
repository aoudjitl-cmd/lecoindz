# -*- coding: utf-8 -*-
from src.config.database import get_connection

def create_review(reviewer_id, reviewed_id, booking_id, rating, comment=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_REVIEWS (reviewer_id, reviewed_id, booking_id, rating, comment)
        VALUES (%(reviewer_id)s, %(reviewed_id)s, %(booking_id)s, %(rating)s, %(comment)s)
    """, {
        "reviewer_id": reviewer_id, "reviewed_id": reviewed_id,
        "booking_id": booking_id, "rating": rating, "comment": comment
    })
    conn.commit()

    # Recalculer la moyenne du rating de l'utilisateur note
    cursor.execute("""
        UPDATE CG_USERS
        SET rating = (
            SELECT ROUND(AVG(rating), 1)
            FROM CG_REVIEWS
            WHERE reviewed_id = %(reviewed_id)s
        )
        WHERE id = %(reviewed_id)s
    """, {"reviewed_id": reviewed_id})
    conn.commit()
    cursor.close()
    conn.close()

def get_reviews_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.reviewer_id, r.reviewed_id, r.booking_id,
               r.rating, r.comment, r.created_at,
               u.first_name, u.last_name
        FROM CG_REVIEWS r
        JOIN CG_USERS u ON r.reviewer_id = u.id
        WHERE r.reviewed_id = %(user_id)s
        ORDER BY r.created_at DESC
    """, {"user_id": user_id})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_review(row) for row in rows]

def get_review_by_booking(reviewer_id, booking_id):
    """Verifie si un avis existe deja pour cette reservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM CG_REVIEWS
        WHERE reviewer_id = %(reviewer_id)s AND booking_id = %(booking_id)s
    """, {"reviewer_id": reviewer_id, "booking_id": booking_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None

def _format_review(row):
    return {
        "id": row[0], "reviewer_id": row[1], "reviewed_id": row[2],
        "booking_id": row[3], "rating": row[4], "comment": row[5],
        "created_at": str(row[6]),
        "reviewer": {"first_name": row[7], "last_name": row[8]}
    }