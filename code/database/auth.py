import sqlite3
import hashlib
from typing import Optional, Tuple

class AuthManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> Optional[int]:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            ''', (username, password_hash, email))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None  # Username already exists
        except Exception as e:
            print(f"Failed to create user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Tuple[int, str]]:
        """Authenticate user and return user ID if successful"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                SELECT id, username FROM users 
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user[0],))
                conn.commit()
            
            conn.close()
            return user  # Returns (user_id, username) or None
        except Exception as e:
            print(f"Authentication failed: {e}")
            return None