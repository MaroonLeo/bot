emoji_mayor = "<:bullet5:1171142205470154935>"
emoji_impostor = "<:impostor:1169179777442250832>"
emoji_tripulante = "<:tripulante:1169186796610011196>"
import sqlite3

def verificar_emojis():
    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM achievements")
        nombres = cursor.fetchall()
        if not nombres:
            print("No hay logros en la base de datos.")
            return
        print("Nombres de logros con emojis:")
        for (name,) in nombres:
            print(repr(name))

if __name__ == "__main__":
    verificar_emojis()
