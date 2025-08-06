import sqlite3

try:
    from main5 import insert_achievements
except ImportError:
    print("No se pudo importar insert_achievements desde main5.py. Asegúrate que el archivo y la función existan.")
    # Opcional: define aquí una versión mínima para continuar
    def insert_achievements():
        print("Función insert_achievements no disponible.")

def actualizar_base_datos():
    conn = sqlite3.connect("amongus.db")
    cursor = conn.cursor()

    # Lista de columnas a agregar: (tabla, columna, tipo y default)
    columnas_a_agregar = [
        ("matches", "mvp_id", "INTEGER"),
        ("players", "mvp_count", "INTEGER DEFAULT 0"),
        ("players", "win_streak", "INTEGER DEFAULT 0"),
        ("players", "survive_count", "INTEGER DEFAULT 0"),
        ("players", "total_kills", "INTEGER DEFAULT 0"),
        ("players", "votes_correct", "INTEGER DEFAULT 0"),
        ("players", "sabotage_wins", "INTEGER DEFAULT 0"),
        ("players", "first_death_count", "INTEGER DEFAULT 0"),
        ("players", "total_losses", "INTEGER DEFAULT 0"),
        ("players", "score", "INTEGER DEFAULT 0"),
        ("players", "wins_no_death", "INTEGER DEFAULT 0"),
        ("players", "mvp_streak", "INTEGER DEFAULT 0"),
        ("players", "fast_vote_win", "BOOLEAN DEFAULT 0"),
        ("players", "fast_sabotage_win", "BOOLEAN DEFAULT 0"),
        ("players", "solo_impostor_wins", "INTEGER DEFAULT 0"),
        ("players", "detective_wins", "INTEGER DEFAULT 0"),
        ("players", "max_single_game_score", "INTEGER DEFAULT 0"),
        ("players", "total_played_minutes", "INTEGER DEFAULT 0"),
    ]

    for tabla, columna, tipo in columnas_a_agregar:
        try:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo};")
            print(f"Columna '{columna}' agregada a '{tabla}'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"La columna '{columna}' ya existe en '{tabla}'.")
            else:
                print(f"Error al agregar la columna '{columna}' en '{tabla}': {e}")

    conn.commit()
    conn.close()

def verificar_logros():
    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM achievements")
        for (name,) in cursor.fetchall():
            print(name)  # Aquí deberían verse los emojis

if __name__ == "__main__":
    actualizar_base_datos()
    insert_achievements()
    verificar_logros()
    print("Base de datos actualizada correctamente.")
