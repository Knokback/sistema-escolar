import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from database import get_db
import os
import uuid

home_bp = Blueprint("home", __name__, url_prefix="/home")

UPLOAD_FOLDER = os.path.join("static", "uploads")

ALLOWED_EXTENSIONS = {

    "png",
    "jpg", 
    "jpeg",
    "webp",

    "gif",

    "mp4",
    "webm"

}


def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(
            ".", 1
        )[1].lower()

        in ALLOWED_EXTENSIONS

    )

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===============================
# 🏠 PRAÇA PÚBLICA
# ===============================
@home_bp.route("/")
def home():

    pagina = request.args.get("pagina", 1, type=int)

    POR_PAGINA = 20

    offset = (pagina - 1) * POR_PAGINA

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    user = db.execute(
        "SELECT username FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    posts = db.execute("""
    SELECT

        posts.id,
        posts.user_id,
        posts.content,
        posts.media_path,
        posts.tipo,
        posts.created_at,

        users.username,
        users.avatar,

        COUNT(likes.id) as likes_count

    FROM posts

    JOIN users
    ON posts.user_id = users.id

    LEFT JOIN likes
    ON posts.id = likes.post_id

    WHERE posts.visibilidade = 'publico'

    GROUP BY posts.id

    ORDER BY posts.created_at DESC

    LIMIT ?
    OFFSET ?

    """, (

        POR_PAGINA,
        offset

    )).fetchall()
    
    total_posts = db.execute("""

    SELECT COUNT(*)

    FROM posts

    WHERE visibilidade='publico'

    """).fetchone()[0]

    tem_proxima = total_posts > pagina * POR_PAGINA

    db.close()

    return render_template(
        "home.html",
        posts=posts,
        username=user["username"],

        pagina=pagina,
        tem_proxima=tem_proxima
    )

# ===============================
# ❤️ LIKE
# ===============================
@home_bp.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db()

    existing = db.execute(
        "SELECT id FROM likes WHERE user_id = ? AND post_id = ?",
        (user_id, post_id)
    ).fetchone()

    if existing:

        db.execute(
            "DELETE FROM likes WHERE user_id = ? AND post_id = ?",
            (user_id, post_id)
        )

    else:

        db.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
            (user_id, post_id)
        )

    db.commit()

    post = db.execute("""

    SELECT user_id

    FROM posts

    WHERE id = ?

    """, (

        post_id,

    )).fetchone()

    dono_post = post["user_id"]

    ja_tem = db.execute("""

    SELECT id

    FROM notifications

    WHERE user_id = ?
    AND message = ?

    """, (

        dono_post,
        f"{session['username']} curtiu o teu post"

    )).fetchone()

    if dono_post == user_id:
        db.close()
        return redirect(url_for("home.home"))

    if not ja_tem:

        db.execute("""

        INSERT INTO notifications
        (user_id, message)

        VALUES (?, ?)

        """, (

            dono_post,
            f"{session['username']} curtiu o teu post"

        ))

    likes = db.execute("""

    SELECT COUNT(*)
    FROM likes
    WHERE post_id = ?

    """, (post_id,)).fetchone()[0]


    db.commit()
    db.close()


    return jsonify({
        "likes": likes
    })

# ===============================
# 🗑️ DELETAR POST
# ===============================
@home_bp.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    db.execute(
        "DELETE FROM posts WHERE id = ? AND user_id = ?",
        (post_id, session["user_id"])
    )

    db.commit()
    db.close()

    return redirect(url_for("home.home"))


# ===============================
# ✏️ EDITAR POST
# ===============================
@home_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit(post_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":

        content = request.form.get("content", "").strip()

        db.execute(
            "UPDATE posts SET content = ? WHERE id = ? AND user_id = ?",
            (content, post_id, session["user_id"])
        )

        db.commit()
        db.close()

        return redirect(url_for("home.home"))

    post = db.execute(
        "SELECT * FROM posts WHERE id = ? AND user_id = ?",
        (post_id, session["user_id"])
    ).fetchone()

    db.close()

    return render_template("edit_post.html", post=post)

#================================
#Sl alguma coisa
#================================

@home_bp.route("/postar_feed", methods=["POST"])
def postar_feed():

    content = request.form["content"]

    db = get_db()

    db.execute("""
    INSERT INTO posts
    (user_id,content,tipo)
    VALUES(?,?,?)
    """,

    (
    session["user_id"],
    content,
    "feed"
    ))

    db.commit()
    db.close()

    return redirect(
    url_for("home.home")
    )

# =========================================
# POSTAGENS
# =========================================

@home_bp.route("/postar_imagem", methods=["POST"])
def postar_imagem():

    return salvar_media("imagem")


@home_bp.route("/postar_video", methods=["POST"])
def postar_video():

    return salvar_media("video")

def salvar_media(tipo):

    file = request.files["media"]

    ext = file.filename.rsplit(".", 1)[1].lower()

    IMAGENS = {"png", "jpg", "jpeg", "gif", "webp"}
    VIDEOS = {"mp4", "webm", "mov", "avi"}

    if tipo == "imagem" and ext.lower() not in IMAGENS:
        return redirect(url_for("home.home"))

    if tipo == "video" and ext.lower() not in VIDEOS:
        return redirect(url_for("home.home"))

    nome = f"{uuid.uuid4()}.{ext}"

    caminho = os.path.join(
        UPLOAD_FOLDER,
        nome
    )

    file.save(caminho)

    db = get_db()

    db.execute("""
    INSERT INTO posts
    (user_id, media_path, tipo)
    VALUES (?, ?, ?)
    """, (

        session["user_id"],
        f"uploads/{nome}",
        tipo

    ))

    db.commit()
    db.close()
    
    return redirect(url_for("home.home"))

# =========================================
# NOTIFICAÇÕES
# =========================================

@home_bp.route("/notificacoes")
def notificacoes():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    notificacoes = db.execute("""

    SELECT *

    FROM notifications

    WHERE user_id = ?

    ORDER BY created_at DESC

    """, (

        session["user_id"],

    )).fetchall()

    db.close()

    return render_template(
        "notificacoes.html",
        notificacoes=notificacoes
    )

@home_bp.route("/posts_ajax")
def posts_ajax():

    pagina = request.args.get("pagina", 1, type=int)

    POR_PAGINA = 20

    offset = (pagina - 1) * POR_PAGINA

    db = get_db()

    posts = db.execute("""

    SELECT

        posts.id,
        posts.user_id,
        posts.content,
        posts.media_path,
        posts.tipo,
        posts.created_at,

        users.username,
        users.avatar,

        COUNT(likes.id) as likes_count

    FROM posts

    JOIN users
    ON posts.user_id = users.id

    LEFT JOIN likes
    ON posts.id = likes.post_id

    WHERE posts.visibilidade='publico'

    GROUP BY posts.id

    ORDER BY posts.created_at DESC

    LIMIT ?
    OFFSET ?

    """, (

        POR_PAGINA,
        offset

    )).fetchall()

    db.close()

    return render_template(
        "posts_ajax.html",
        posts=posts
    )
