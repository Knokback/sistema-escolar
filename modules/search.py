from flask import Blueprint, render_template, request
from database import get_db

search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/search"
)

@search_bp.route("/pesquisar")
def pesquisar():

    termo = request.args.get("q", "")

    db = get_db()

    users = db.execute("""
    SELECT id, username, avatar
    FROM users
    WHERE username LIKE ?
    """, (f"%{termo}%",)).fetchall()

    db.close()

    return render_template(
        "search.html",
        users=users,
        termo=termo
    )
