from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.models.booking import (create_booking, get_booking_by_id,
                                 get_user_bookings, update_booking_status,
                                 update_parcel_status)
from src.models.parcel import get_parcel_by_id
from src.models.trip import get_trip_by_id
from src.middleware.auth import get_current_user
from src.config.database import get_connection

router = APIRouter()

class BookingRequest(BaseModel):
    parcel_id: int
    trip_id: int
    agreed_price: float

class StatusRequest(BaseModel):
    status: str

@router.post("/", status_code=201)
def book(data: BookingRequest, current_user=Depends(get_current_user)):
    """Création d'une réservation."""
    parcel = get_parcel_by_id(data.parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Colis introuvable")
    if parcel["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Ce colis n'est plus disponible")

    trip = get_trip_by_id(data.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trajet introuvable")
    if trip["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail="Ce trajet n'est plus disponible")

    # Le voyageur ne peut pas transporter son propre colis
    if parcel["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas transporter votre propre colis")

    # Le trajet doit appartenir au voyageur connecté
    if trip["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Ce trajet ne vous appartient pas")

    create_booking(
        parcel_id=data.parcel_id,
        trip_id=data.trip_id,
        sender_id=parcel["user_id"],
        carrier_id=current_user["user_id"],
        agreed_price=data.agreed_price
    )

    update_parcel_status(data.parcel_id, "MATCHED")

    return {"message": "Demande de transport envoyée avec succès"}

@router.get("/mes-reservations")
def mes_reservations(current_user=Depends(get_current_user)):
    bookings = get_user_bookings(current_user["user_id"])
    return {"total": len(bookings), "bookings": bookings}

@router.get("/{booking_id}")
def get_booking(booking_id: int, current_user=Depends(get_current_user)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if booking["sender_id"] != current_user["user_id"] and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acces refuse")
    return booking

@router.patch("/{booking_id}/statut")
def changer_statut(booking_id: int, data: StatusRequest, current_user=Depends(get_current_user)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")

    statuts_valides = ["ACCEPTED", "IN_TRANSIT", "DELIVERED", "CANCELLED"]
    if data.status not in statuts_valides:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptees : {statuts_valides}")

    # L'expediteur accepte ou refuse toujours
    if data.status in ["ACCEPTED", "CANCELLED"] and booking["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul l'expediteur peut accepter ou refuser")

    # Le voyageur confirme la prise en charge
    if data.status == "IN_TRANSIT" and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le voyageur peut confirmer la prise en charge")

    # L'expediteur confirme la livraison
    if data.status == "DELIVERED" and booking["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul l'expediteur peut confirmer la livraison")

    update_booking_status(booking_id, data.status)

    if data.status == "IN_TRANSIT":
        update_parcel_status(booking["parcel_id"], "IN_TRANSIT")
    elif data.status == "DELIVERED":
        update_parcel_status(booking["parcel_id"], "DELIVERED")
    elif data.status == "CANCELLED":
        update_parcel_status(booking["parcel_id"], "PENDING")

    return {"message": f"Statut mis a jour : {data.status}"}

@router.patch("/{booking_id}/paid")
def marquer_paye(booking_id: int, current_user=Depends(get_current_user)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if booking["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acces refuse")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_BOOKINGS SET is_paid = 1 WHERE id = :booking_id
    """, {"booking_id": booking_id})
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Reservation marquee comme payee"}