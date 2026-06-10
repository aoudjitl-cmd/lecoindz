# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth, trips, parcels, bookings, messages, payments, subscriptions, direct_messages, reviews, admin

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
app.include_router(admin.router, prefix="/admin-api", tags=["Administration"])

@app.get("/admin/free-unverified-emails2")
def free_unverified_emails2():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE CG_USERS SET email = CONCAT(email, '_old2') WHERE is_verified = 0")
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return {"updated": affected}
	
	
	
@app.get("/admin/verify-existing-users")
def verify_existing_users():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE CG_USERS SET is_verified = 1 WHERE is_verified = 0")
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return {"updated": affected}
	
	
	
@app.get("/admin/show-tables")
def show_tables():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"tables": [r[0] for r in rows]}

@app.get("/admin/migrate-is-admin")
def migrate_is_admin():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE CG_USERS ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0")
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "skip", "reason": str(e)}
    finally:
        cursor.close()
        conn.close()
		
		
@app.get("/admin/set-admin")
def set_admin():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE CG_USERS SET is_admin = 1 WHERE email = 'aoudjitl@gmail.com'")
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return {"updated": affected}