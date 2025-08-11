import sqlite3

conexion = sqlite3.connect("mascotas.db")
cursor = conexion.cursor()

try:
    cursor.execute("ALTER TABLE mascotas ADD COLUMN usuario_id INTEGER")
    print("Columna 'usuario_id' agregada.")
except sqlite3.OperationalError as e:
    print(f"Error o columna ya existe: {e}")
try:
    cursor.execute("ALTER TABLE mascotas ADD COLUMN found INTEGER DEFAULT 0")
    print("Columna 'found' agregada.")
except sqlite3.OperationalError as e:
    print(f"Error o columna 'found' ya existe: {e}")

conexion.commit()
conexion.close()
