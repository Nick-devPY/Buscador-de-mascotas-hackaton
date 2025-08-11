# Importar Flask-Login y utilidades
from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
import os

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mascotas-perdidas"

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

login_manager.login_message = "Por favor, inicie sesión"
login_manager.login_message_category = "info"  # Categoría para usar con flash

# Carpeta donde se guardarán las imágenes
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Ruta para mostrar el formulario
@app.route("/reportar", methods=["GET", "POST"])
@login_required
def reportar():
    if request.method == "POST":
        # 1️⃣ Recibir datos del formulario
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        ubicacion = request.form["ubicacion"]
        contacto = request.form["contacto"]

        # 2️⃣ Procesar imagen (si se sube)
        foto = request.files["foto"]
        nombre_foto = None
        if foto and foto.filename != "":
            nombre_foto = foto.filename
            ruta_foto = os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto)
            foto.save(ruta_foto)  # Guarda la imagen físicamente en /static/uploads/

        # 3️⃣ Guardar en base de datos con aprobado = 0
        conn = sqlite3.connect("mascotas.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mascotas (nombre, descripcion, ubicacion, contacto, usuario_id, foto, aprobado, found)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """,
            (nombre, descripcion, ubicacion, contacto, current_user.id, nombre_foto),
        )
        conn.commit()
        conn.close()

        # 4️⃣ Redirigir al inicio después de enviar
        flash("Mascota reportada correctamente. Espera aprobación.")
        return redirect(url_for("index"))

    # Si es GET → mostrar formulario
    return render_template("reportar.html")


@app.route("/")
def index():
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, descripcion, ubicacion, contacto, foto, aprobado, usuario_id, found FROM mascotas WHERE aprobado=1"
    )
    mascotas = cursor.fetchall()
    conn.close()
    return render_template("index.html", mascotas=mascotas)


@app.route("/admin")
def admin():
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, descripcion, ubicacion, contacto, foto FROM mascotas WHERE aprobado = 0"
    )
    pendientes = cursor.fetchall()
    conn.close()
    return render_template("admin.html", pendientes=pendientes)


@app.route("/aprobar/<int:id>")
def aprobar(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE mascotas SET aprobado = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Reporte aprobado correctamente.")
    return redirect(url_for("admin"))


@app.route("/rechazar/<int:id>")
def rechazar(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mascotas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Reporte eliminado correctamente.")
    return redirect(url_for("admin"))


@app.route("/encontrada/<int:id>", methods=["POST"])
@login_required
def encontrada(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT usuario_id FROM mascotas WHERE id = ?", (id,))
    fila = cursor.fetchone()
    if fila is None:
        flash("Solo el usuario que reportó puede marcar como encontrada.")
        return redirect(url_for("index"))
    usuario_id = fila[0]
    if str(usuario_id) != current_user.id:
        abort(403)  # No autorizado
    cursor.execute("UPDATE mascotas SET found = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Mascota marcada como encontrada, gracias por tu ayuda.", "success")
    return redirect(url_for("index"))


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = str(id)
        self.username = username
        self.password = password


def get_db():
    return sqlite3.connect("mascotas.db")


@login_manager.user_loader
def load_user(user_id):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT id, username, password FROM usuarios WHERE id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    if row:
        return User(*row)
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT id FROM usuarios WHERE username=?", (username,))
        if cur.fetchone():
            flash("Usuario ya existe")
            return redirect(url_for("register"))

        hashed_pwd = generate_password_hash(password)
        cur.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            (username, hashed_pwd),
        )
        con.commit()
        con.close()

        flash("Registro exitoso, ahora puedes iniciar sesión")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()
        cur.execute(
            "SELECT id, username, password FROM usuarios WHERE username=?", (username,)
        )
        row = cur.fetchone()
        con.close()

        if row and check_password_hash(row[2], password):
            user = User(*row)
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Credenciales inválidas")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión correctamente.")
    return redirect(url_for("index"))


@app.errorhandler(403)
def permiso_denegado(e):
    return (
        render_template(
            "403.html", mensaje="No tienes permisos para realizar esta acción."
        ),
        403,
    )


@app.route("/mis_reportes")
@login_required
def mis_reportes():
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, descripcion, ubicacion, contacto, foto, aprobado, usuario_id, found "
        "FROM mascotas WHERE usuario_id = ?",
        (current_user.id,),
    )
    reportes = cursor.fetchall()
    conn.close()
    return render_template("mis_reportes.html", reportes=reportes)


# Editar reporte - mostrar formulario y procesar edición
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_reporte(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT usuario_id, nombre, descripcion, ubicacion, contacto FROM mascotas WHERE id = ?",
        (id,),
    )
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        abort(404)

    usuario_id = fila[0]
    if str(usuario_id) != current_user.id:
        conn.close()
        abort(403)

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        ubicacion = request.form["ubicacion"]
        contacto = request.form["contacto"]

        cursor.execute(
            """
            UPDATE mascotas
            SET nombre = ?, descripcion = ?, ubicacion = ?, contacto = ?
            WHERE id = ?
        """,
            (nombre, descripcion, ubicacion, contacto, id),
        )
        conn.commit()
        conn.close()

        flash("Reporte actualizado correctamente.")
        return redirect(url_for("mis_reportes"))

    # GET: mostrar formulario con datos actuales
    conn.close()
    return render_template(
        "editar_reporte.html",
        mascota={
            "id": id,
            "nombre": fila[1],
            "descripcion": fila[2],
            "ubicacion": fila[3],
            "contacto": fila[4],
        },
    )


# Eliminar reporte
@app.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_reporte(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()

    cursor.execute("SELECT usuario_id FROM mascotas WHERE id = ?", (id,))
    fila = cursor.fetchone()
    if fila is None:
        conn.close()
        abort(404)

    usuario_id = fila[0]
    if str(usuario_id) != current_user.id:
        conn.close()
        abort(403)

    cursor.execute("DELETE FROM mascotas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Reporte eliminado correctamente.")
    return redirect(url_for("mis_reportes"))

