from src.config.database import get_connection

def create_parcel(user_id, title, description, origin_city, origin_country,
                  dest_city, dest_country, weight, taille, deadline_date=None, is_fragile=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_PARCELS (user_id, title, description, origin_city, origin_country,
                                dest_city, dest_country, weight, taille, deadline_date, is_fragile)
        VALUES (:user_id, :title, :description, :origin_city, :origin_country,
                :dest_city, :dest_country, :weight, :taille,
                TO_DATE(:deadline_date, 'YYYY-MM-DD'), :is_fragile)
    """, {
        "user_id": user_id, "title": title, "description": description,
        "origin_city": origin_city, "origin_country": origin_country,
        "dest_city": dest_city, "dest_country": dest_country,
        "weight": weight, "taille": taille,
        "deadline_date": deadline_date, "is_fragile": is_fragile
    })
    conn.commit()
    cursor.close()
    conn.close()

def get_parcels(dest_city=None, dest_country=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.id, p.user_id, u.first_name, u.last_name, u.rating,
               p.title, p.description, p.origin_city, p.origin_country,
               p.dest_city, p.dest_country, p.weight, p.taille,
               p.deadline_date, p.is_fragile, p.status, p.created_at
        FROM CG_PARCELS p
        JOIN CG_USERS u ON p.user_id = u.id
        WHERE p.status = 'PENDING'
    """
    params = {}
    if dest_city:
        query += " AND UPPER(p.dest_city) = UPPER(:dest_city)"
        params["dest_city"] = dest_city
    if dest_country:
        query += " AND UPPER(p.dest_country) = UPPER(:dest_country)"
        params["dest_country"] = dest_country
    query += " ORDER BY p.created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_parcel(row) for row in rows]

def get_parcel_by_id(parcel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.user_id, u.first_name, u.last_name, u.rating,
               p.title, p.description, p.origin_city, p.origin_country,
               p.dest_city, p.dest_country, p.weight, p.taille,
               p.deadline_date, p.is_fragile, p.status, p.created_at
        FROM CG_PARCELS p
        JOIN CG_USERS u ON p.user_id = u.id
        WHERE p.id = :parcel_id
    """, {"parcel_id": parcel_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _format_parcel(row) if row else None

def _format_parcel(row):
    return {
        "id": row[0], "user_id": row[1],
        "sender": {"first_name": row[2], "last_name": row[3], "rating": row[4]},
        "title": row[5], "description": row[6],
        "origin_city": row[7], "origin_country": row[8],
        "dest_city": row[9], "dest_country": row[10],
        "weight": row[11], "taille": row[12],
        "deadline_date": str(row[13]) if row[13] else None,
        "is_fragile": row[14], "status": row[15],
        "created_at": str(row[16])
    }