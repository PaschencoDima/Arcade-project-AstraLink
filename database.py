import sqlite3
import hashlib
import os

DATABASE_NAME = "game_database.db"


def init_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_progress (
            user_id INTEGER PRIMARY KEY,
            dash_unlocked BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_session (
            user_id INTEGER PRIMARY KEY,
            current_room INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, password_hash))
        user_id = cursor.lastrowid

        cursor.execute("INSERT INTO player_progress (user_id) VALUES (?)", (user_id,))
        cursor.execute("INSERT INTO current_session (user_id) VALUES (?)", (user_id,))

        conn.commit()
        return True, "Регистрация успешна!", user_id
    except sqlite3.IntegrityError:
        return False, "Пользователь с таким именем уже существует", None
    except Exception as e:
        return False, f"Ошибка: {str(e)}", None
    finally:
        conn.close()


def login_user(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if not result:
            return False, "Пользователь не найден", None

        user_id, stored_hash = result
        if hash_password(password) == stored_hash:
            cursor.execute("INSERT OR REPLACE INTO current_session (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return True, "Успешный вход!", user_id
        else:
            return False, "Неверный пароль", None
    except Exception as e:
        return False, f"Ошибка: {str(e)}", None
    finally:
        conn.close()


def get_current_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM current_session ORDER BY rowid DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None
    finally:
        conn.close()


def update_player_progress(user_id, dash_unlocked=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        if dash_unlocked is not None:
            cursor.execute("UPDATE player_progress SET dash_unlocked = ? WHERE user_id = ?",
                           (1 if dash_unlocked else 0, user_id))

        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def get_player_progress(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT dash_unlocked FROM player_progress WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result:
            dash_unlocked = bool(result[0])
            return dash_unlocked
        return False
    except:
        return False
    finally:
        conn.close()


def update_current_room(user_id, room_number):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE current_session SET current_room = ? WHERE user_id = ?",
                       (room_number, user_id))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def get_current_room(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT current_room FROM current_session WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return 1
    except:
        return 1
    finally:
        conn.close()


def logout_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM current_session")
        conn.commit()
    except:
        pass
    finally:
        conn.close()


init_database()