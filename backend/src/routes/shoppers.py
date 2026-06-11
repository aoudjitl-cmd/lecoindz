# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.shopper import create_shopper, get_shoppers, get_mine, delete_shopper
from src.middleware.auth import get_current_user

router = APIRouter()

class ShopperRequest(BaseModel):
    city: str
    country: Optional[str] = "France"
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    delivery_zones: Optional[str] = None
    description: Optional[str] = None

@router.post("/", status_code=201)
def add_shopper(data: ShopperRequest, current_user=Depends(get_current_user)):
    create_shopper(
        user_id=current_user["user_id"],
        city=data.city,
        country=data.country,
        available_from=data.available_from,
        available_until=data.available_until,
        delivery_zones=data.delivery_zones,
        description=data.description
    )
    return {"message": "Disponibilite publiee avec succes"}

@router.get("/")
def search_shoppers(city: Optional[str] = None, country: Optional[str] = None):
    shoppers = get_shoppers(city=city, country=country)
    return {"total": len(shoppers), "shoppers": shoppers}

@router.get("/mes-disponibilites")
def mes_disponibilites(current_user=Depends(get_current_user)):
    shoppers = get_mine(current_user["user_id"])
    return {"shoppers": shoppers}

@router.delete("/{shopper_id}")
def supprimer_disponibilite(shopper_id: int, current_user=Depends(get_current_user)):
    delete_shopper(shopper_id, current_user["user_id"])
    return {"message": "Disponibilite supprimee"}