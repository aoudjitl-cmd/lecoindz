from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth, trips, parcels, bookings, messages, payments, subscriptions, direct_messages

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

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API RayahDZ"}

@app.get("/admin/migrate-budget")
def migrate_budget():
    from src.models.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE CG_PARCELS ADD COLUMN budget DECIMAL(10,2) NULL")
        conn.commit()
        return {"status": "ok", "message": "Colonne budget ajoutée avec succès"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()