from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "mascotas-perdidas"

# Carpeta donde se guardarán las imágenes
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Ruta para mostrar el formulario
@app.route("/reportar", methods=["GET", "POST"])
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
            INSERT INTO mascotas (nombre, descripcion, ubicacion, contacto, foto, aprobado)
            VALUES (?, ?, ?, ?, ?, 0)
        """,
            (nombre, descripcion, ubicacion, contacto, nombre_foto),
        )
        conn.commit()
        conn.close()

        # 4️⃣ Redirigir al inicio después de enviar
        flash("Mascota reportada correctamente. Espera aprobación.")
        return redirect(url_for("inicio"))

    # Si es GET → mostrar formulario
    return render_template("reportar.html")


@app.route("/")
def inicio():
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mascotas WHERE aprobado = 1")
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
def encontrada(id):
    conn = sqlite3.connect("mascotas.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mascotas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Mascota marcada como encontrada, gracias por tu ayuda.")
    return redirect(url_for("inicio"))
