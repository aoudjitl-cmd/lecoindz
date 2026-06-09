# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import stripe
from src.config.settings import settings
from src.middleware.auth import get_current_user
from src.models.booking import get_booking_by_id
from src.config.database import get_connection

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

class PaymentRequest(BaseModel):
    booking_id: int

def save_payment(booking_id, amount, commission, carrier_amount, payment_intent_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_PAYMENTS (booking_id, amount, commission, carrier_amount, status, payment_ref)
        VALUES (%(booking_id)s, %(amount)s, %(commission)s, %(carrier_amount)s, 'HELD', %(payment_ref)s)
    """, {
        "booking_id": booking_id,
        "amount": amount,
        "commission": commission,
        "carrier_amount": carrier_amount,
        "payment_ref": payment_intent_id
    })
    conn.commit()
    cursor.close()
    conn.close()

def update_payment_status(payment_intent_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_PAYMENTS
        SET status = %(status)s
        WHERE payment_ref = %(payment_ref)s
    """, {"status": status, "payment_ref": payment_intent_id})
    conn.commit()
    cursor.close()
    conn.close()

def get_payment_by_booking(booking_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, booking_id, amount, commission, carrier_amount, status, payment_ref
        FROM CG_PAYMENTS
        WHERE booking_id = %(booking_id)s
    """, {"booking_id": booking_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "id": row[0], "booking_id": row[1], "amount": row[2],
            "commission": row[3], "carrier_amount": row[4],
            "status": row[5], "payment_ref": row[6]
        }
    return None

@router.post("/create-payment-intent")
def create_payment_intent(data: PaymentRequest, current_user=Depends(get_current_user)):
    booking = get_booking_by_id(data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if booking["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul l'expediteur peut effectuer le paiement")
    if booking["status"] != "ACCEPTED":
        raise HTTPException(status_code=400, detail="La reservation doit etre acceptee avant le paiement")

    existing = get_payment_by_booking(data.booking_id)
    if existing and existing["status"] in ["HELD", "RELEASED"]:
        raise HTTPException(status_code=400, detail="Un paiement existe deja pour cette reservation")

    amount = float(booking["agreed_price"])
    commission = round(amount * 0.10, 2)
    carrier_amount = round(amount - commission, 2)

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency="eur",
            metadata={
                "booking_id": data.booking_id,
                "sender_id": current_user["user_id"],
                "carrier_id": booking["carrier_id"]
            },
            capture_method="automatic"
        )
        save_payment(data.booking_id, amount, commission, carrier_amount, intent.id)
        return {
            "client_secret": intent.client_secret,
            "amount": amount,
            "commission": commission,
            "carrier_amount": carrier_amount,
            "public_key": settings.STRIPE_PUBLIC_KEY
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{booking_id}")
def payment_status(booking_id: int, current_user=Depends(get_current_user)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if booking["sender_id"] != current_user["user_id"] and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acces refuse")

    payment = get_payment_by_booking(booking_id)
    if not payment:
        return {"status": "NOT_PAID", "message": "Aucun paiement trouve"}
    return payment