import sqlite3
import hashlib
import os
from datetime import datetime

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
            double_jump_unlocked BOOLEAN DEFAULT 0,
            arena_completed BOOLEAN DEFAULT 0,
            sonic_defeated BOOLEAN DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arena_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            arena_completed BOOLEAN DEFAULT 0,
            robots_defeated INTEGER DEFAULT 0,
            damage_taken INTEGER DEFAULT 0,
            completion_time INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            user_id INTEGER PRIMARY KEY,
            total_robots_defeated INTEGER DEFAULT 0,
            total_damage_dealt INTEGER DEFAULT 0,
            total_play_time INTEGER DEFAULT 0,
            deaths_count INTEGER DEFAULT 0,
            bosses_defeated INTEGER DEFAULT 0,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_name TEXT NOT NULL,
            achievement_description TEXT,
            unlocked BOOLEAN DEFAULT 0,
            unlocked_at TIMESTAMP,
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
        cursor.execute("INSERT INTO player_stats (user_id) VALUES (?)", (user_id,))

        initial_achievements = [
            ("Новичок", "Зарегистрируйтесь в игре"),
            ("Первые шаги", "Завершите обучение"),
        ]
        for name, desc in initial_achievements:
            cursor.execute(
                "INSERT INTO achievements (user_id, achievement_name, achievement_description) VALUES (?, ?, ?)",
                (user_id, name, desc)
            )

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

            cursor.execute("""
                UPDATE player_stats 
                SET last_played = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            """, (user_id,))

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
    except Exception as e:
        return None
    finally:
        conn.close()


def update_player_progress(user_id, dash_unlocked=None, double_jump_unlocked=None,
                           arena_completed=None, sonic_defeated=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        update_fields = []
        params = []

        if dash_unlocked is not None:
            update_fields.append("dash_unlocked = ?")
            params.append(1 if dash_unlocked else 0)

        if double_jump_unlocked is not None:
            update_fields.append("double_jump_unlocked = ?")
            params.append(1 if double_jump_unlocked else 0)

        if arena_completed is not None:
            update_fields.append("arena_completed = ?")
            params.append(1 if arena_completed else 0)

        if sonic_defeated is not None:
            update_fields.append("sonic_defeated = ?")
            params.append(1 if sonic_defeated else 0)

        if update_fields:
            update_fields.append("last_updated = CURRENT_TIMESTAMP")
            params.append(user_id)

            query = f"UPDATE player_progress SET {', '.join(update_fields)} WHERE user_id = ?"
            cursor.execute(query, params)

            check_achievements(user_id, cursor)

            conn.commit()
            return True
        return False
    except Exception as e:
        return False
    finally:
        conn.close()


def get_player_progress(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT dash_unlocked, double_jump_unlocked, arena_completed, sonic_defeated 
            FROM player_progress 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()

        if result:
            dash_unlocked, double_jump_unlocked, arena_completed, sonic_defeated = result
            return {
                'dash_unlocked': bool(dash_unlocked),
                'double_jump_unlocked': bool(double_jump_unlocked),
                'arena_completed': bool(arena_completed),
                'sonic_defeated': bool(sonic_defeated)
            }
        return {
            'dash_unlocked': False,
            'double_jump_unlocked': False,
            'arena_completed': False,
            'sonic_defeated': False
        }
    except Exception as e:
        return {
            'dash_unlocked': False,
            'double_jump_unlocked': False,
            'arena_completed': False,
            'sonic_defeated': False
        }
    finally:
        conn.close()


def unlock_dash_ability(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE player_progress 
            SET dash_unlocked = 1, last_updated = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            INSERT OR IGNORE INTO achievements 
            (user_id, achievement_name, achievement_description) 
            VALUES (?, ?, ?)
        """, (user_id, "Мастер скорости", "Разблокируйте способность Dash"))

        cursor.execute("""
            UPDATE achievements 
            SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
        """, (user_id, "Мастер скорости"))

        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def unlock_double_jump_ability(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE player_progress 
            SET double_jump_unlocked = 1, last_updated = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            UPDATE player_stats 
            SET bosses_defeated = bosses_defeated + 1
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            INSERT OR IGNORE INTO achievements 
            (user_id, achievement_name, achievement_description) 
            VALUES (?, ?, ?)
        """, (user_id, "Воздушный мастер", "Разблокируйте двойной прыжок"))

        cursor.execute("""
            UPDATE achievements 
            SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
        """, (user_id, "Воздушный мастер"))

        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def mark_sonic_defeated(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE player_progress 
            SET sonic_defeated = 1, last_updated = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            UPDATE player_stats 
            SET bosses_defeated = bosses_defeated + 1
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            INSERT OR IGNORE INTO achievements 
            (user_id, achievement_name, achievement_description) 
            VALUES (?, ?, ?)
        """, (user_id, "Победитель Соника", "Победите босса Соника"))

        cursor.execute("""
            UPDATE achievements 
            SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
        """, (user_id, "Победитель Соника"))

        conn.commit()
        return True
    except Exception as e:
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
        return True
    except Exception as e:
        return False
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
    except Exception as e:
        return 1
    finally:
        conn.close()


def update_arena_progress(user_id, arena_completed=True, robots_defeated=0,
                          damage_taken=0, completion_time=0):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        if arena_completed:
            cursor.execute("""
                UPDATE player_progress 
                SET arena_completed = 1, last_updated = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            """, (user_id,))

        cursor.execute("""
            INSERT INTO arena_progress 
            (user_id, arena_completed, robots_defeated, damage_taken, completion_time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, 1 if arena_completed else 0, robots_defeated,
              damage_taken, completion_time))

        if robots_defeated > 0:
            cursor.execute("""
                UPDATE player_stats 
                SET total_robots_defeated = total_robots_defeated + ?,
                    total_damage_dealt = total_damage_dealt + ?
                WHERE user_id = ?
            """, (robots_defeated, robots_defeated * 40, user_id))

        check_arena_achievements(user_id, cursor, robots_defeated)

        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def get_arena_progress(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT arena_completed 
            FROM player_progress 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()

        arena_completed = False
        if result:
            arena_completed = bool(result[0])

        cursor.execute("""
            SELECT COUNT(*) as attempts, 
                   SUM(robots_defeated) as total_robots,
                   MIN(completion_time) as best_time,
                   MAX(completed_at) as last_completed
            FROM arena_progress 
            WHERE user_id = ? AND arena_completed = 1
        """, (user_id,))
        stats_result = cursor.fetchone()

        stats = {
            'arena_completed': arena_completed,
            'attempts': stats_result[0] if stats_result[0] else 0,
            'total_robots_defeated': stats_result[1] if stats_result[1] else 0,
            'best_time': stats_result[2] if stats_result[2] else 0,
            'last_completed': stats_result[3] if stats_result[3] else None
        }

        return stats
    except Exception as e:
        return {'arena_completed': False, 'attempts': 0, 'total_robots_defeated': 0}
    finally:
        conn.close()


def update_player_stats(user_id, robots_defeated=0, damage_dealt=0,
                        play_time=0, death=False, boss_defeated=False):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        update_fields = []
        params = []

        if robots_defeated > 0:
            update_fields.append("total_robots_defeated = total_robots_defeated + ?")
            params.append(robots_defeated)

        if damage_dealt > 0:
            update_fields.append("total_damage_dealt = total_damage_dealt + ?")
            params.append(damage_dealt)

        if play_time > 0:
            update_fields.append("total_play_time = total_play_time + ?")
            params.append(play_time)

        if death:
            update_fields.append("deaths_count = deaths_count + 1")

        if boss_defeated:
            update_fields.append("bosses_defeated = bosses_defeated + 1")

        if update_fields:
            update_fields.append("last_played = CURRENT_TIMESTAMP")
            params.append(user_id)

            query = f"UPDATE player_stats SET {', '.join(update_fields)} WHERE user_id = ?"
            cursor.execute(query, params)

            check_stat_achievements(user_id, cursor)

            conn.commit()
            return True
        return False
    except Exception as e:
        return False
    finally:
        conn.close()


def get_player_stats(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT total_robots_defeated, total_damage_dealt, 
                   total_play_time, deaths_count, bosses_defeated, last_played
            FROM player_stats 
            WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()

        if result:
            return {
                'total_robots_defeated': result[0],
                'total_damage_dealt': result[1],
                'total_play_time': result[2],
                'deaths_count': result[3],
                'bosses_defeated': result[4],
                'last_played': result[5]
            }
        return {
            'total_robots_defeated': 0,
            'total_damage_dealt': 0,
            'total_play_time': 0,
            'deaths_count': 0,
            'bosses_defeated': 0,
            'last_played': None
        }
    except Exception as e:
        return {
            'total_robots_defeated': 0,
            'total_damage_dealt': 0,
            'total_play_time': 0,
            'deaths_count': 0,
            'bosses_defeated': 0,
            'last_played': None
        }
    finally:
        conn.close()


def check_achievements(user_id, cursor):
    try:
        cursor.execute(
            "SELECT dash_unlocked, double_jump_unlocked, arena_completed, sonic_defeated FROM player_progress WHERE user_id = ?",
            (user_id,))
        result = cursor.fetchone()

        if not result:
            return

        dash_unlocked, double_jump_unlocked, arena_completed, sonic_defeated = result

        if dash_unlocked:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements 
                (user_id, achievement_name, achievement_description) 
                VALUES (?, ?, ?)
            """, (user_id, "Мастер скорости", "Разблокируйте способность Dash"))

            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Мастер скорости"))

        if double_jump_unlocked:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements 
                (user_id, achievement_name, achievement_description) 
                VALUES (?, ?, ?)
            """, (user_id, "Воздушный мастер", "Разблокируйте двойной прыжок"))

            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Воздушный мастер"))

        if sonic_defeated:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements 
                (user_id, achievement_name, achievement_description) 
                VALUES (?, ?, ?)
            """, (user_id, "Победитель Соника", "Победите босса Соника"))

            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Победитель Соника"))

        if arena_completed:
            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Победитель арены"))
    except Exception as e:
        pass


def check_arena_achievements(user_id, cursor, robots_defeated):
    try:
        if robots_defeated >= 2:
            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Уничтожитель роботов"))
    except Exception as e:
        pass


def check_stat_achievements(user_id, cursor):
    try:
        cursor.execute("""
            SELECT total_robots_defeated, total_play_time, deaths_count, bosses_defeated
            FROM player_stats 
            WHERE user_id = ?
        """, (user_id,))
        stats = cursor.fetchone()

        if not stats:
            return

        total_robots, total_play_time, deaths_count, bosses_defeated = stats

        if total_robots >= 10:
            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Опытный боец"))

        if total_play_time >= 3600:
            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Ветеран"))

        if deaths_count >= 10:
            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Неудачник"))

        if bosses_defeated >= 1:
            cursor.execute("""
                INSERT OR IGNORE INTO achievements 
                (user_id, achievement_name, achievement_description) 
                VALUES (?, ?, ?)
            """, (user_id, "Охотник на боссов", "Победите первого босса"))

            cursor.execute("""
                UPDATE achievements 
                SET unlocked = 1, unlocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND achievement_name = ? AND unlocked = 0
            """, (user_id, "Охотник на боссов"))
    except Exception as e:
        pass


def get_achievements(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT achievement_name, achievement_description, unlocked, unlocked_at
            FROM achievements 
            WHERE user_id = ?
            ORDER BY unlocked ASC, id ASC
        """, (user_id,))

        achievements = []
        for row in cursor.fetchall():
            achievements.append({
                'name': row[0],
                'description': row[1],
                'unlocked': bool(row[2]),
                'unlocked_at': row[3]
            })

        return achievements
    except Exception as e:
        return []
    finally:
        conn.close()


def logout_user():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM current_session")
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def get_user_info(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT username, created_at FROM users WHERE id = ?", (user_id,))
        user_result = cursor.fetchone()

        if not user_result:
            return None

        username, created_at = user_result

        progress = get_player_progress(user_id)
        stats = get_player_stats(user_id)
        achievements = get_achievements(user_id)
        arena_progress = get_arena_progress(user_id)

        return {
            'username': username,
            'created_at': created_at,
            'progress': progress,
            'stats': stats,
            'achievements': achievements,
            'arena_progress': arena_progress
        }
    except Exception as e:
        return None
    finally:
        conn.close()


def reset_player_progress(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE player_progress 
            SET dash_unlocked = 0, double_jump_unlocked = 0, arena_completed = 0, 
                sonic_defeated = 0, last_updated = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("DELETE FROM arena_progress WHERE user_id = ?", (user_id,))

        cursor.execute("""
            UPDATE achievements 
            SET unlocked = 0, unlocked_at = NULL 
            WHERE user_id = ? AND achievement_name NOT IN ('Новичок', 'Первые шаги')
        """, (user_id,))

        cursor.execute("""
            UPDATE player_stats 
            SET total_robots_defeated = 0, total_damage_dealt = 0,
                bosses_defeated = 0, deaths_count = 0
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("UPDATE current_session SET current_room = 1 WHERE user_id = ?", (user_id,))

        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


init_database()