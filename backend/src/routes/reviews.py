# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.review import create_review, get_reviews_for_user, get_review_by_booking
from src.models.booking import get_booking_by_id
from src.middleware.auth import get_current_user

router = APIRouter()

class ReviewRequest(BaseModel):
    booking_id: int
    rating: int        # 1 a 5
    comment: Optional[str] = None

@router.post("/", status_code=201)
def add_review(data: ReviewRequest, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    # Verifier que la reservation existe et est DELIVERED
    booking = get_booking_by_id(data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if booking["status"] != "DELIVERED":
        raise HTTPException(status_code=400, detail="La reservation doit etre livree pour laisser un avis")

    # Verifier que l'utilisateur fait partie de la reservation
    if user_id != booking["sender_id"] and user_id != booking["carrier_id"]:
        raise HTTPException(status_code=403, detail="Vous ne faites pas partie de cette reservation")

    # Verifier que l'avis n'existe pas deja
    if get_review_by_booking(user_id, data.booking_id):
        raise HTTPException(status_code=400, detail="Vous avez deja laisse un avis pour cette reservation")

    # Determiner qui on note : l'expediteur note le voyageur et vice versa
    if user_id == booking["sender_id"]:
        reviewed_id = booking["carrier_id"]
    else:
        reviewed_id = booking["sender_id"]

    # Valider la note
    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="La note doit etre entre 1 et 5")

    create_review(
        reviewer_id=user_id,
        reviewed_id=reviewed_id,
        booking_id=data.booking_id,
        rating=data.rating,
        comment=data.comment
    )
    return {"message": "Avis publie avec succes"}

@router.get("/user/{user_id}")
def get_user_reviews(user_id: int):
    reviews = get_reviews_for_user(user_id)
    total = len(reviews)
    avg = round(sum(r["rating"] for r in reviews) / total, 1) if total > 0 else None
    return {"total": total, "average": avg, "reviews": reviews}

@router.get("/booking/{booking_id}/can-review")
def can_review(booking_id: int, current_user=Depends(get_current_user)):
    """Verifie si l'utilisateur peut encore laisser un avis."""
    user_id = current_user["user_id"]
    booking = get_booking_by_id(booking_id)
    if not booking or booking["status"] != "DELIVERED":
        return {"can_review": False}
    if user_id != booking["sender_id"] and user_id != booking["carrier_id"]:
        return {"can_review": False}
    already_reviewed = get_review_by_booking(user_id, booking_id)
    return {"can_review": not already_reviewed}