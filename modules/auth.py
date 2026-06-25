from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import uuid

auth_bp = Blueprint("auth", __name__)


# =========================
# GERAR RCID
# =========================

def gerar_rcid():

    codigo = str(uuid.uuid4())[:8].upper()

    return f"RC-{codigo}"


# =========================
# LOGIN
# =========================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("home.home"))

        else:

            error = "Usuário ou senha inválidos."

    return render_template(
        "login.html",
        error=error
    )


# =========================
# REGISTRO
# =========================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # =========================
        # SENHAS DIFERENTES
        # =========================

        if password != confirm_password:

            error = "As senhas não coincidem."

            return render_template(
                "register.html",
                error=error
            )

        db = get_db()

        # =========================
        # USERNAME EXISTE?
        # =========================

        existing_user = db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:

            error = "Esse nome de usuário já existe."

            return render_template(
                "register.html",
                error=error
            )

        # =========================
        # EMAIL EXISTE?
        # =========================

        existing_email = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:

            error = "Esse email já está cadastrado."

            return render_template(
                "register.html",
                error=error
            )

        # =========================
        # HASH SENHA
        # =========================

        hashed_password = generate_password_hash(password)

        # =========================
        # RCID
        # =========================

        rcid = gerar_rcid()

        # =========================
        # CRIAR USUÁRIO
        # =========================

        db.execute("""

        INSERT INTO users (

            username,
            email,
            password,
            rcid,
            tokens,
            tokens_max

        )

        VALUES (?, ?, ?, ?, ?, ?)

        """, (

            username,
            email,
            hashed_password,
            rcid,
            3,
            6

        ))

        db.commit()
        db.close()

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "register.html",
        error=error
    )


# =========================
# LOGOUT
# =========================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("auth.login")
    )
