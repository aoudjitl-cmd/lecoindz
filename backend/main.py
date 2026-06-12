# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import auth, subscriptions, direct_messages, reviews, admin
from src.routes import products, shoppers, orders

app = FastAPI(
    title="LeCoinDZ API",
    description="API de la plateforme de personal shopping France-Algerie",
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
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Abonnements"])
app.include_router(direct_messages.router, prefix="/direct", tags=["Messages directs"])
app.include_router(reviews.router, prefix="/reviews", tags=["Avis"])
app.include_router(admin.router, prefix="/admin-api", tags=["Administration"])
app.include_router(products.router, prefix="/products", tags=["Produits"])
app.include_router(shoppers.router, prefix="/shoppers", tags=["Shoppers"])
app.include_router(orders.router, prefix="/orders", tags=["Commandes"])

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API LeCoinDZ"}

@app.get("/admin/create-tables")
def create_tables():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    results = []

    tables = [
        # Users
        """CREATE TABLE IF NOT EXISTS LCD_USERS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            avatar_url VARCHAR(500),
            is_verified TINYINT(1) NOT NULL DEFAULT 0,
            is_admin TINYINT(1) NOT NULL DEFAULT 0,
            rating DECIMAL(3,2) NOT NULL DEFAULT 0,
            nb_ratings INT NOT NULL DEFAULT 0,
            subscription_status VARCHAR(20) DEFAULT 'TRIAL',
            subscription_id VARCHAR(255),
            trial_end DATE,
            verification_token VARCHAR(100),
            cgu_accepted_at DATETIME,
            cgu_version VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",

        # Annonces produits
        """CREATE TABLE IF NOT EXISTS LCD_PRODUCTS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            url VARCHAR(1000) NOT NULL,
            title VARCHAR(500),
            price DECIMAL(10,2),
            image_url VARCHAR(1000),
            description TEXT,
            size VARCHAR(50),
            color VARCHAR(100),
            quantity INT DEFAULT 1,
            commission DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES LCD_USERS(id)
        )""",

        # Disponibilites shoppers
        """CREATE TABLE IF NOT EXISTS LCD_SHOPPERS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            city VARCHAR(100) NOT NULL,
            country VARCHAR(100) DEFAULT 'France',
            available_from DATE,
            available_until DATE,
            delivery_zones TEXT,
            description TEXT,
            status VARCHAR(20) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES LCD_USERS(id)
        )""",

        # Commandes
        """CREATE TABLE IF NOT EXISTS LCD_ORDERS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            shopper_id INT NOT NULL,
            buyer_id INT NOT NULL,
            agreed_commission DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'PENDING',
            pickup_code VARCHAR(10),
            delivery_code VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES LCD_PRODUCTS(id),
            FOREIGN KEY (shopper_id) REFERENCES LCD_USERS(id),
            FOREIGN KEY (buyer_id) REFERENCES LCD_USERS(id)
        )""",

        # Messages par commande
        """CREATE TABLE IF NOT EXISTS LCD_MESSAGES (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            sender_id INT NOT NULL,
            content TEXT NOT NULL,
            is_read TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES LCD_ORDERS(id),
            FOREIGN KEY (sender_id) REFERENCES LCD_USERS(id)
        )""",

        # Conversations directes
        """CREATE TABLE IF NOT EXISTS LCD_CONVERSATIONS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user1_id INT NOT NULL,
            user2_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES LCD_USERS(id),
            FOREIGN KEY (user2_id) REFERENCES LCD_USERS(id)
        )""",

        # Messages directs
        """CREATE TABLE IF NOT EXISTS LCD_DIRECT_MESSAGES (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conversation_id INT NOT NULL,
            sender_id INT NOT NULL,
            content TEXT NOT NULL,
            is_read TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES LCD_CONVERSATIONS(id),
            FOREIGN KEY (sender_id) REFERENCES LCD_USERS(id)
        )""",

        # Avis
        """CREATE TABLE IF NOT EXISTS LCD_REVIEWS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reviewer_id INT NOT NULL,
            reviewed_id INT NOT NULL,
            order_id INT NOT NULL,
            rating TINYINT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reviewer_id) REFERENCES LCD_USERS(id),
            FOREIGN KEY (reviewed_id) REFERENCES LCD_USERS(id),
            FOREIGN KEY (order_id) REFERENCES LCD_ORDERS(id),
            UNIQUE KEY unique_review (reviewer_id, order_id)
        )""",

        # Abonnements/paiements
        """CREATE TABLE IF NOT EXISTS LCD_PAYMENTS (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10,2),
            status VARCHAR(20),
            payment_ref VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES LCD_USERS(id)
        )"""
    ]

    for sql in tables:
        table_name = sql.split("LCD_")[1].split(" ")[0] if "LCD_" in sql else "unknown"
        try:
            cursor.execute(sql)
            conn.commit()
            results.append({"table": "LCD_" + table_name, "status": "ok"})
        except Exception as e:
            results.append({"table": "LCD_" + table_name, "status": "error", "reason": str(e)})

    cursor.close()
    conn.close()
    return {"results": results}
	
	
@app.get("/admin/set-admin")
def set_admin():
    from src.config.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE LCD_USERS SET is_admin = 1 WHERE email = 'rayah.plateforme@gmail.com'")
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return {"updated": affected}