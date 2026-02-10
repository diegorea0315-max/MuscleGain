from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta, date

from init_db import init_db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_change_me")
DATABASE = os.getenv("DATABASE_PATH", "database.db")
ADMIN_BOOTSTRAP_USERNAMES = {"DraxsTg"}

MUSCLES = [
    {"slug": "pectorales", "name": "Pectorales"},
    {"slug": "espalda", "name": "Espalda"},
    {"slug": "hombros", "name": "Hombros"},
    {"slug": "biceps", "name": "Biceps"},
    {"slug": "triceps", "name": "Triceps"},
    {"slug": "antebrazos", "name": "Antebrazos"},
    {"slug": "abdomen", "name": "Abdomen"},
    {"slug": "gluteos", "name": "Gluteos"},
    {"slug": "cuadriceps", "name": "Cuadriceps"},
    {"slug": "isquios", "name": "Isquios"},
    {"slug": "pantorrillas", "name": "Pantorrillas"},
    {"slug": "trapecios", "name": "Trapecios"},
]

# Sugerencias base para autocompletar y chips por musculo.
MUSCLE_SUGGESTIONS_BASE = {
    "Pectorales": ["Press banca", "Press inclinado", "Fondos", "Aperturas"],
    "Espalda": ["Dominadas", "Remo con barra", "Jalon al pecho", "Remo con mancuerna"],
    "Hombros": ["Press militar", "Elevaciones laterales", "Face pull", "Pajaros"],
    "Biceps": ["Curl barra", "Curl mancuernas", "Curl martillo"],
    "Triceps": ["Fondos", "Extensiones polea", "Press frances"],
    "Pierna": ["Sentadilla", "Prensa", "Peso muerto rumano", "Curl femoral", "Zancadas"],
    "Gluteos": ["Hip thrust", "Puente gluteo", "Sentadilla sumo"],
    "Abdomen": ["Plancha", "Crunch", "Elevaciones de piernas"],
    "Pantorrillas": ["Elevaciones de talones", "Gemelo sentado"],
}

# Plantillas simples para rutinas recomendadas.
RECOMMENDED_ROUTINES = [
    {
        "name": "Full Body 3 dias",
        "tagline": "Basica y efectiva para empezar.",
        "train_days": ["Lun", "Mie", "Vie"],
        "rest_days": ["Mar", "Jue", "Sab", "Dom"],
        "days": [
            {"label": "Dia A", "exercises": ["Sentadilla", "Press banca", "Remo con barra", "Plancha"]},
            {"label": "Dia B", "exercises": ["Peso muerto", "Press militar", "Dominadas", "Abdomen"]},
            {"label": "Dia C", "exercises": ["Prensa", "Fondos", "Remo con mancuerna", "Gemelos"]},
        ],
    },
    {
        "name": "Upper/Lower 4 dias",
        "tagline": "Fuerza y volumen equilibrado.",
        "train_days": ["Lun", "Mar", "Jue", "Vie"],
        "rest_days": ["Mie", "Sab", "Dom"],
        "days": [
            {"label": "Upper 1", "exercises": ["Press banca", "Remo con barra", "Press militar", "Curl biceps"]},
            {"label": "Lower 1", "exercises": ["Sentadilla", "Curl femoral", "Gemelos", "Abdomen"]},
            {"label": "Upper 2", "exercises": ["Press inclinado", "Dominadas", "Elevaciones laterales", "Triceps"]},
            {"label": "Lower 2", "exercises": ["Peso muerto rumano", "Prensa", "Zancadas", "Gluteos"]},
        ],
    },
    {
        "name": "Push/Pull/Legs 6 dias",
        "tagline": "Para frecuencia alta.",
        "train_days": ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"],
        "rest_days": ["Dom"],
        "days": [
            {"label": "Push 1", "exercises": ["Press banca", "Press militar", "Fondos", "Triceps"]},
            {"label": "Pull 1", "exercises": ["Dominadas", "Remo con barra", "Curl biceps", "Face pull"]},
            {"label": "Legs 1", "exercises": ["Sentadilla", "Prensa", "Gemelos", "Abdomen"]},
            {"label": "Push 2", "exercises": ["Press inclinado", "Aperturas", "Elevaciones laterales"]},
            {"label": "Pull 2", "exercises": ["Remo con mancuerna", "Jalon al pecho", "Curl martillo"]},
            {"label": "Legs 2", "exercises": ["Peso muerto rumano", "Zancadas", "Gluteos"]},
        ],
    },
]



def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def iso_today() -> str:
    return date.today().isoformat()


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def parse_days_csv(value: str) -> set[str]:
    return {v for v in (value or "").split(",") if v}


def build_suggestions(user_exercises: list[str]) -> dict[str, list[str]]:
    suggestions = {k: list(v) for k, v in MUSCLE_SUGGESTIONS_BASE.items()}
    all_sugs = sorted({ex for items in suggestions.values() for ex in items})
    if user_exercises:
        suggestions["Tus ejercicios"] = sorted(set(user_exercises))
    return {"Todos": all_sugs, **suggestions}


def parse_rest_days(rest_days_str: str) -> set[int]:
    """
    rest_days_str: "0,3,6" donde 0=Dom, 6=Sab.
    """
    if not rest_days_str:
        return {0}
    parts = [p.strip() for p in rest_days_str.split(",") if p.strip().isdigit()]
    return set(int(p) for p in parts)


def today_dow_sun0(d: date | None = None) -> int:
    """
    Devuelve dia de la semana con Domingo=0 ... Sabado=6.
    Python: weekday() => Lun=0 ... Dom=6.
    """
    d = d or date.today()
    return (d.weekday() + 1) % 7


def ensure_user_settings(user_id: int) -> sqlite3.Row:
    """
    Si no existe settings para el usuario, lo crea con defaults.
    """
    db = get_db()
    row = db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        db.execute(
            "INSERT INTO user_settings (user_id, rest_days, weekly_min_sessions) VALUES (?, ?, ?)",
            (user_id, "0", 3),
        )
        db.commit()
        row = db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return row


def get_user_exercises(user_id: int) -> list[str]:
    db = get_db()
    rows = db.execute(
        "SELECT name FROM exercises WHERE user_id = ? ORDER BY name ASC",
        (user_id,),
    ).fetchall()
    db.close()
    return [r["name"] for r in rows]


def get_user_routines(user_id: int) -> list[str]:
    db = get_db()
    rows = db.execute(
        "SELECT name FROM routines WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    db.close()
    return [r["name"] for r in rows]


def ensure_exercise(db: sqlite3.Connection, user_id: int, name: str) -> None:
    name = (name or "").strip()
    if not name:
        return
    db.execute(
        "INSERT OR IGNORE INTO exercises (user_id, name) VALUES (?, ?)",
        (user_id, name),
    )


def table_has_column(db: sqlite3.Connection, table: str, column: str) -> bool:
    rows = db.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def is_admin_user(user_id: int) -> bool:
    db = get_db()
    row = db.execute("SELECT 1 FROM admins WHERE user_id = ? LIMIT 1", (user_id,)).fetchone()
    db.close()
    return row is not None


def ensure_admin_bootstrap(username: str) -> None:
    if not username or username not in ADMIN_BOOTSTRAP_USERNAMES:
        return
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if user:
        db.execute(
            "INSERT OR IGNORE INTO admins (user_id, created_at) VALUES (?, ?)",
            (user["id"], datetime.utcnow().isoformat()),
        )
        db.commit()
    db.close()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesion primero.")
            return redirect(url_for("login"))
        if not is_admin_user(int(session["user_id"])):
            flash("No tienes permisos de administrador.")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_admin_flag():
    is_admin = False
    if "user_id" in session:
        try:
            is_admin = is_admin_user(int(session["user_id"]))
        except Exception:
            is_admin = False
    return {"is_admin": is_admin}


# Ensure tables exist when running under gunicorn/production
init_db(DATABASE)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesion primero.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped



@app.route("/")
def home():
    return render_template("home.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Completa todos los campos.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password),
            )
            db.commit()

            user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                db.execute(
                    "INSERT OR IGNORE INTO user_settings (user_id, rest_days, weekly_min_sessions) VALUES (?, ?, ?)",
                    (user["id"], "0", 3),
                )
                db.commit()
                if username in ADMIN_BOOTSTRAP_USERNAMES:
                    db.execute(
                        "INSERT OR IGNORE INTO admins (user_id, created_at) VALUES (?, ?)",
                        (user["id"], datetime.utcnow().isoformat()),
                    )
                    db.commit()

            flash("Cuenta creada correctamente. Inicia sesion.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Usuario o correo ya existe.")
        except Exception:
            flash("Error inesperado. Intenta de nuevo.")
        finally:
            db.close()

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Completa usuario y contrasena.")
            return render_template("login.html")

        db = get_db()
        user = db.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            ensure_admin_bootstrap(user["username"])
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contrasena incorrectos.")

    return render_template("login.html")




def workouts_count_between(user_id: int, start_iso: str, end_iso: str) -> int:
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) as c
        FROM workouts
        WHERE user_id = ? AND date BETWEEN ? AND ?
        """,
        (user_id, start_iso, end_iso),
    ).fetchone()
    db.close()
    return int(row["c"] or 0)


def volume_between(user_id: int, start_iso: str, end_iso: str) -> float:
    db = get_db()
    row = db.execute(
        """
        SELECT COALESCE(SUM(s.weight * s.reps * s.sets), 0) as vol
        FROM sets s
        JOIN workouts w ON w.id = s.workout_id
        WHERE w.user_id = ? AND w.date BETWEEN ? AND ?
        """,
        (user_id, start_iso, end_iso),
    ).fetchone()
    db.close()
    return float(row["vol"] or 0.0)


def last_workout_date(user_id: int) -> str | None:
    db = get_db()
    row = db.execute(
        """
        SELECT date
        FROM workouts
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    db.close()
    return row["date"] if row else None


def smart_streak(user_id: int, rest_days: set[int]) -> int:
    """
    Racha inteligente:
    - Cuenta dias consecutivos hacia atras donde:
      (hubo entrenamiento) OR (era dia de descanso programado)
    - Se rompe si: NO es descanso y NO hay entrenamiento ese dia.
    """
    db = get_db()
    streak = 0
    day = date.today()

    while True:
        iso = day.isoformat()
        dow = today_dow_sun0(day)

        trained = (
            db.execute(
                "SELECT 1 FROM workouts WHERE user_id = ? AND date = ? LIMIT 1",
                (user_id, iso),
            ).fetchone()
            is not None
        )

        is_rest = dow in rest_days

        if trained or is_rest:
            streak += 1
            day = day - timedelta(days=1)
            continue

        break

    db.close()
    return streak


def recent_activity(user_id: int, limit: int = 5) -> list[dict]:
    db = get_db()
    rows = db.execute(
        """
        SELECT id, date, duration_min, note
        FROM workouts
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()

    items = []
    for r in rows:
        items.append(
            {
                "date": r["date"],
                "duration_min": int(r["duration_min"] or 0),
                "note": (r["note"] or "").strip(),
            }
        )
    db.close()
    return items


def default_notes() -> list[str]:
    return [
        "Constancia > intensidad.",
        "Hoy: tecnica limpia.",
        "Hazlo simple y repetible.",
        "Un set bien hecho vale mas que tres apurados.",
        "Si dudas, reduce peso y controla.",
    ]


def get_notes_for_user(user_id: int) -> list[str]:
    db = get_db()
    rows = db.execute(
        "SELECT text FROM saved_notes WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    db.close()

    saved = [r["text"] for r in rows if r["text"]]
    base = default_notes()
    out = []
    for t in saved + base:
        if t not in out:
            out.append(t)
    return out[:10]



@app.route("/dashboard")
@login_required
def dashboard():
    user_id = int(session["user_id"])
    settings = ensure_user_settings(user_id)
    rest_days = parse_rest_days(settings["rest_days"])
    weekly_min = int(settings["weekly_min_sessions"] or 3)

    today = date.today()
    end7 = today.isoformat()
    start7 = (today - timedelta(days=6)).isoformat()

    this7_count = workouts_count_between(user_id, start7, end7)
    this7_vol = volume_between(user_id, start7, end7)

    prev7_end = (today - timedelta(days=7)).isoformat()
    prev7_start = (today - timedelta(days=13)).isoformat()
    prev7_vol = volume_between(user_id, prev7_start, prev7_end)

    if this7_vol == 0 and prev7_vol == 0:
        trend_label = "Sin datos"
        trend_pct = 0
    elif prev7_vol == 0:
        trend_label = "Subiendo"
        trend_pct = 100
    else:
        delta = (this7_vol - prev7_vol) / prev7_vol
        trend_pct = int(delta * 100)
        if trend_pct >= 10:
            trend_label = "Subiendo"
        elif trend_pct <= -10:
            trend_label = "Bajando"
        else:
            trend_label = "Estable"

    streak = smart_streak(user_id, rest_days)

    last_date = last_workout_date(user_id)
    last_label = "Aun no registras"
    if last_date:
        d0 = datetime.strptime(last_date, "%Y-%m-%d").date()
        diff = (today - d0).days
        last_label = "Hoy" if diff == 0 else f"Hace {diff} dia" if diff == 1 else f"Hace {diff} dias"

    dow = today_dow_sun0(today)
    if dow in rest_days:
        action_title = "Recupera"
        action_sub = "Hoy toca descanso. Estira y duerme bien."
        day_chip = "Descanso"
    else:
        action_title = "Entrena"
        action_sub = "Haz una sesion corta y limpia."
        day_chip = "Entreno"

    if this7_count >= weekly_min:
        next_step = "Mantener"
        next_step_sub = "Vas bien esta semana."
    else:
        falta = weekly_min - this7_count
        next_step = "Completar semana"
        next_step_sub = f"Te faltan {falta} sesion(es) para tu meta."

    notes = get_notes_for_user(user_id)
    activity = recent_activity(user_id, limit=6)

    stats = {
        "streak": streak,
        "sessions_7d": this7_count,
        "volume_7d": round(this7_vol, 1),
        "trend_label": trend_label,
        "trend_pct": trend_pct,
        "last_label": last_label,
    }

    focus = {
        "chip": day_chip,
        "action_title": action_title,
        "action_sub": action_sub,
        "next_step": next_step,
        "next_step_sub": next_step_sub,
    }

    return render_template(
        "dashboard.html",
        username=session.get("username", "Usuario"),
        stats=stats,
        focus=focus,
        notes=notes,
        activity=activity,
    )



@app.route("/session/new", methods=["GET", "POST"])
@login_required
def register_session():
    user_id = int(session["user_id"])
    exercises = get_user_exercises(user_id)
    routines = get_user_routines(user_id)
    suggestions = build_suggestions(exercises)
    exercise_options = sorted({ex for ex in exercises} | {ex for items in suggestions.values() for ex in items})
    muscle_slug_map = {m["slug"]: m["name"] for m in MUSCLES}

    if request.method == "POST":
        workout_date = request.form.get("date", "").strip() or iso_today()
        duration_min = safe_int(request.form.get("duration_min", "0"), 0)
        note = request.form.get("note", "").strip()
        routine = (request.form.get("routine") or "Libre").strip()

        exercise_list = request.form.getlist("exercise[]")
        sets_list = request.form.getlist("sets[]")
        reps_list = request.form.getlist("reps[]")
        weight_list = request.form.getlist("weight[]")
        note_list = request.form.getlist("set_note[]")

        has_rows = any((e or "").strip() for e in exercise_list)
        if not has_rows:
            flash("Agrega al menos un ejercicio.")
            return render_template(
                "session.html",
                exercises=exercises,
                routines=routines,
                suggestions=suggestions,
                muscle_slug_map=muscle_slug_map,
                exercise_options=exercise_options,
                today=iso_today(),
            )

        db = get_db()
        try:
            if table_has_column(db, "workouts", "routine"):
                cur = db.execute(
                    "INSERT INTO workouts (user_id, date, routine, duration_min, note) VALUES (?, ?, ?, ?, ?)",
                    (user_id, workout_date, routine or "Libre", duration_min, note),
                )
            else:
                cur = db.execute(
                    "INSERT INTO workouts (user_id, date, duration_min, note) VALUES (?, ?, ?, ?)",
                    (user_id, workout_date, duration_min, note),
                )
            workout_id = cur.lastrowid

            for i, ex in enumerate(exercise_list):
                name = (ex or "").strip()
                if not name:
                    continue
                sets_count = safe_int(sets_list[i] if i < len(sets_list) else 1, 1)
                reps = safe_int(reps_list[i] if i < len(reps_list) else 0, 0)
                weight = safe_float(weight_list[i] if i < len(weight_list) else 0, 0.0)
                set_note = (note_list[i] if i < len(note_list) else "").strip()

                ensure_exercise(db, user_id, name)
                db.execute(
                    """
                    INSERT INTO sets (workout_id, exercise, sets, reps, weight, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (workout_id, name, max(1, sets_count), reps, weight, set_note),
                )

            db.commit()
        finally:
            db.close()

        flash("Sesion registrada correctamente.")
        return redirect(url_for("progress"))

    return render_template(
        "session.html",
        exercises=exercises,
        routines=routines,
        suggestions=suggestions,
        muscle_slug_map=muscle_slug_map,
        exercise_options=exercise_options,
        today=iso_today(),
    )



@app.route("/routines", methods=["GET", "POST"])
@login_required
def routines():
    user_id = int(session["user_id"])
    exercises = get_user_exercises(user_id)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        train_days = request.form.getlist("train_days[]")
        rest_days = request.form.getlist("rest_days[]")
        day_labels = request.form.getlist("day_label[]")
        day_exercises = request.form.getlist("day_exercises[]")

        if not name:
            flash("Pon un nombre a la rutina.")
            return redirect(url_for("routines"))

        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO routines (user_id, name, created_at, train_days, rest_days) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, datetime.utcnow().isoformat(), ",".join(train_days), ",".join(rest_days)),
            )
            routine_id = cur.lastrowid

            for idx, label in enumerate(day_labels):
                day_label = (label or "").strip()
                if not day_label:
                    continue
                cur_day = db.execute(
                    "INSERT INTO routine_days (routine_id, day_label, day_order) VALUES (?, ?, ?)",
                    (routine_id, day_label, idx),
                )
                day_id = cur_day.lastrowid

                lines = (day_exercises[idx] if idx < len(day_exercises) else "").splitlines()
                for ex in [l.strip() for l in lines if l.strip()]:
                    ensure_exercise(db, user_id, ex)
                    db.execute(
                        "INSERT INTO routine_exercises (routine_day_id, exercise) VALUES (?, ?)",
                        (day_id, ex),
                    )

            db.commit()
        finally:
            db.close()
        flash("Rutina creada.")
        return redirect(url_for("routines"))

    db = get_db()
    routines_rows = db.execute(
        """
        SELECT r.id, r.name,
               (SELECT COUNT(*) FROM routine_days d WHERE d.routine_id = r.id) AS days
        FROM routines r
        WHERE r.user_id = ?
        ORDER BY r.id DESC
        """,
        (user_id,),
    ).fetchall()
    db.close()

    routines_list = [
        {"id": r["id"], "name": r["name"], "days": r["days"]} for r in routines_rows
    ]

    return render_template(
        "routines.html",
        routines=routines_list,
        exercises=exercises,
        recommended=RECOMMENDED_ROUTINES,
    )


@app.route("/routines/<int:routine_id>/edit", methods=["GET", "POST"])
@login_required
def routine_edit(routine_id: int):
    user_id = int(session["user_id"])
    exercises = get_user_exercises(user_id)

    db = get_db()
    routine = db.execute(
        "SELECT id, name, train_days, rest_days FROM routines WHERE id = ? AND user_id = ?",
        (routine_id, user_id),
    ).fetchone()

    if not routine:
        db.close()
        flash("Rutina no encontrada.")
        return redirect(url_for("routines"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        train_days = request.form.getlist("train_days[]")
        rest_days = request.form.getlist("rest_days[]")
        day_labels = request.form.getlist("day_label[]")
        day_exercises = request.form.getlist("day_exercises[]")

        if not name:
            flash("Pon un nombre a la rutina.")
            db.close()
            return redirect(url_for("routine_edit", routine_id=routine_id))

        try:
            db.execute(
                "UPDATE routines SET name = ?, train_days = ?, rest_days = ? WHERE id = ? AND user_id = ?",
                (name, ",".join(train_days), ",".join(rest_days), routine_id, user_id),
            )

            db.execute(
                "DELETE FROM routine_exercises WHERE routine_day_id IN (SELECT id FROM routine_days WHERE routine_id = ?)",
                (routine_id,),
            )
            db.execute("DELETE FROM routine_days WHERE routine_id = ?", (routine_id,))

            for idx, label in enumerate(day_labels):
                day_label = (label or "").strip()
                if not day_label:
                    continue
                cur_day = db.execute(
                    "INSERT INTO routine_days (routine_id, day_label, day_order) VALUES (?, ?, ?)",
                    (routine_id, day_label, idx),
                )
                day_id = cur_day.lastrowid

                lines = (day_exercises[idx] if idx < len(day_exercises) else "").splitlines()
                for ex in [l.strip() for l in lines if l.strip()]:
                    ensure_exercise(db, user_id, ex)
                    db.execute(
                        "INSERT INTO routine_exercises (routine_day_id, exercise) VALUES (?, ?)",
                        (day_id, ex),
                    )

            db.commit()
        finally:
            db.close()
        flash("Rutina actualizada.")
        return redirect(url_for("routines"))

    days_rows = db.execute(
        "SELECT id, day_label FROM routine_days WHERE routine_id = ? ORDER BY day_order ASC",
        (routine_id,),
    ).fetchall()

    days = []
    for d in days_rows:
        ex_rows = db.execute(
            "SELECT exercise FROM routine_exercises WHERE routine_day_id = ?",
            (d["id"],),
        ).fetchall()
        exercises_text = "\n".join([e["exercise"] for e in ex_rows])
        days.append({"label": d["day_label"], "exercises": exercises_text})

    db.close()

    return render_template(
        "routine_edit.html",
        routine={"id": routine["id"], "name": routine["name"]},
        days=days,
        exercises=exercises,
        train_days=parse_days_csv(routine["train_days"]),
        rest_days=parse_days_csv(routine["rest_days"]),
    )


@app.route("/routines/<int:routine_id>/delete", methods=["POST"])
@login_required
def routine_delete(routine_id: int):
    user_id = int(session["user_id"])
    db = get_db()
    db.execute(
        "DELETE FROM routine_exercises WHERE routine_day_id IN (SELECT id FROM routine_days WHERE routine_id = ?)",
        (routine_id,),
    )
    db.execute("DELETE FROM routine_days WHERE routine_id = ?", (routine_id,))
    db.execute("DELETE FROM routines WHERE id = ? AND user_id = ?", (routine_id, user_id))
    db.commit()
    db.close()
    flash("Rutina eliminada.")
    return redirect(url_for("routines"))



@app.route("/progress")
@login_required
def progress():
    user_id = int(session["user_id"])
    db = get_db()

    workouts = db.execute(
        """
        SELECT id, date, duration_min, note
        FROM workouts
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 12
        """,
        (user_id,),
    ).fetchall()

    workout_items = []
    for w in workouts:
        set_rows = db.execute(
            """
            SELECT exercise, sets, reps, weight, notes
            FROM sets
            WHERE workout_id = ?
            ORDER BY id ASC
            """,
            (w["id"],),
        ).fetchall()
        workout_items.append(
            {
                "date": w["date"],
                "duration_min": int(w["duration_min"] or 0),
                "note": (w["note"] or "").strip(),
                "sets": [
                    {
                        "exercise": s["exercise"],
                        "sets": int(s["sets"] or 1),
                        "reps": int(s["reps"] or 0),
                        "weight": float(s["weight"] or 0),
                        "notes": (s["notes"] or "").strip(),
                    }
                    for s in set_rows
                ],
            }
        )

    summary_rows = db.execute(
        """
        SELECT s.exercise as exercise,
               MAX(w.date) as last_date,
               MAX(s.weight) as max_weight,
               MAX(s.weight * (1 + s.reps / 30.0)) as est_1rm,
               SUM(s.weight * s.reps * s.sets) as volume
        FROM sets s
        JOIN workouts w ON w.id = s.workout_id
        WHERE w.user_id = ?
        GROUP BY s.exercise
        ORDER BY last_date DESC
        """,
        (user_id,),
    ).fetchall()

    exercise_summary = []
    for r in summary_rows:
        exercise_summary.append(
            {
                "exercise": r["exercise"],
                "last_date": r["last_date"],
                "max_weight": round(float(r["max_weight"] or 0), 1),
                "est_1rm": round(float(r["est_1rm"] or 0), 1),
                "volume": round(float(r["volume"] or 0), 1),
            }
        )

    db.close()

    return render_template("progress.html", workouts=workout_items, summary=exercise_summary)



@app.route("/muscle-map")
@login_required
def muscle_map():
    return render_template("muscle_map.html", muscles=MUSCLES)


def get_muscle_info(slug: str) -> dict:
    db = get_db()
    row = db.execute(
        "SELECT muscle_slug, name, overview_html FROM muscle_info WHERE muscle_slug = ?",
        (slug,),
    ).fetchone()
    db.close()
    if not row:
        return {"slug": slug, "name": slug.title(), "overview_html": ""}
    return {"slug": row["muscle_slug"], "name": row["name"], "overview_html": row["overview_html"] or ""}


def get_muscle_tiers(slug: str) -> list[dict]:
    tier_order = ["S", "A", "B", "C", "D", "E", "F"]
    db = get_db()
    rows = db.execute(
        """
        SELECT tier, title, body_html, video_url
        FROM muscle_tiers
        WHERE muscle_slug = ?
        """,
        (slug,),
    ).fetchall()
    db.close()
    by_tier = {r["tier"]: r for r in rows}
    tiers = []
    for t in tier_order:
        r = by_tier.get(t)
        tiers.append(
            {
                "tier": t,
                "title": (r["title"] or "") if r else "",
                "body_html": (r["body_html"] or "") if r else "",
                "video_url": (r["video_url"] or "") if r else "",
            }
        )
    return tiers


@app.route("/api/muscles/<slug>")
@login_required
def api_muscle(slug: str):
    info = get_muscle_info(slug)
    tiers = get_muscle_tiers(slug)
    return jsonify({"ok": True, "info": info, "tiers": tiers})


@app.route("/admin/muscle-map")
@admin_required
def admin_muscle_map():
    return render_template("admin_muscle_map.html", muscles=MUSCLES)


@app.route("/admin/muscle-map/save/<slug>", methods=["POST"])
@admin_required
def admin_save_muscle(slug: str):
    payload = request.json or {}
    name = (payload.get("name") or "").strip() or slug.title()
    overview_html = (payload.get("overview_html") or "").strip()
    tiers = payload.get("tiers") or []

    db = get_db()
    db.execute(
        """
        INSERT INTO muscle_info (muscle_slug, name, overview_html, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(muscle_slug) DO UPDATE SET
            name = excluded.name,
            overview_html = excluded.overview_html,
            updated_at = excluded.updated_at
        """,
        (slug, name, overview_html, datetime.utcnow().isoformat()),
    )

    for item in tiers:
        tier = (item.get("tier") or "").strip().upper()
        if tier not in {"S", "A", "B", "C", "D", "E", "F"}:
            continue
        title = (item.get("title") or "").strip()
        body_html = (item.get("body_html") or "").strip()
        video_url = (item.get("video_url") or "").strip()
        db.execute(
            """
            INSERT INTO muscle_tiers (muscle_slug, tier, title, body_html, video_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(muscle_slug, tier) DO UPDATE SET
                title = excluded.title,
                body_html = excluded.body_html,
                video_url = excluded.video_url,
                updated_at = excluded.updated_at
            """,
            (slug, tier, title, body_html, video_url, datetime.utcnow().isoformat()),
        )

    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/admin/admins", methods=["GET", "POST"])
@admin_required
def admin_admins():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        action = (request.form.get("action") or "").strip()
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            flash("Usuario no encontrado.")
        else:
            if action == "add":
                db.execute(
                    "INSERT OR IGNORE INTO admins (user_id, created_at) VALUES (?, ?)",
                    (user["id"], datetime.utcnow().isoformat()),
                )
                db.commit()
                flash("Admin agregado.")
            elif action == "remove":
                if username in ADMIN_BOOTSTRAP_USERNAMES:
                    flash("No puedes quitar al admin principal.")
                else:
                    db.execute("DELETE FROM admins WHERE user_id = ?", (user["id"],))
                    db.commit()
                    flash("Admin eliminado.")
        db.close()
        return redirect(url_for("admin_admins"))

    db = get_db()
    rows = db.execute(
        """
        SELECT u.username
        FROM admins a
        JOIN users u ON u.id = a.user_id
        ORDER BY u.username ASC
        """
    ).fetchall()
    db.close()
    admins = [r["username"] for r in rows]
    return render_template("admin_admins.html", admins=admins)



@app.route("/api/save_note", methods=["POST"])
@login_required
def api_save_note():
    user_id = int(session["user_id"])
    text = (request.json or {}).get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Texto vacio"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO saved_notes (user_id, text, created_at) VALUES (?, ?, ?)",
        (user_id, text, datetime.utcnow().isoformat()),
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})



@app.route("/logout")
def logout():
    session.clear()
    flash("Sesion cerrada correctamente.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db(DATABASE)
    app.run(debug=True)
