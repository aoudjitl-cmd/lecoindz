# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.middleware.auth import get_current_user
from src.config.database import get_connection

router = APIRouter()

class ReviewRequest(BaseModel):
    order_id: int
    rating: int
    comment: Optional[str] = None

def get_order_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, shopper_id, buyer_id, status FROM LCD_ORDERS WHERE id = %s", (order_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {"id": row[0], "shopper_id": row[1], "buyer_id": row[2], "status": row[3]}
    return None

def get_review_by_order(reviewer_id, order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM LCD_REVIEWS WHERE reviewer_id = %s AND order_id = %s",
        (reviewer_id, order_id)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None

def create_review(reviewer_id, reviewed_id, order_id, rating, comment=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LCD_REVIEWS (reviewer_id, reviewed_id, order_id, rating, comment)
        VALUES (%s, %s, %s, %s, %s)
    """, (reviewer_id, reviewed_id, order_id, rating, comment))
    conn.commit()
    cursor.execute("""
        UPDATE LCD_USERS
        SET rating = (SELECT ROUND(AVG(rating), 1) FROM LCD_REVIEWS WHERE reviewed_id = %s),
            nb_ratings = (SELECT COUNT(*) FROM LCD_REVIEWS WHERE reviewed_id = %s)
        WHERE id = %s
    """, (reviewed_id, reviewed_id, reviewed_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_reviews_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.reviewer_id, r.reviewed_id, r.order_id,
               r.rating, r.comment, r.created_at,
               u.first_name, u.last_name
        FROM LCD_REVIEWS r
        JOIN LCD_USERS u ON r.reviewer_id = u.id
        WHERE r.reviewed_id = %s
        ORDER BY r.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{
        "id": row[0], "reviewer_id": row[1], "reviewed_id": row[2],
        "order_id": row[3], "rating": row[4], "comment": row[5],
        "created_at": str(row[6]),
        "reviewer": {"first_name": row[7], "last_name": row[8]}
    } for row in rows]

@router.post("/", status_code=201)
def add_review(data: ReviewRequest, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    order = get_order_by_id(data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order["status"] != "DELIVERED":
        raise HTTPException(status_code=400, detail="La commande doit etre livree pour laisser un avis")
    if user_id != order["buyer_id"] and user_id != order["shopper_id"]:
        raise HTTPException(status_code=403, detail="Vous ne faites pas partie de cette commande")
    if get_review_by_order(user_id, data.order_id):
        raise HTTPException(status_code=400, detail="Vous avez deja laisse un avis")
    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="La note doit etre entre 1 et 5")

    reviewed_id = order["shopper_id"] if user_id == order["buyer_id"] else order["buyer_id"]
    create_review(user_id, reviewed_id, data.order_id, data.rating, data.comment)
    return {"message": "Avis publie avec succes"}

@router.get("/user/{user_id}")
def get_user_reviews(user_id: int):
    reviews = get_reviews_for_user(user_id)
    total = len(reviews)
    avg = round(sum(r["rating"] for r in reviews) / total, 1) if total > 0 else None
    return {"total": total, "average": avg, "reviews": reviews}