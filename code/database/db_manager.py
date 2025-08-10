import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from langchain.schema import HumanMessage, AIMessage

class DatabaseManager:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.db_path = self._get_db_path()
        self.init_database()
    
    def _get_db_path(self) -> str:
        """Get database path"""
        db_dir = os.path.join(self.root_dir, "data")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "chat_app.db")
    
    def init_database(self):
        """Initialize SQLite database with users and chat history tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Create chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_message(self, user_id: int, message_type: str, content: str) -> bool:
        """Save message to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_history (user_id, message_type, content)
                VALUES (?, ?, ?)
            ''', (user_id, message_type, content))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to save message: {e}")
            return False
    
    def load_chat_history(self, user_id: int, limit: int = 50) -> List:
        """Load chat history for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_type, content, timestamp 
                FROM chat_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to LangChain message objects
            chat_history = []
            for message_type, content, timestamp in rows:
                if message_type == "human":
                    chat_history.append(HumanMessage(content=content))
                else:
                    chat_history.append(AIMessage(content=content))
            
            return chat_history
        except Exception as e:
            print(f"Failed to load chat history: {e}")
            return []
    
    def clear_chat_history(self, user_id: int) -> bool:
        """Clear chat history for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to clear chat history: {e}")
            return False