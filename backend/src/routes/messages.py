from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.models.message import send_message, get_messages, mark_as_read, count_unread
from src.models.booking import get_booking_by_id
from src.middleware.auth import get_current_user

router = APIRouter()

class MessageRequest(BaseModel):
    content: str

@router.post("/{booking_id}", status_code=201)
def envoyer_message(booking_id: int, data: MessageRequest, current_user=Depends(get_current_user)):
    """Envoyer un message dans une réservation."""
    # Vérifier que l'utilisateur est bien concerné par cette réservation
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation introuvable")
    if booking["sender_id"] != current_user["user_id"] and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    send_message(booking_id, current_user["user_id"], data.content)
    return {"message": "Message envoyé"}

@router.get("/{booking_id}")
def get_conversation(booking_id: int, current_user=Depends(get_current_user)):
    """Récupère tous les messages d'une réservation."""
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation introuvable")
    if booking["sender_id"] != current_user["user_id"] and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Marquer les messages comme lus
    mark_as_read(booking_id, current_user["user_id"])
    messages = get_messages(booking_id)
    return {"booking_id": booking_id, "messages": messages}

@router.get("/non-lus/count")
def messages_non_lus(current_user=Depends(get_current_user)):
    """Compte les messages non lus."""
    count = count_unread(current_user["user_id"])
    return {"unread": count}