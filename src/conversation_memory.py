# src/conversation_memory.py

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database/conversations.db")


class ConversationMemory:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    message TEXT,
                    response TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    def add_interaction(self, user_id: str, platform: str, message: str, response: str):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO interactions (user_id, platform, message, response) VALUES (?, ?, ?, ?)",
                    (user_id, platform, message, response)
                )
                conn.commit()
        except Exception as e:
            print(f"❌ Error guardando en memoria: {e}")

    def get_conversation_history(self, user_id: str, limit: int = 6) -> list:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                rows = conn.execute(
                    """SELECT message, response FROM interactions
                       WHERE user_id = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (user_id, limit)
                ).fetchall()
                # Retornar en orden cronológico
                return [{"message": r[0], "response": r[1]} for r in reversed(rows)]
        except Exception as e:
            print(f"❌ Error leyendo memoria: {e}")
            return []
