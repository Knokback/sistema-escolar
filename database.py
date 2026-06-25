import sqlite3
import os
import uuid

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


# =========================
# CONEXÃO
# =========================

def get_db():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CRIAR DATABASE
# =========================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("A criar base de dados...")

    # =========================
    # USERS
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,

        rcid TEXT UNIQUE,

        full_name TEXT,
        nickname TEXT,

        age INTEGER,

        location TEXT,

        status TEXT,

        bio TEXT,

        avatar TEXT,

        tokens INTEGER DEFAULT 3,
        tokens_max INTEGER DEFAULT 6,

        ultimo_reset TEXT

    )
    """)

    # =========================
    # POSTS
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        content TEXT,

        media_path TEXT,

        tipo TEXT DEFAULT 'feed',

        visibilidade TEXT DEFAULT 'publico',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)

    try:
        cursor.execute("""
        ALTER TABLE posts
        ADD COLUMN tipo TEXT DEFAULT 'feed'
        """)
    except:
        pass

    # =========================
    # LIKES
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        post_id INTEGER NOT NULL,

        UNIQUE(user_id, post_id),

        FOREIGN KEY(user_id)
        REFERENCES users(id),

        FOREIGN KEY(post_id)
        REFERENCES posts(id)

    )
    """)

    # =========================
    # CONNECTIONS / TOKENS
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,

        token_code TEXT UNIQUE,

        status TEXT DEFAULT 'pendente',

        created_at TEXT,

        FOREIGN KEY(sender_id)
        REFERENCES users(id),

        FOREIGN KEY(receiver_id)
        REFERENCES users(id)

    )
    """)

    # =========================
    # CHAT PRIVADO
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS private_messages (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,

        content TEXT,

        media_path TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(sender_id)
        REFERENCES users(id),

        FOREIGN KEY(receiver_id)
        REFERENCES users(id)

    )
    """)

    # =========================
    # CONQUISTAS
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS achievements (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        title TEXT NOT NULL,

        description TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )
    """)

    #==========================
    # Sl talvez tabela messages
    #==========================
    
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS messages (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        content TEXT,

        media_path TEXT,

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)

    )

    """)

    # =========================
    # NOTIFICATIONS
    # =========================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS notifications (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        message TEXT NOT NULL,

        lida INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # =========================
    # FOLLOWERS
    # =========================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS followers (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        follower_id INTEGER NOT NULL,

        following_id INTEGER NOT NULL,

        UNIQUE(follower_id, following_id),

        FOREIGN KEY(follower_id)
        REFERENCES users(id),

        FOREIGN KEY(following_id)
        REFERENCES users(id)

    )

    """)

    # =========================
    # GERAR RCIDs FALTANDO
    # =========================

    users = cursor.execute("""

        SELECT id
        FROM users

        WHERE rcid IS NULL

    """).fetchall()

    for user in users:

        rcid = "RC-" + str(uuid.uuid4())[:8].upper()

        cursor.execute("""

            UPDATE users
            SET rcid = ?

            WHERE id = ?

        """, (

            rcid,
            user[0]

        ))

    conn.commit()
    conn.close()

    print("Base de dados pronta!")
