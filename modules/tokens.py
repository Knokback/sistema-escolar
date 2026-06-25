from flask import Blueprint, render_template, redirect, url_for, session, flash
from database import get_db
from datetime import datetime
import uuid

tokens_bp = Blueprint(
    "tokens",
    __name__,
    url_prefix="/tokens"
)

# =========================
# GERAR TOKEN
# =========================

def gerar_token():

    return str(uuid.uuid4())[:8].upper()


# =========================
# ENVIAR CONVITE
# =========================

@tokens_bp.route("/enviar_convite/<int:user_id>", methods=["POST"])
def enviar_convite(user_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    meu_id = session["user_id"]

    # NÃO PODE ENVIAR PRA SI MESMO
    if meu_id == user_id:

        flash("Você não pode enviar convite para si mesmo.")

        return redirect(
            url_for("perfil.perfil", user_id=user_id)
        )

    # VERIFICAR SE JÁ EXISTE
    existente = db.execute("""

        SELECT *

        FROM connections

        WHERE

        (
            sender_id = ?
            AND receiver_id = ?
        )

        OR

        (
            sender_id = ?
            AND receiver_id = ?
        )

    """, (

        meu_id,
        user_id,

        user_id,
        meu_id

    )).fetchone()

    if existente:

        if existente["status"] == "ativo":
            flash("Vocês já estão conectados.")

        else:
            flash("Já existe um convite pendente.")

        db.close()

        return redirect(
            url_for("perfil.perfil", user_id=user_id)
        )

    # VERIFICAR TOKENS
    user = db.execute("""

        SELECT tokens

        FROM users

        WHERE id = ?

    """, (

        meu_id,

    )).fetchone()

    if user["tokens"] <= 0:

        flash("Você não possui tokens.")

        db.close()

        return redirect(
            url_for("perfil.perfil", user_id=user_id)
        )

    # GERAR TOKEN
    token_code = gerar_token()

    # INSERIR CONVITE
    db.execute("""

        INSERT INTO connections (

            sender_id,
            receiver_id,
            token_code,
            status,
            created_at

        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        meu_id,
        user_id,

        token_code,

        "pendente",

        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ))

    # REMOVER TOKEN
    db.execute("""

        UPDATE users

        SET tokens = tokens - 1

        WHERE id = ?

    """, (

        meu_id,

    ))

    db.commit()

    remetente = db.execute("""

    SELECT username

    FROM users

    WHERE id = ?

    """, (

        meu_id,

    )).fetchone()

    db.execute("""

    INSERT INTO notifications
    (user_id, message)

    VALUES (?, ?)

    """, (

        user_id,
        f"{remetente['username']} enviou um convite de conexão"

    ))

    db.commit()
    
    db.close()

    flash("Convite enviado!")

    return redirect(
        url_for("perfil.perfil", user_id=user_id)
    )


# =========================
# ACEITAR CONVITE
# =========================

@tokens_bp.route("/aceitar/<int:convite_id>", methods=["POST"])
def aceitar(convite_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    db.execute("""

        UPDATE connections

        SET status = 'ativo'

        WHERE id = ?

    """, (

        convite_id,

    ))

    db.commit()
    db.close()

    flash("Conexão criada!")

    return redirect(
        url_for("tokens.convites")
    )


# =========================
# VER CONVITES
# =========================

@tokens_bp.route("/convites")
def convites():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    convites = db.execute("""

        SELECT
            connections.*,
            users.username,
            users.rcid

        FROM connections

        JOIN users
        ON users.id = connections.sender_id

        WHERE

            connections.receiver_id = ?

            AND connections.status = 'pendente'

    """, (

        session["user_id"],

    )).fetchall()

    db.close()

    return render_template(
        "convites.html",
        convites=convites
    )


# =========================
# VER CONEXÕES
# =========================

@tokens_bp.route("/conexoes")
def conexoes():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    meu_id = session["user_id"]

    db = get_db()

    conexoes = db.execute("""

        SELECT DISTINCT users.*

        FROM connections

        JOIN users

        ON
        (
            users.id = connections.sender_id
            OR
            users.id = connections.receiver_id
        )

        WHERE

        (
            connections.sender_id = ?
            OR
            connections.receiver_id = ?
        )

        AND connections.status = 'ativo'

        AND users.id != ?

    """, (

        meu_id,
        meu_id,
        meu_id

    )).fetchall()

    db.close()

    return render_template(
        "conexoes.html",
        conexoes=conexoes
    )

# =========================
# REMOVER CONEXÃO
# =========================

@tokens_bp.route("/remover/<int:user_id>", methods=["POST"])
def remover(user_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    meu_id = session["user_id"]

    db = get_db()

    db.execute("""

    UPDATE connections

    SET status='inativo'

    WHERE

    (
        sender_id=?
        AND receiver_id=?
    )

    OR

    (
        sender_id=?
        AND receiver_id=?
    )

    """, (

        meu_id,
        user_id,

        user_id,
        meu_id

    ))

    db.commit()
    db.close()

    flash("Conexão removida.")

    return redirect(
        url_for("perfil.perfil", user_id=user_id)
    )
