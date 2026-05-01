import os
from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dating.db"

app = Flask(__name__, static_folder="app/static")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            branch TEXT,
            bio TEXT,
            interests TEXT
        );

        CREATE TABLE IF NOT EXISTS swipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swiper_id INTEGER NOT NULL,
            swiped_id INTEGER NOT NULL,
            liked INTEGER NOT NULL,
            UNIQUE(swiper_id, swiped_id),
            FOREIGN KEY(swiper_id) REFERENCES users(id),
            FOREIGN KEY(swiped_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id),
            FOREIGN KEY(user1_id) REFERENCES users(id),
            FOREIGN KEY(user2_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(receiver_id) REFERENCES users(id)
        );
        """
    )
    db.commit()
    db.close()


if not DB_PATH.exists():
    init_db()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def login_required():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return None


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("discover"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        branch = request.form.get("branch", "").strip()
        bio = request.form.get("bio", "").strip()
        interests = request.form.get("interests", "").strip()

        if not email.endswith("@pes.edu"):
            return render_template("register.html", error="Only @pes.edu emails are allowed.")
        if not name or not password:
            return render_template("register.html", error="Name and password are required.")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash, branch, bio, interests) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, generate_password_hash(password), branch, bio, interests),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Email already registered.")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email.endswith("@pes.edu"):
            return render_template("login.html", error="Use your @pes.edu email.")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("discover"))

        return render_template("login.html", error="Invalid credentials.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    maybe_redirect = login_required()
    if maybe_redirect:
        return maybe_redirect

    user = current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        branch = request.form.get("branch", "").strip()
        bio = request.form.get("bio", "").strip()
        interests = request.form.get("interests", "").strip()

        db = get_db()
        db.execute(
            "UPDATE users SET name = ?, branch = ?, bio = ?, interests = ? WHERE id = ?",
            (name, branch, bio, interests, user["id"]),
        )
        db.commit()
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/discover")
def discover():
    maybe_redirect = login_required()
    if maybe_redirect:
        return maybe_redirect

    user = current_user()
    db = get_db()
    candidate = db.execute(
        """
        SELECT u.* FROM users u
        WHERE u.id != ?
        AND u.id NOT IN (
            SELECT swiped_id FROM swipes WHERE swiper_id = ?
        )
        LIMIT 1
        """,
        (user["id"], user["id"]),
    ).fetchone()

    return render_template("discover.html", user=user, candidate=candidate)


@app.route("/swipe", methods=["POST"])
def swipe():
    maybe_redirect = login_required()
    if maybe_redirect:
        return maybe_redirect

    swiper = current_user()
    swiped_id = int(request.form["swiped_id"])
    liked = 1 if request.form.get("liked") == "1" else 0

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO swipes (swiper_id, swiped_id, liked) VALUES (?, ?, ?)",
        (swiper["id"], swiped_id, liked),
    )

    match_created = False
    if liked:
        reverse_like = db.execute(
            "SELECT 1 FROM swipes WHERE swiper_id = ? AND swiped_id = ? AND liked = 1",
            (swiped_id, swiper["id"]),
        ).fetchone()
        if reverse_like:
            a, b = sorted([swiper["id"], swiped_id])
            db.execute(
                "INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)",
                (a, b),
            )
            match_created = True

    db.commit()
    return jsonify({"ok": True, "match": match_created})


@app.route("/matches")
def matches():
    maybe_redirect = login_required()
    if maybe_redirect:
        return maybe_redirect

    user = current_user()
    db = get_db()
    rows = db.execute(
        """
        SELECT m.id, u.id as other_id, u.name, u.branch
        FROM matches m
        JOIN users u ON u.id = CASE WHEN m.user1_id = ? THEN m.user2_id ELSE m.user1_id END
        WHERE m.user1_id = ? OR m.user2_id = ?
        ORDER BY m.created_at DESC
        """,
        (user["id"], user["id"], user["id"]),
    ).fetchall()

    return render_template("matches.html", matches=rows)


@app.route("/chat/<int:other_id>", methods=["GET", "POST"])
def chat(other_id: int):
    maybe_redirect = login_required()
    if maybe_redirect:
        return maybe_redirect

    user = current_user()
    db = get_db()

    pair = sorted([user["id"], other_id])
    is_match = db.execute(
        "SELECT 1 FROM matches WHERE user1_id = ? AND user2_id = ?",
        (pair[0], pair[1]),
    ).fetchone()

    if not is_match:
        return redirect(url_for("matches"))

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db.execute(
                "INSERT INTO messages (sender_id, receiver_id, body) VALUES (?, ?, ?)",
                (user["id"], other_id, body),
            )
            db.commit()
        return redirect(url_for("chat", other_id=other_id))

    other_user = db.execute("SELECT * FROM users WHERE id = ?", (other_id,)).fetchone()
    messages = db.execute(
        """
        SELECT * FROM messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
        """,
        (user["id"], other_id, other_id, user["id"]),
    ).fetchall()

    return render_template("chat.html", messages=messages, other_user=other_user, me=user)


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
