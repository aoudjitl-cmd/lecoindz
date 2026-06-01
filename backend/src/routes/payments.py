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
    """Sauvegarde le paiement dans la base de données."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_PAYMENTS (booking_id, amount, commission, carrier_amount, status, payment_ref)
        VALUES (:booking_id, :amount, :commission, :carrier_amount, 'HELD', :payment_ref)
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
    """Met à jour le statut d'un paiement."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_PAYMENTS
        SET status = :status
        WHERE payment_ref = :payment_ref
    """, {"status": status, "payment_ref": payment_intent_id})
    conn.commit()
    cursor.close()
    conn.close()

def get_payment_by_booking(booking_id):
    """Récupère le paiement d'une réservation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, booking_id, amount, commission, carrier_amount, status, payment_ref
        FROM CG_PAYMENTS
        WHERE booking_id = :booking_id
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
    """Crée un PaymentIntent Stripe pour une réservation."""
    booking = get_booking_by_id(data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation introuvable")

    # Seul l'expéditeur peut payer
    if booking["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul l'expéditeur peut effectuer le paiement")

    # Vérifier que la réservation est acceptée
    if booking["status"] != "ACCEPTED":
        raise HTTPException(status_code=400, detail="La réservation doit être acceptée avant le paiement")

    # Vérifier qu'un paiement n'existe pas déjà
    existing = get_payment_by_booking(data.booking_id)
    if existing and existing["status"] in ["HELD", "RELEASED"]:
        raise HTTPException(status_code=400, detail="Un paiement existe déjà pour cette réservation")

    # Calcul des montants
    amount = float(booking["agreed_price"])
    commission = round(amount * 0.10, 2)       # 10% pour RayahDZ
    carrier_amount = round(amount - commission, 2)  # 90% pour le voyageur

    try:
        # Créer le PaymentIntent Stripe (montant en centimes)
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

        # Sauvegarder en base
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
    """Récupère le statut du paiement d'une réservation."""
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation introuvable")
    if booking["sender_id"] != current_user["user_id"] and booking["carrier_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Accès refusé")

    payment = get_payment_by_booking(booking_id)
    if not payment:
        return {"status": "NOT_PAID", "message": "Aucun paiement trouvé"}
    return payment