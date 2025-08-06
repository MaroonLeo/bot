import sqlite3

def mostrar_jugadores():
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('amongus.db')

    # Crear un cursor para ejecutar comandos SQL
    cursor = conn.cursor()

    # Ejecutar la consulta SQL
    cursor.execute("SELECT player_id, username FROM players LIMIT 100")

    # Obtener todos los resultados
    resultados = cursor.fetchall()

    # Mostrar los resultados
    print("Primeros 5 jugadores en la base:")
    for fila in resultados:
        player_id, username = fila
        print(f"ID: {player_id}, Usuario: {username}")

    # Cerrar la conexión
    conn.close()

if __name__ == "__main__":
    mostrar_jugadores()
