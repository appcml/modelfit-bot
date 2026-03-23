import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class ConversationMemory:
    """Gestiona historial de conversaciones por usuario."""
    
    def __init__(self, db_path: str = "database/conversations.db"):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Crea directorio y DB si no existen."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_type TEXT DEFAULT 'text',
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                platform TEXT,
                name TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_interaction DATETIME,
                interaction_count INTEGER DEFAULT 0,
                preferences TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_interaction(self, user_id: str, platform: str, message: str, 
                       response: str = None, message_type: str = "text",
                       metadata: Dict = None):
        """Guarda interacción en base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Guardar mensaje
        cursor.execute('''
            INSERT INTO conversations (user_id, platform, message, response, 
                                     message_type, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, platform, message, response, message_type, 
              json.dumps(metadata) if metadata else None))
        
        # Actualizar perfil de usuario
        cursor.execute('''
            INSERT INTO user_profiles (user_id, platform, last_interaction, interaction_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                last_interaction = CURRENT_TIMESTAMP,
                interaction_count = interaction_count + 1
        ''', (user_id, platform))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtiene últimas interacciones con un usuario."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, timestamp, message_type
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in reversed(rows):  # Orden cronológico
            history.append({
                'message': row[0],
                'response': row[1],
                'timestamp': row[2],
                'type': row[3]
            })
        
        return history
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Obtiene perfil de usuario."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, first_seen, last_interaction, interaction_count, preferences
            FROM user_profiles WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'name': row[0],
                'first_seen': row[1],
                'last_interaction': row[2],
                'interaction_count': row[3],
                'preferences': json.loads(row[4]) if row[4] else {}
            }
        return None
    
    def get_daily_message_count(self, user_id: str) -> int:
        """Cuenta mensajes de hoy por usuario (para rate limiting)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*) FROM conversations
            WHERE user_id = ? AND date(timestamp) = ?
        ''', (user_id, today))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def update_user_name(self, user_id: str, name: str):
        """Actualiza nombre del usuario si lo detectamos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_profiles SET name = ? WHERE user_id = ?
        ''', (name, user_id))
        
        conn.commit()
        conn.close()
