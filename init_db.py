import sqlite3

conexion = sqlite3.connect("mascotas.db")
cursor = conexion.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
)

# Aquí insertas la actualización que deseas hacer
nuevo_descripcion = "Nuevo texto de descripción"
nuevo_foto = "nueva_foto.jpg"
id_mascota = 1

cursor.execute(
    """
    UPDATE mascotas
    SET descripcion = ?, foto = ?
    WHERE id = ?
    """,
    (nuevo_descripcion, nuevo_foto, id_mascota),
)

cursor.execute(
    "SELECT id, nombre, descripcion, ubicacion, contacto, foto, aprobado, usuario_id, found FROM mascotas"
)
datos = cursor.fetchall()
for fila in datos:
    print(fila)


conexion.commit()
conexion.close()


print("Base de datos creada correctamente.")
