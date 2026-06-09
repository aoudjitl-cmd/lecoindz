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

@app.get("/admin/fix-reviews-table")
def fix_reviews_table():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    results = []
    migrations = [
        "ALTER TABLE CG_REVIEWS ADD COLUMN comment TEXT NULL",
        "ALTER TABLE CG_REVIEWS ADD COLUMN reviewer_id INT NOT NULL",
        "ALTER TABLE CG_REVIEWS ADD COLUMN reviewed_id INT NOT NULL",
        "ALTER TABLE CG_REVIEWS ADD COLUMN booking_id INT NOT NULL",
        "ALTER TABLE CG_REVIEWS ADD COLUMN rating TINYINT NOT NULL",
        "ALTER TABLE CG_REVIEWS ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ]
    for sql in migrations:
        try:
            cursor.execute(sql)
            conn.commit()
            results.append({"sql": sql, "status": "ok"})
        except Exception as e:
            results.append({"sql": sql, "status": "skip", "reason": str(e)})
    cursor.close()
    conn.close()
    return {"results": results}