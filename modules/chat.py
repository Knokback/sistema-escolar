from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
def chat():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db()

    # ================= GET (mostrar mensagens) =================

    messages = db.execute("""

    SELECT
    messages.*,
    users.username,
    users.avatar

    FROM messages

    JOIN users
    ON messages.user_id = users.id

    ORDER BY messages.created_at ASC

    """).fetchall()

    db.close()

    return render_template("chat.html", messages=messages)
