import sqlite3

conexion = sqlite3.connect("mascotas.db")
cursor = conexion.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS mascotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    ubicacion TEXT NOT NULL,
    contacto TEXT NOT NULL,
    foto TEXT,
    aprobado INTEGER DEFAULT 0
)
"""
)

conexion.commit()
conexion.close()

print("Base de datos creada correctamente.")
