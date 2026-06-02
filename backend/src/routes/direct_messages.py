from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.middleware.auth import get_current_user
from src.config.database import get_connection

router = APIRouter()

class MessageRequest(BaseModel):
    content: str

def get_or_create_conversation(user1_id, user2_id):
    """Récupère ou crée une conversation entre deux utilisateurs."""
    conn = get_connection()
    cursor = conn.cursor()

    # Chercher une conversation existante
    cursor.execute("""
        SELECT id FROM CG_CONVERSATIONS
        WHERE (user1_id = %(u1)s AND user2_id = %(u2)s)
        OR (user1_id = %(u2)s AND user2_id = %(u1)s)
    """, {"u1": user1_id, "u2": user2_id})
    row = cursor.fetchone()

    if row:
        conv_id = row[0]
    else:
        # Créer une nouvelle conversation
        cursor.execute("""
            INSERT INTO CG_CONVERSATIONS (user1_id, user2_id)
            VALUES (%(u1)s, %(u2)s)
        """, {"u1": user1_id, "u2": user2_id})
        conn.commit()
        conv_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return conv_id

def get_conversation_messages(conv_id):
    """Récupère les messages d'une conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.conversation_id, m.sender_id, m.content,
               m.is_read, m.created_at,
               u.first_name, u.last_name
        FROM CG_DIRECT_MESSAGES m
        JOIN CG_USERS u ON m.sender_id = u.id
        WHERE m.conversation_id = %(conv_id)s
        ORDER BY m.created_at ASC
    """, {"conv_id": conv_id})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{
        "id": row[0], "conversation_id": row[1],
        "sender_id": row[2], "content": row[3],
        "is_read": row[4], "created_at": str(row[5]),
        "sender": {"first_name": row[6], "last_name": row[7]}
    } for row in rows]

def get_user_conversations(user_id):
    """Récupère toutes les conversations d'un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id,
               u1.id, u1.first_name, u1.last_name,
               u2.id, u2.first_name, u2.last_name,
               (SELECT COUNT(*) FROM CG_DIRECT_MESSAGES m
                WHERE m.conversation_id = c.id
                AND m.sender_id != %(user_id)s
                AND m.is_read = 0) as unread,
               (SELECT m2.content FROM CG_DIRECT_MESSAGES m2
                WHERE m2.conversation_id = c.id
                ORDER BY m2.created_at DESC
                LIMIT 1) as last_message
        FROM CG_CONVERSATIONS c
        JOIN CG_USERS u1 ON c.user1_id = u1.id
        JOIN CG_USERS u2 ON c.user2_id = u2.id
        WHERE c.user1_id = %(user_id)s OR c.user2_id = %(user_id)s
        ORDER BY c.created_at DESC
    """, {"user_id": user_id})
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{
        "id": row[0],
        "user1": {"id": row[1], "first_name": row[2], "last_name": row[3]},
        "user2": {"id": row[4], "first_name": row[5], "last_name": row[6]},
        "unread": row[7],
        "last_message": row[8]
    } for row in rows]

@router.post("/avec/{other_user_id}")
def envoyer_message(other_user_id: int, data: MessageRequest, current_user=Depends(get_current_user)):
    """Envoyer un message direct à un utilisateur."""
    if other_user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous envoyer un message")

    conv_id = get_or_create_conversation(current_user["user_id"], other_user_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CG_DIRECT_MESSAGES (conversation_id, sender_id, content)
        VALUES (%(conv_id)s, %(sender_id)s, %(content)s)
    """, {"conv_id": conv_id, "sender_id": current_user["user_id"], "content": data.content})
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Message envoye", "conversation_id": conv_id}

@router.get("/avec/{other_user_id}")
def get_messages(other_user_id: int, current_user=Depends(get_current_user)):
    """Récupère les messages avec un utilisateur."""
    conv_id = get_or_create_conversation(current_user["user_id"], other_user_id)

    # Marquer les messages comme lus
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE CG_DIRECT_MESSAGES
        SET is_read = 1
        WHERE conversation_id = %(conv_id)s
        AND sender_id != %(user_id)s
        AND is_read = 0
    """, {"conv_id": conv_id, "user_id": current_user["user_id"]})
    conn.commit()
    cursor.close()
    conn.close()

    messages = get_conversation_messages(conv_id)
    return {"conversation_id": conv_id, "messages": messages}

@router.get("/mes-conversations")
def mes_conversations(current_user=Depends(get_current_user)):
    """Récupère toutes les conversations de l'utilisateur."""
    conversations = get_user_conversations(current_user["user_id"])
    return {"conversations": conversations}