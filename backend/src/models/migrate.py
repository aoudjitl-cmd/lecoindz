import mysql.connector

conn = mysql.connector.connect(
    host="zephyr.proxy.rlwy.net",
    port=20932,
    user="root",                    
    password="sxvbLJHBqwUlvlHTrgMqvIeDeXfkTZyQ",      
    database="railway"       
)

cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE CG_PARCELS ADD COLUMN budget DECIMAL(10,2) NULL")
    conn.commit()
    print("✅ Colonne budget ajoutée")
except Exception as e:
    print(f"❌ Erreur : {e}")
finally:
    cursor.close()
    conn.close()