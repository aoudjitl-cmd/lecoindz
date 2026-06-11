# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from src.models.product import create_product, get_products, get_product_by_id
from src.middleware.auth import get_current_user
import httpx
from bs4 import BeautifulSoup

router = APIRouter()

class ProductRequest(BaseModel):
    url: str
    size: Optional[str] = None
    color: Optional[str] = None
    quantity: Optional[int] = 1
    commission: Optional[float] = None

async def scrape_product(url: str) -> dict:
    """Recupere les infos du produit depuis l'URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            # Open Graph tags (standard)
            title = (
                getattr(soup.find("meta", property="og:title"), "get", lambda k: None)("content") or
                getattr(soup.find("title"), "text", None) or
                "Produit"
            )
            image = getattr(soup.find("meta", property="og:image"), "get", lambda k: None)("content")
            description = getattr(soup.find("meta", property="og:description"), "get", lambda k: None)("content")

            # Prix
            price = None
            price_meta = (
                soup.find("meta", property="product:price:amount") or
                soup.find("meta", {"name": "price"}) or
                soup.find("meta", property="og:price:amount")
            )
            if price_meta:
                try:
                    price = float(price_meta.get("content", "").replace(",", ".").replace(" ", ""))
                except:
                    pass

            return {
                "title": title[:500] if title else None,
                "image_url": image,
                "description": description[:500] if description else None,
                "price": price
            }
    except Exception as e:
        return {"title": None, "image_url": None, "description": None, "price": None}

@router.post("/", status_code=201)
async def add_product(data: ProductRequest, current_user=Depends(get_current_user)):
    # Scraper les infos du produit
    product_info = await scrape_product(data.url)

    create_product(
        user_id=current_user["user_id"],
        url=data.url,
        title=product_info["title"],
        price=product_info["price"],
        image_url=product_info["image_url"],
        description=product_info["description"],
        size=data.size,
        color=data.color,
        quantity=data.quantity,
        commission=data.commission
    )
    return {
        "message": "Annonce publiee avec succes",
        "product_info": product_info
    }

@router.get("/")
def search_products(max_commission: Optional[float] = None):
    products = get_products(max_price=max_commission)
    return {"total": len(products), "products": products}

@router.get("/{product_id}")
def get_product(product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return product

@router.post("/scrape")
async def scrape_url(data: dict):
    """Scrape une URL et retourne les infos du produit — pour l'apercu avant publication."""
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL requise")
    info = await scrape_product(url)
    return info