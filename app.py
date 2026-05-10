from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "123"

print("🔥 IA MEDIA FIXADA 🔥")

BANCO = "novo_escola.db"

# =========================
# CRIAR BANCO
# =========================

def criar_banco():

    conn = sqlite3.connect(BANCO)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        presenca TEXT DEFAULT 'Faltou',
        nota REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

criar_banco()

# =========================
# LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = request.form["user"]

        if user:

            session["user"] = user

            return redirect("/dashboard")

    return render_template("login.html")

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" not in session:
        return redirect("/")

    resposta_ia = ""

    conn = sqlite3.connect(BANCO)

    cursor = conn.cursor()

    # -------------------------
    # ADICIONAR ALUNO
    # -------------------------

    if request.method == "POST":

        if "nome" in request.form:

            nome = request.form["nome"]

            cursor.execute(
                "INSERT INTO alunos(nome) VALUES(?)",
                (nome,)
            )

            conn.commit()

    # -------------------------
    # MARCAR PRESENÇA
    # -------------------------

        if "presenca" in request.form:

            aluno_id = request.form["presenca"]

            cursor.execute(
                "UPDATE alunos SET presenca='Presente' WHERE id=?",
                (aluno_id,)
            )

            conn.commit()

    # -------------------------
    # SALVAR NOTA
    # -------------------------

        if "nota" in request.form:

            aluno_id = request.form["aluno_id"]

            nota = request.form["nota"]

            cursor.execute(
                "UPDATE alunos SET nota=? WHERE id=?",
                (nota, aluno_id)
            )

            conn.commit()

    # -------------------------
    # IA
    # -------------------------

        if "pergunta" in request.form:

            pergunta = request.form["pergunta"].lower()

            # TOTAL

            if "quantos alunos" in pergunta:

                cursor.execute(
                    "SELECT COUNT(*) FROM alunos"
                )

                total = cursor.fetchone()[0]

                resposta_ia = f"Tem {total} alunos cadastrados."

            # PRESENÇA

            elif "presença" in pergunta:

                cursor.execute(
                    "SELECT nome, presenca FROM alunos"
                )

                dados = cursor.fetchall()

                resposta_ia = str(dados)

            # MÉDIA

            elif "média" in pergunta or "media" in pergunta:

                cursor.execute(
                    "SELECT AVG(nota) FROM alunos"
                )

                media = cursor.fetchone()[0]

                if media is None:
                    media = 0

                resposta_ia = f"A média da turma é {media:.1f}"

            else:

                resposta_ia = "Ainda estou aprendendo..."

    # =========================
    # BUSCAR ALUNOS
    # =========================

    cursor.execute("SELECT * FROM alunos")

    alunos = cursor.fetchall()

    conn.close()

    # =========================
    # ESTATÍSTICAS
    # =========================

    total = len(alunos)

    presentes = 0

    soma_notas = 0

    for aluno in alunos:

        if aluno[2] == "Presente":
            presentes += 1

        soma_notas += aluno[3]

    faltas = total - presentes

    media_turma = 0

    if total > 0:
        media_turma = soma_notas / total

    return render_template(
        "dashboard.html",
        alunos=alunos,
        resposta_ia=resposta_ia,
        total=total,
        presentes=presentes,
        faltas=faltas,
        media_turma=round(media_turma, 1)
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":

    app.run(debug=True)
