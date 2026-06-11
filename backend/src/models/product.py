# -*- coding: utf-8 -*-
from src.config.database import get_connection

def create_product(user_id, url, title=None, price=None, image_url=None,
                   description=None, size=None, color=None, quantity=1, commission=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LCD_PRODUCTS (user_id, url, title, price, image_url,
                                  description, size, color, quantity, commission)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, url, title, price, image_url, description, size, color, quantity, commission))
    conn.commit()
    cursor.close()
    conn.close()

def get_products(dest_country=None, category=None, max_price=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.id, p.user_id, u.first_name, u.last_name, u.rating,
               p.url, p.title, p.price, p.image_url, p.description,
               p.size, p.color, p.quantity, p.commission, p.status, p.created_at
        FROM LCD_PRODUCTS p
        JOIN LCD_USERS u ON p.user_id = u.id
        WHERE p.status = 'PENDING'
    """
    params = []
    if max_price:
        query += " AND p.commission <= %s"
        params.append(max_price)
    query += " ORDER BY p.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_product(row) for row in rows]

def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.user_id, u.first_name, u.last_name, u.rating,
               p.url, p.title, p.price, p.image_url, p.description,
               p.size, p.color, p.quantity, p.commission, p.status, p.created_at
        FROM LCD_PRODUCTS p
        JOIN LCD_USERS u ON p.user_id = u.id
        WHERE p.id = %s
    """, (product_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _format_product(row) if row else None

def _format_product(row):
    return {
        "id": row[0], "user_id": row[1],
        "buyer": {"first_name": row[2], "last_name": row[3], "rating": float(row[4]) if row[4] else None},
        "url": row[5], "title": row[6],
        "price": float(row[7]) if row[7] else None,
        "image_url": row[8], "description": row[9],
        "size": row[10], "color": row[11],
        "quantity": row[12],
        "commission": float(row[13]) if row[13] else None,
        "status": row[14], "created_at": str(row[15])
    }