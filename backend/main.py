# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth, trips, parcels, bookings, messages, payments, subscriptions, direct_messages, reviews

app = FastAPI(
    title="RayahDZ API",
    description="API de la plateforme de transport de colis entre particuliers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(trips.router, prefix="/trips", tags=["Trajets"])
app.include_router(parcels.router, prefix="/parcels", tags=["Colis"])
app.include_router(bookings.router, prefix="/bookings", tags=["Reservations"])
app.include_router(messages.router, prefix="/messages", tags=["Messagerie"])
app.include_router(payments.router, prefix="/payments", tags=["Paiements"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Abonnements"])
app.include_router(direct_messages.router, prefix="/direct", tags=["Messages directs"])
app.include_router(reviews.router, prefix="/reviews", tags=["Avis"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API RayahDZ"}

@app.get("/admin/migrate-cgu")
def migrate_cgu():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    results = []
    for sql in [
        "ALTER TABLE CG_USERS ADD COLUMN cgu_accepted_at DATETIME NULL",
        "ALTER TABLE CG_USERS ADD COLUMN cgu_version VARCHAR(10) NULL",
    ]:
        try:
            cursor.execute(sql)
            conn.commit()
            results.append({"sql": sql, "status": "ok"})
        except Exception as e:
            results.append({"sql": sql, "status": "skip", "reason": str(e)})
    cursor.close()
    conn.close()
    return {"results": results}