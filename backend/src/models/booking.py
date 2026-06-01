from src.config.database import get_connection
import random, string

def generate_code(length=6):
    """Génère un code aléatoire pour la remise/livraison."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_booking(parcel_id, trip_id, sender_id, carrier_id, agreed_price):
    """Créer une réservation entre un expéditeur et un voyageur."""
    conn = get_connection()
    cursor = conn.cursor()
    pickup_code = generate_code()
    delivery_code = generate_code()
    cursor.execute("""
        INSERT INTO CG_BOOKINGS (parcel_id, trip_id, sender_id, carrier_id,
                                 agreed_price, pickup_code, delivery_code)
        VALUES (:parcel_id, :trip_id, :sender_id, :carrier_id,
                :agreed_price, :pickup_code, :delivery_code)
    """, {
        "parcel_id": parcel_id, "trip_id": trip_id,
        "sender_id": sender_id, "carrier_id": carrier_id,
        "agreed_price": agreed_price,
        "pickup_code": pickup_code, "delivery_code": delivery_code
    })
    conn.commit()
    cursor.close()
    conn.close()

def get_booking_by_id(booking_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.parcel_id, b.trip_id, b.sender_id, b.carrier_id,
               b.agreed_price, b.status, b.pickup_code, b.delivery_code,
               b.created_at,
               u1.first_name, u1.last_name,
               u2.first_name, u2.last_name
        FROM CG_BOOKINGS b
        JOIN CG_USERS u1 ON b.sender_id = u1.id
        JOIN CG_USERS u2 ON b.carrier_id = u2.id
        WHERE b.id = :booking_id
    """, {"booking_id": booking_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return _format_booking(row) if row else None

def get_user_bookings(user_id):
    """Récupère toutes les réservations d'un utilisateur (en tant qu'expéditeur ou voyageur)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, b.parcel_id, b.trip_id, b.sender_id, b.carrier_id,
               b.agreed_price, b.status, b.pickup_code, b.delivery_code,
               b.created_at,
               u1.first_name, u1.last_name,
               u2.first_name, u2.last_name
        FROM CG_BOOKINGS b
        JOIN CG_USERS u1 ON b.sender_id = u1.id
        JOIN CG_USERS u2 ON b.carrier_id = u2.id
        WHERE b.sender_id = :user_id OR b.carrier_id = :user_id
        ORDER BY b.created_at DESC
    """, {"user_id": user_id})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_format_booking(row) for row in rows]

def update_booking_status(booking_id, status):
    """Met à jour le statut d'une réservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_BOOKINGS
        SET status = :status, updated_at = CURRENT_TIMESTAMP
        WHERE id = :booking_id
    """, {"status": status, "booking_id": booking_id})
    conn.commit()
    cursor.close()
    conn.close()

def update_parcel_status(parcel_id, status):
    """Met à jour le statut d'un colis."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_PARCELS SET status = :status WHERE id = :parcel_id
    """, {"status": status, "parcel_id": parcel_id})
    conn.commit()
    cursor.close()
    conn.close()

def _format_booking(row):
    return {
        "id": row[0], "parcel_id": row[1], "trip_id": row[2],
        "sender_id": row[3], "carrier_id": row[4],
        "agreed_price": row[5], "status": row[6],
        "pickup_code": row[7], "delivery_code": row[8],
        "created_at": str(row[9]),
        "sender": {"first_name": row[10], "last_name": row[11]},
        "carrier": {"first_name": row[12], "last_name": row[13]}
    }