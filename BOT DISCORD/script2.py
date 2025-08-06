import sqlite3

TABLAS_ESPERADAS = {
    "players",
    "matches",
    "match_players",
    "achievements",
    "player_achievements"
}

def verificar_tablas(db_path="amongus.db"):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas_encontradas = {fila[0] for fila in cursor.fetchall()}

    print("🔍 Tablas encontradas en la base de datos:")
    for t in sorted(tablas_encontradas):
        print(f"  - {t}")

    faltantes = TABLAS_ESPERADAS - tablas_encontradas

    if not faltantes:
        print("\n✅ Todas las tablas necesarias están presentes.")
    else:
        print("\n❌ Faltan las siguientes tablas necesarias:")
        for tabla in faltantes:
            print(f"  - {tabla}")

if __name__ == "__main__":
    verificar_tablas()
    
def add_antimvp_column():
    conn = sqlite3.connect("amongus.db")
    cursor = conn.cursor()

    try:
        # Intenta agregar la columna si no existe
        cursor.execute("ALTER TABLE players ADD COLUMN antimvp_count INTEGER DEFAULT 0")
        print("✅ Columna 'antimvp_count' añadida correctamente.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ La columna 'antimvp_count' ya existe. No se hizo ningún cambio.")
        else:
            print("❌ Error al modificar la tabla:", e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_antimvp_column()
