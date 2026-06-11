# -*- coding: utf-8 -*-
from src.config.database import get_connection

def create_shopper(user_id, city, country="France", available_from=None,
                   available_until=None, delivery_zones=None, description=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO LCD_SHOPPERS (user_id, city, country, available_from,
                                  available_until, delivery_zones, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, city, country, available_from, available_until, delivery_zones, description))
    conn.commit()
    cursor.close()
    conn.close()

def get_shoppers(city=None, country=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.id, s.user_id, u.first_name, u.last_name, u.rating,
               s.city, s.country, s.available_from, s.available_until,
               s.delivery_zones, s.description, s.status, s.created_at
        FROM LCD_SHOPPERS s
        JOIN LCD_USERS u ON s.user_id = u.id
        WHERE s.status = 'ACTIVE'
    """
    params = []
    if city:
        query += " AND UPPER(s.city) = UPPER(%s)"
        params.append(city)
    if country:
        query += " AND UPPER(s.country) = UPPER(%s)"
        params.append(country)
    query += " ORDER BY s.created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_shopper(row) for row in rows]

def get_mine(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.user_id, u.first_name, u.last_name, u.rating,
               s.city, s.country, s.available_from, s.available_until,
               s.delivery_zones, s.description, s.status, s.created_at
        FROM LCD_SHOPPERS s
        JOIN LCD_USERS u ON s.user_id = u.id
        WHERE s.user_id = %s
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_shopper(row) for row in rows]

def delete_shopper(shopper_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM LCD_SHOPPERS WHERE id = %s AND user_id = %s", (shopper_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def _format_shopper(row):
    return {
        "id": row[0], "user_id": row[1],
        "shopper": {"first_name": row[2], "last_name": row[3], "rating": float(row[4]) if row[4] else None},
        "city": row[5], "country": row[6],
        "available_from": str(row[7]) if row[7] else None,
        "available_until": str(row[8]) if row[8] else None,
        "delivery_zones": row[9], "description": row[10],
        "status": row[11], "created_at": str(row[12])
    }