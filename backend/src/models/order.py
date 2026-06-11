# -*- coding: utf-8 -*-
import random, string
from src.config.database import get_connection

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_order(product_id, shopper_id, buyer_id, agreed_commission):
    conn = get_connection()
    cursor = conn.cursor()
    pickup_code = generate_code()
    delivery_code = generate_code()
    cursor.execute("""
        INSERT INTO LCD_ORDERS (product_id, shopper_id, buyer_id,
                                agreed_commission, pickup_code, delivery_code)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (product_id, shopper_id, buyer_id, agreed_commission, pickup_code, delivery_code))
    conn.commit()
    cursor.close()
    conn.close()

def get_order_by_id(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.product_id, o.shopper_id, o.buyer_id,
               o.agreed_commission, o.status, o.pickup_code, o.delivery_code, o.created_at,
               u1.first_name, u1.last_name,
               u2.first_name, u2.last_name
        FROM LCD_ORDERS o
        JOIN LCD_USERS u1 ON o.buyer_id = u1.id
        JOIN LCD_USERS u2 ON o.shopper_id = u2.id
        WHERE o.id = %s
    """, (order_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _format_order(row) if row else None

def get_user_orders(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.id, o.product_id, o.shopper_id, o.buyer_id,
               o.agreed_commission, o.status, o.pickup_code, o.delivery_code, o.created_at,
               u1.first_name, u1.last_name,
               u2.first_name, u2.last_name
        FROM LCD_ORDERS o
        JOIN LCD_USERS u1 ON o.buyer_id = u1.id
        JOIN LCD_USERS u2 ON o.shopper_id = u2.id
        WHERE o.buyer_id = %s OR o.shopper_id = %s
        ORDER BY o.created_at DESC
    """, (user_id, user_id))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_order(row) for row in rows]

def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE LCD_ORDERS SET status = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (status, order_id))
    conn.commit()
    cursor.close()
    conn.close()

def _format_order(row):
    return {
        "id": row[0], "product_id": row[1],
        "shopper_id": row[2], "buyer_id": row[3],
        "agreed_commission": float(row[4]) if row[4] else None,
        "status": row[5], "pickup_code": row[6], "delivery_code": row[7],
        "created_at": str(row[8]),
        "buyer": {"first_name": row[9], "last_name": row[10]},
        "shopper": {"first_name": row[11], "last_name": row[12]}
    }