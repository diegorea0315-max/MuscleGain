# init_db.py
import sqlite3

DATABASE = "database.db"


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def init_db(db_path: str = DATABASE) -> None:
    """
    Crea las tablas necesarias si no existen.
    Incluye pequenas migraciones si faltan columnas.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        rest_days TEXT DEFAULT '0',
        weekly_min_sessions INTEGER DEFAULT 3,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        routine TEXT DEFAULT '',
        duration_min INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    if not _column_exists(cur, "workouts", "routine"):
        cur.execute("ALTER TABLE workouts ADD COLUMN routine TEXT DEFAULT ''")
    if not _column_exists(cur, "workouts", "duration_min"):
        cur.execute("ALTER TABLE workouts ADD COLUMN duration_min INTEGER DEFAULT 0")
    if not _column_exists(cur, "workouts", "note"):
        cur.execute("ALTER TABLE workouts ADD COLUMN note TEXT DEFAULT ''")

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER NOT NULL,
        exercise TEXT NOT NULL,
        weight REAL DEFAULT 0,
        reps INTEGER DEFAULT 0,
        sets INTEGER DEFAULT 1,
        notes TEXT DEFAULT '',
        FOREIGN KEY (workout_id) REFERENCES workouts(id)
    )
    """
    )

    if not _column_exists(cur, "sets", "sets"):
        cur.execute("ALTER TABLE sets ADD COLUMN sets INTEGER DEFAULT 1")
    if not _column_exists(cur, "sets", "notes"):
        cur.execute("ALTER TABLE sets ADD COLUMN notes TEXT DEFAULT ''")

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS saved_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(user_id, name),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        train_days TEXT DEFAULT '',
        rest_days TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    if not _column_exists(cur, "routines", "train_days"):
        cur.execute("ALTER TABLE routines ADD COLUMN train_days TEXT DEFAULT ''")
    if not _column_exists(cur, "routines", "rest_days"):
        cur.execute("ALTER TABLE routines ADD COLUMN rest_days TEXT DEFAULT ''")

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS routine_days (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        routine_id INTEGER NOT NULL,
        day_label TEXT NOT NULL,
        day_order INTEGER DEFAULT 0,
        FOREIGN KEY (routine_id) REFERENCES routines(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS routine_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        routine_day_id INTEGER NOT NULL,
        exercise TEXT NOT NULL,
        FOREIGN KEY (routine_day_id) REFERENCES routine_days(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        created_at TEXT DEFAULT '',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS muscle_info (
        muscle_slug TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        overview_html TEXT DEFAULT '',
        updated_at TEXT DEFAULT ''
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS muscle_tiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        muscle_slug TEXT NOT NULL,
        tier TEXT NOT NULL,
        title TEXT DEFAULT '',
        body_html TEXT DEFAULT '',
        video_url TEXT DEFAULT '',
        updated_at TEXT DEFAULT '',
        UNIQUE(muscle_slug, tier)
    )
    """
    )

    conn.commit()
    conn.close()
