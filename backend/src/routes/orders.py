# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.order import create_order, get_order_by_id, get_user_orders, update_order_status
from src.models.product import get_product_by_id
from src.middleware.auth import get_current_user

router = APIRouter()

class OrderRequest(BaseModel):
    product_id: int
    agreed_commission: float

class StatusRequest(BaseModel):
    status: str

@router.post("/", status_code=201)
def add_order(data: OrderRequest, current_user=Depends(get_current_user)):
    product = get_product_by_id(data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    if product["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Ce produit n'est plus disponible")
    if product["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas acheter votre propre annonce")

    create_order(
        product_id=data.product_id,
        shopper_id=current_user["user_id"],
        buyer_id=product["user_id"],
        agreed_commission=data.agreed_commission
    )
    return {"message": "Proposition envoyee avec succes"}

@router.get("/mes-commandes")
def mes_commandes(current_user=Depends(get_current_user)):
    orders = get_user_orders(current_user["user_id"])
    return {"orders": orders}

@router.get("/{order_id}")
def get_order(order_id: int, current_user=Depends(get_current_user)):
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order["buyer_id"] != current_user["user_id"] and order["shopper_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Acces refuse")
    return order

@router.patch("/{order_id}/statut")
def changer_statut(order_id: int, data: StatusRequest, current_user=Depends(get_current_user)):
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    allowed = {
        "ACCEPTED": order["buyer_id"] == current_user["user_id"] and order["status"] == "PENDING",
        "CANCELLED": order["buyer_id"] == current_user["user_id"] and order["status"] == "PENDING",
        "IN_PROGRESS": order["shopper_id"] == current_user["user_id"] and order["status"] == "ACCEPTED",
        "DELIVERED": order["buyer_id"] == current_user["user_id"] and order["status"] == "IN_PROGRESS",
    }

    if not allowed.get(data.status, False):
        raise HTTPException(status_code=400, detail="Action non autorisee")

    update_order_status(order_id, data.status)
    return {"message": "Statut mis a jour"}