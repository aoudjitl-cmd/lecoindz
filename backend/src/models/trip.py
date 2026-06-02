from src.config.database import get_connection


def create_trip(user_id, origin_city, origin_country, dest_city, dest_country,
                departure_date, arrival_date, max_weight, max_size, price_per_kg, description=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_TRIPS (user_id, origin_city, origin_country, dest_city, dest_country,
                              departure_date, arrival_date, max_weight, max_size, price_per_kg, description)
        VALUES (%(user_id)s, %(origin_city)s, %(origin_country)s, %(dest_city)s, %(dest_country)s,
                %(departure_date)s, %(arrival_date)s,
                %(max_weight)s, %(max_size)s, %(price_per_kg)s, %(description)s)
    """, {
        "user_id": user_id, "origin_city": origin_city, "origin_country": origin_country,
        "dest_city": dest_city, "dest_country": dest_country,
        "departure_date": departure_date, "arrival_date": arrival_date,
        "max_weight": max_weight, "max_size": max_size,
        "price_per_kg": price_per_kg, "description": description
    })
    conn.commit()
    cursor.close()
    conn.close()


def get_trips(dest_city=None, dest_country=None, min_weight=None):
    """Recherche des trajets selon destination et capacité."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT t.id, t.user_id, u.first_name, u.last_name, u.rating,
               t.origin_city, t.origin_country, t.dest_city, t.dest_country,
               t.departure_date, t.arrival_date, t.max_weight, t.max_size,
               t.price_per_kg, t.description, t.status
        FROM CG_TRIPS t
        JOIN CG_USER u ON t.user_id = u.id
        WHERE t.status = 'ACTIVE'
    """
    params = {}
    if dest_city:
        query += " AND UPPER(t.dest_city) = UPPER(%(dest_city)s)"
        params["dest_city"] = dest_city
    if dest_country:
        query += " AND UPPER(t.dest_country) = UPPER(%(dest_country)s)"
        params["dest_country"] = dest_country
    if min_weight:
        query += " AND t.max_weight >= %(min_weight)s"
        params["min_weight"] = min_weight
    query += " ORDER BY t.departure_date ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_trip(row) for row in rows]


def get_trip_by_id(trip_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.user_id, u.first_name, u.last_name, u.rating,
               t.origin_city, t.origin_country, t.dest_city, t.dest_country,
               t.departure_date, t.arrival_date, t.max_weight, t.max_size,
               t.price_per_kg, t.description, t.status
        FROM CG_TRIPS t
        JOIN CG_USER u ON t.user_id = u.id
        WHERE t.id = %(trip_id)s
    """, {"trip_id": trip_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _format_trip(row) if row else None


def _format_trip(row):
    return {
        "id": row[0], "user_id": row[1],
        "carrier": {"first_name": row[2], "last_name": row[3], "rating": row[4]},
        "origin_city": row[5], "origin_country": row[6],
        "dest_city": row[7], "dest_country": row[8],
        "departure_date": str(row[9]), "arrival_date": str(row[10]),
        "max_weight": row[11], "max_size": row[12],
        "price_per_kg": row[13], "description": row[14], "status": row[15]
    }