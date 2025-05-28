import sqlite3
from datetime import datetime
from typing import Any, Text, Dict, List
class UserDatabase:
    def __init__(self, db_name='users.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                tasks TEXT,
                user_id TEXT PRIMARY KEY,
                username TEXT,
                theme TEXT,
                language TEXT DEFAULT 'ru',
                last_activity TEXT,
                email TEXT,
                city TEXT,
                hobbies TEXT
            )
        ''')
        self.conn.commit()

    def save_user(self, user_data: dict):
        query = '''
            INSERT OR REPLACE INTO users 
            VALUES (:user_id, :username, :theme, :language, :last_activity, :email, :city, :hobbies)
        '''
        self.cursor.execute(query, user_data)
        self.conn.commit()

    def get_user(self, user_id: str) -> dict:
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return {

            "username": row[1],
            "theme": row[2],
            "language": row[3],
            "last_activity": row[4],
            "email": row[5],
            "city": row[6],
            "hobbies": row[7]
        }

    def get_all_users(self) -> list:
        self.cursor.execute('SELECT * FROM users')
        rows = self.cursor.fetchall()
        return [{
            "username": row[1],
            "theme": row[2],
            "language": row[3],
            "last_activity": row[4],
            "email": row[5],
            "city": row[6],
            "hobbies": row[7]
        } for row in rows]

    def get_last_user(self) -> Dict[str, Any]:
        self.cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        return dict(row) if row else {}

    def close(self):
        self.conn.close()