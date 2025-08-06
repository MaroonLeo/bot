import sqlite3

def hacer_copia_seguridad(origen, destino):
    # Conectar a la base de datos original
    conn_origen = sqlite3.connect(origen)
    # Crear la base de datos destino (o conectar si existe)
    conn_destino = sqlite3.connect(destino)
    # Usar el método backup para copiar los datos
    conn_origen.backup(conn_destino)
    # Cerrar conexiones
    conn_destino.close()
    conn_origen.close()
    print(f"Copia de seguridad creada en {destino}")

if __name__ == "__main__":
    hacer_copia_seguridad("amongus.db", "amongus_backup.db")
