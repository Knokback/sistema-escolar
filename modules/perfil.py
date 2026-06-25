from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

perfil_bp = Blueprint("perfil", __name__)

DATABASE = "database.db"


# =========================
# DB
# =========================

def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# PERFIL
# =========================

@perfil_bp.route("/perfil/<int:user_id>", methods=["GET", "POST"])
@perfil_bp.route("/perfil", methods=["GET", "POST"])
def perfil(user_id=None):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    perfil_id = user_id if user_id else session["user_id"]

    db = get_db()

    # =========================
    # EDITAR PERFIL
    # =========================

    if request.method == "POST":

        if perfil_id != session["user_id"]:

            flash("Você não pode editar este perfil.")
            return redirect(url_for("perfil.perfil", user_id=perfil_id))

        username = request.form.get("username")
        nickname = request.form.get("nickname")
        age = request.form.get("age")
        location = request.form.get("location")
        status = request.form.get("status")
        bio = request.form.get("bio")

        avatar = request.files.get("avatar")

        avatar_path = None

        # =========================
        # AVATAR
        # =========================

        if avatar and avatar.filename != "":

            filename = secure_filename(avatar.filename)

            upload_folder = os.path.join("static", "uploads")

            os.makedirs(upload_folder, exist_ok=True)

            avatar_path = f"uploads/{filename}"

            avatar.save(os.path.join("static", "uploads", filename))

        # =========================
        # UPDATE
        # =========================

        if avatar_path:

            db.execute("""

            UPDATE users

            SET
                username=?,
                nickname=?,
                age=?,
                location=?,
                status=?,
                bio=?,
                avatar=?

            WHERE id=?

            """, (

                username,
                nickname,
                age,
                location,
                status,
                bio,
                avatar_path,

                session["user_id"]

            ))

        else:

            db.execute("""

            UPDATE users

            SET
                username=?,
                nickname=?,
                age=?,
                location=?,
                status=?,
                bio=?

            WHERE id=?

            """, (

                username,
                nickname,
                age,
                location,
                status,
                bio,

                session["user_id"]

            ))

        db.commit()

        flash("Perfil atualizado!")

        return redirect(url_for("perfil.perfil"))

    # =========================
    # USER
    # =========================

    user = db.execute(

        "SELECT * FROM users WHERE id=?",

        (perfil_id,)

    ).fetchone()

    if not user:

        flash("Usuário não encontrado.")
        return redirect(url_for("home.home"))

    # =========================
    # POSTS
    # =========================

    posts = db.execute("""

    SELECT *
    FROM posts

    WHERE user_id=?

    ORDER BY created_at DESC

    """, (perfil_id,)).fetchall()

    # ==========================
    # SEGUDORES
    # ==========================

    seguidores = db.execute("""

    SELECT COUNT(*)

    FROM followers

    WHERE following_id = ?

    """, (perfil_id,)).fetchone()[0]

    # ===========================
    # SEGUIDO
    # ===========================

    seguindo = db.execute("""

    SELECT COUNT(*)

    FROM followers

    WHERE follower_id = ?

    """, (perfil_id,)).fetchone()[0]

    # ============================
    # JÁ SEGUE
    # ============================

    ja_segue = db.execute("""

    SELECT *

    FROM followers

    WHERE follower_id = ?
    AND following_id = ?

    """, (

        session["user_id"],
        perfil_id

    )).fetchone()
    
    #==========================
    #Sl
    #==========================

    connection = db.execute("""

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

        session["user_id"],
        perfil_id,

        perfil_id,
        session["user_id"]

    )).fetchone()

    # =========================
    # STATUS DA CONEXÃO
    # =========================

    connection_status = None

    if perfil_id != session["user_id"]:

        connection = db.execute("""

        SELECT *

        FROM connections

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

            session["user_id"],
            perfil_id,

            perfil_id,
            session["user_id"]

        )).fetchone()

        if connection:

            connection_status = connection["status"]
            
    # =========================
    # STATS
    # =========================

    total_posts = len(posts)

    total_images = 0
    total_videos = 0

    for post in posts:

        media = post["media_path"]

        if media:

            if media.endswith(".mp4"):
                total_videos += 1
            else:
                total_images += 1

    db.close()

    return render_template(

        "perfil.html",

        user=user,
        posts=posts,

        total_posts=total_posts,
        total_images=total_images,
        total_videos=total_videos,

        seguidores=seguidores,
        seguindo=seguindo,
        ja_segue=ja_segue,

        perfil_id=perfil_id,

        connection=connection,
        connection_status=connection_status

    )

#================================
#TA PESQUISAR NOME
#================================
@perfil_bp.route("/pesquisar")
def pesquisar():

    termo = request.args.get("q", "").strip()

    resultados = []

    if termo:

        db = get_db()

        resultados = db.execute("""

        SELECT
            id,
            username,
            avatar

        FROM users

        WHERE username LIKE ?

        LIMIT 50

        """, (f"%{termo}%",)).fetchall()

        db.close()

    return render_template(
        "pesquisar.html",
        resultados=resultados,
        termo=termo
    )

# =========================================
# ROTA SEGUIR
# =========================================
@perfil_bp.route("/seguir/<int:user_id>", methods=["POST"])
def seguir(user_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    try:

        db.execute("""
        INSERT INTO followers
        (follower_id, following_id)
        VALUES (?, ?)
        """, (

            session["user_id"],
            user_id

        ))

        db.commit()

    except:
        pass

    seguidor = db.execute("""

    SELECT username

    FROM users

    WHERE id = ?

    """, (

        session["user_id"],

    )).fetchone()

    db.execute("""

    INSERT INTO notifications
    (user_id, message)

    VALUES (?, ?)

    """, (

        user_id,
        f"{seguidor['username']} começou a seguir você"

    ))

    db.commit()

    db.close()

    return redirect(request.referrer or url_for("home.home"))

# =========================================
# PARAR DE SEGUIR
# =========================================

@perfil_bp.route("/deixar_seguir/<int:user_id>", methods=["POST"])
def deixar_seguir(user_id):

    db = get_db()

    db.execute("""
    DELETE FROM followers

    WHERE follower_id = ?
    AND following_id = ?
    """, (

        session["user_id"],
        user_id

    ))

    db.commit()
    db.close()

    return redirect(request.referrer or url_for("home.home")) 
