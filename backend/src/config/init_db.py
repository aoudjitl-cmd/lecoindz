import sys
import os

sys.path.append(os.path.dirname(__file__))

from database import get_connection


def init_database():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Découpage simple des instructions CREATE
    statements = sql_content.split(";")

    conn = get_connection()
    cursor = conn.cursor()

    for statement in statements:
        statement = statement.strip()

        if not statement:
            continue

        try:
            cursor.execute(statement)
            print(f"✅ Exécuté : {statement[:50]}...")
        except Exception as e:
            print(f"\n❌ Erreur SQL :")
            print(statement)
            print(f"\n➡ {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Base de données initialisée avec succès !")


if __name__ == "__main__":
    init_database()