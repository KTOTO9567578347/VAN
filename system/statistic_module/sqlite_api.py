import sqlite3
import hashlib

class SQLiteAPI:
    def __init__(self, db_name='../users.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                privileges TEXT DEFAULT 'user'
            )
        ''')
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, name, password, privileges='user'):
        hashed_password = self._hash_password(password)
        try:
            self.cursor.execute('''
                INSERT INTO users (name, password, privileges) VALUES (?, ?, ?)
            ''', (name, hashed_password, privileges))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"User '{name}' already exists.")
            return False

    def login(self, name, password):
        hashed_password = self._hash_password(password)
        self.cursor.execute('''
            SELECT password FROM users WHERE name = ?
        ''', (name,))
        result = self.cursor.fetchone()
        if result and result[0] == hashed_password:
            return True
        return False
    
    def delete_user_by_username(self, username):
        self.cursor.execute('''
            DELETE FROM users WHERE name = ?
        ''', (username,))
        self.conn.commit()
    
    def get_users(self):
        self.cursor.execute('''
            SELECT name, privileges FROM users
        ''')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

# Пример использования
if __name__ == "__main__":
    api = SQLiteAPI()

    # Добавление пользователей с разными привилегиями
    api.add_user("user1", "password123", "user")
    api.add_user("root", "1234", "admin")

    # Попытка входа
    if api.login("user1", "password123"):
        print("Login successful!")
    else:
        print("Login failed!")

    # Получение списка пользователей с привилегиями
    users = api.get_users()
    print("Users with privileges:")
    for user in users:
        print(f"Name: {user[0]}, Privileges: {user[1]}")

    api.close()