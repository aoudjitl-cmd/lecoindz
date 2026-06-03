from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.trip import create_trip, get_trips, get_trip_by_id, _format_trip
from src.middleware.auth import get_current_user
from src.config.database import get_connection

router = APIRouter()

class TripRequest(BaseModel):
    origin_city: str
    origin_country: str
    dest_city: str
    dest_country: str
    departure_date: str
    arrival_date: str
    max_weight: float
    max_size: str
    price_per_kg: float
    description: Optional[str] = None

@router.post("/", status_code=201)
def add_trip(data: TripRequest, current_user=Depends(get_current_user)):
    create_trip(
        user_id=current_user["user_id"],
        origin_city=data.origin_city, origin_country=data.origin_country,
        dest_city=data.dest_city, dest_country=data.dest_country,
        departure_date=data.departure_date, arrival_date=data.arrival_date,
        max_weight=data.max_weight, max_size=data.max_size,
        price_per_kg=data.price_per_kg, description=data.description
    )
    return {"message": "Trajet publie avec succes"}

@router.get("/mes-trajets")
def mes_trajets(current_user=Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.user_id, u.first_name, u.last_name, u.rating,
               t.origin_city, t.origin_country, t.dest_city, t.dest_country,
               t.departure_date, t.arrival_date, t.max_weight, t.max_size,
               t.price_per_kg, t.description, t.status
        FROM CG_TRIPS t
        JOIN CG_USERS u ON t.user_id = u.id
        WHERE t.user_id = %(user_id)s
        ORDER BY t.departure_date DESC
    """, {"user_id": current_user["user_id"]})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"total": len(rows), "trips": [_format_trip(row) for row in rows]}

@router.get("/")
def search_trips(dest_city: Optional[str] = None, dest_country: Optional[str] = None,
                 min_weight: Optional[float] = None):
    trips = get_trips(dest_city, dest_country, min_weight)
    return {"total": len(trips), "trips": trips}

@router.get("/{trip_id}")
def get_trip(trip_id: int):
    trip = get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trajet introuvable")
    return trip

@router.delete("/{trip_id}")
def supprimer_trip(trip_id: int, current_user=Depends(get_current_user)):
    """Supprimer un trajet."""
    trip = get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trajet introuvable")
    if trip["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acces refuse")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Verifier s'il y a des reservations actives
        cursor.execute("""
            SELECT COUNT(*) FROM CG_BOOKINGS
            WHERE trip_id = %(trip_id)s
            AND status NOT IN ('CANCELLED', 'DELIVERED')
        """, {"trip_id": trip_id})
        count = cursor.fetchone()[0]

        if count > 0:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer un trajet avec des reservations en cours"
            )

        # Supprimer d'abord les reservations annulees/livrees
        cursor.execute("""
            DELETE FROM CG_BOOKINGS
            WHERE trip_id = %(trip_id)s
            AND status IN ('CANCELLED', 'DELIVERED')
        """, {"trip_id": trip_id})

        # Supprimer le trajet
        cursor.execute(
            "DELETE FROM CG_TRIPS WHERE id = %(trip_id)s",
            {"trip_id": trip_id}
        )
        conn.commit()

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

    return {"message": "Trajet supprime"}