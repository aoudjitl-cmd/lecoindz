# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
import stripe
from src.config.settings import settings
from src.middleware.auth import get_current_user
from src.config.database import get_connection

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, first_name, last_name, subscription_status, subscription_id, trial_end
        FROM CG_USERS WHERE id = %(user_id)s
    """, {"user_id": user_id})
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "id": row[0], "email": row[1],
            "first_name": row[2], "last_name": row[3],
            "subscription_status": row[4],
            "subscription_id": row[5],
            "trial_end": str(row[6]) if row[6] else None
        }
    return None

def update_subscription(user_id, subscription_status, subscription_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_USERS
        SET subscription_status = %(status)s,
            subscription_id = %(sub_id)s
        WHERE id = %(user_id)s
    """, {
        "status": subscription_status,
        "sub_id": subscription_id,
        "user_id": user_id
    })
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/create-checkout")
def create_checkout(current_user=Depends(get_current_user)):
    user = get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user["subscription_status"] == "ACTIVE":
        raise HTTPException(status_code=400, detail="Vous avez deja un abonnement actif")

    try:
        customers = stripe.Customer.list(email=user["email"], limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=user["email"],
                name=f"{user['first_name']} {user['last_name']}"
            )

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=["card"],
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1
            }],
            mode="subscription",
            subscription_data={
                "trial_period_days": 0
            },
            success_url="https://www.rayahdz.com/subscription-success.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://www.rayahdz.com/subscription.html",
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def subscription_status(current_user=Depends(get_current_user)):
    user = get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {
        "subscription_status": user["subscription_status"],
        "trial_end": user["trial_end"]
    }

@router.post("/verify/{session_id}")
def verify_subscription(session_id: str, current_user=Depends(get_current_user)):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.status == "complete":
            update_subscription(
                current_user["user_id"],
                "ACTIVE",
                session.subscription
            )
            return {"message": "Abonnement active avec succes"}
        raise HTTPException(status_code=400, detail="Session non complete")
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/cancel")
def cancel_subscription(current_user=Depends(get_current_user)):
    user = get_user_by_id(current_user["user_id"])
    if not user or not user["subscription_id"]:
        raise HTTPException(status_code=400, detail="Aucun abonnement actif")

    try:
        stripe.Subscription.modify(
            user["subscription_id"],
            cancel_at_period_end=True
        )
        update_subscription(current_user["user_id"], "CANCELLED")
        return {"message": "Abonnement annule — acces jusqu'a la fin de la periode"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))