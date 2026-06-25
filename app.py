import os
import sqlite3
from flask import Flask, render_template, session, redirect, url_for
from database import init_db

from modules.auth import auth_bp
from modules.home import home_bp
from modules.chat import chat_bp
from modules.perfil import perfil_bp
from modules.tokens import tokens_bp
from modules.search import search_bp

app = Flask(__name__)

app.secret_key = "redcareta-secret-key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["DATABASE"] = os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


# ==============================
# BLUEPRINTS
# ==============================

app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(tokens_bp)
app.register_blueprint(search_bp)

# ==============================
# ROTAS
# ==============================

@app.route("/")
def index():
    return render_template("login.html")


@app.route("/feed_private")
def feed_private():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    conn = get_db_connection()

    connections = conn.execute("""

    SELECT
        sender_id,
        receiver_id

    FROM connections

    WHERE
    (
        sender_id = ?
        OR
        receiver_id = ?
    )

    AND status = 'ativo'

    """, (

        user_id,
        user_id

    )).fetchall()

    friend_ids = []

    for c in connections:

        if c["sender_id"] == user_id:
            friend_ids.append(c["receiver_id"])

        else:
            friend_ids.append(c["sender_id"])
    friend_ids.append(user_id)

    if not friend_ids:
        friend_ids = [user_id]

    placeholders = ",".join("?" * len(friend_ids))

    posts = conn.execute(f"""

    SELECT
        posts.*,
        users.username,
        users.avatar

    FROM posts

    JOIN users
    ON posts.user_id = users.id

    WHERE posts.user_id IN ({placeholders})

    ORDER BY posts.created_at DESC

    """, friend_ids).fetchall()

    conn.close()

    return render_template("feed_private.html", posts=posts)

@app.errorhandler(413)
def arquivo_grande(e):

    return render_template(
        "erro413.html"
    ), 413

# ==============================
# EXECUÇÃO
# ==============================

if __name__ == "__main__":
    from werkzeug.serving import is_running_from_reloader

    if not is_running_from_reloader():
        init_db()

    app.run(host="0.0.0.0", port=5000, debug=True)
