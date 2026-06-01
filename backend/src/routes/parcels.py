from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.parcel import create_parcel, get_parcels, get_parcel_by_id
from src.middleware.auth import get_current_user

router = APIRouter()

class ParcelRequest(BaseModel):
    title: str
    description: Optional[str] = None
    origin_city: str
    origin_country: str
    dest_city: str
    dest_country: str
    weight: float
    taille: str          # SMALL / MEDIUM / LARGE
    deadline_date: Optional[str] = None
    is_fragile: Optional[int] = 0

@router.post("/", status_code=201)
def add_parcel(data: ParcelRequest, current_user=Depends(get_current_user)):
    create_parcel(
        user_id=current_user["user_id"],
        title=data.title, description=data.description,
        origin_city=data.origin_city, origin_country=data.origin_country,
        dest_city=data.dest_city, dest_country=data.dest_country,
        weight=data.weight, taille=data.taille,
        deadline_date=data.deadline_date, is_fragile=data.is_fragile
    )
    return {"message": "Annonce de colis publiée avec succès"}

@router.get("/")
def search_parcels(dest_city: Optional[str] = None, dest_country: Optional[str] = None):
    parcels = get_parcels(dest_city, dest_country)
    return {"total": len(parcels), "parcels": parcels}

@router.get("/{parcel_id}")
def get_parcel(parcel_id: int):
    parcel = get_parcel_by_id(parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Colis introuvable")
    return parcel