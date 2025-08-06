import os
import discord
from discord.ext import commands
import sqlite3
from datetime import datetime
from discord.ui import Button, View, Select
from discord import Interaction, SelectOption
from functools import partial
import asyncio
import emojis

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

# ----------------------------
# FUNCIÓN PARA CALCULAR PUNTOS
# ----------------------------
def calculate_points(was_impostor: bool, won: bool, win_method: str, first_death: bool, double_points: bool = False) -> int:
    """Calcula los puntos según las reglas especificadas"""
    points = 0
    if was_impostor:
        if won:
            if win_method == "kill":
                points = 5
            elif win_method == "vote":
                points = 6
            elif win_method == "sabotage":
                points = 8
            else:
                points = 5  # Por defecto
        else:
            points = -2  # Derrota impostor
    else:
        if won:
            points = 3 + (2 if first_death else 0)  # Victoria + bonus primera muerte
        else:
            points = -4  # Derrota tripulante

    if double_points:
        points *= 2

    return points

# ----------------------------
# BASE DE DATOS AMONG US (MODIFICADA)
# ----------------------------
def init_db():
    with sqlite3.connect("amongus.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                impostor_wins INTEGER DEFAULT 0,
                crewmate_wins INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                last_played TIMESTAMP,
                mvp_count INTEGER DEFAULT 0,
                antimvp_count INTEGER DEFAULT 0
                

                     
                     
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                impostors_win BOOLEAN NOT NULL,
                win_method TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_minutes INTEGER DEFAULT 0,
                mvp_id INTEGER,  -- Nuevo campo para MVP
                FOREIGN KEY (mvp_id) REFERENCES players(player_id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS match_players (
                match_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                was_impostor BOOLEAN NOT NULL,
                won BOOLEAN NOT NULL,
                first_death BOOLEAN DEFAULT 0,
                FOREIGN KEY (match_id) REFERENCES matches(match_id),
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                criteria TEXT UNIQUE
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player_achievements (
                player_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,
                date_earned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (player_id, achievement_id),
                FOREIGN KEY (player_id) REFERENCES players(player_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
            )
        """)

import sqlite3


init_db()
def insert_achievements():
    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        achievements_list = [
            ("🏆 Primera victoria", "Gana tu primera partida", "first_win"),
            ("🌟 MVP frecuente", "Ser MVP 10 veces", "mvp_10"),
            ("🔪 Impostor experto", "Gana 20 veces como impostor", "impostor_20_wins"),
            ("⭐ Tripulante resistente", "Gana 20 veces como tripulante", "crewmate_20_wins"),
            ("💯 Racha de victorias", "Gana 5 partidas seguidas", "win_streak_5"),
            ("👍 Superviviente", "Sobrevive a 10 partidas sin morir", "survive_10"),
            ("🔇 Asesino silencioso", "Consigue 10 kills como impostor", "kills_10"),
            ("💯 Votación perfecta", "Gana una partida votando correctamente", "perfect_vote"),
            ("🕐 Saboteador maestro", "Gana 10 partidas por sabotaje", "sabotage_10"),
            ("🕊️ Primera muerte", "Ser la primera muerte en 5 partidas", "first_death_5"),
            ("👟 Jugador activo", "Participa en 50 partidas", "played_50"),
            ("💯 Puntuación alta", "Alcanza 100 puntos en total", "score_100"),
            ("🖇️ Tripulación unida", "Gana una partida sin muertes", "no_death_win"),
            ("🌟 MVP consecutivo", "Ser MVP en 3 partidas seguidas", "mvp_streak_3"),
            ("🕐 Votación rápida", "Gana una partida con votación en menos de 5 minutos", "fast_vote_win"),
            ("🕐 Sabotaje rápido", "Completa un sabotaje en menos de 1 minuto", "fast_sabotage"),
            ("🥷🏻 Impostor solitario", "Gana una partida siendo el único impostor", "solo_impostor_win"),
            ("🕵🏻 Detective experto", "Gana 10 partidas como tripulante encontrando al impostor", "detective_10"),
            ("💯 Puntaje perfecto", "Obtén 20 puntos en una sola partida", "perfect_score"),
            ("👍 Veterano", "Juega durante más de 2 horas en una sala", "played_100h")
        ]
        for name, desc, criteria in achievements_list:
            cursor.execute("""
                INSERT OR REPLACE INTO achievements (name, description, criteria)
                VALUES (?, ?, ?)
            """, (name, desc, criteria))
        conn.commit()

import sqlite3

def check_and_award_achievements(player_id):
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        player = cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,)).fetchone()
        if not player:
            return

        achievements = cursor.execute("SELECT * FROM achievements").fetchall()

        points_per_achievement = {
            "first_win": 20,
            "mvp_10": 15,
            "impostor_20_wins": 20,
            "crewmate_20_wins": 20,
            "win_streak_5": 18,
            "survive_10": 15,
            "kills_10": 17,
            "perfect_vote": 12,
            "sabotage_10": 15,
            "first_death_5": 10,
            "played_50": 12,
            "score_100": 15,
            "no_death_win": 20,
            "mvp_streak_3": 18,
            "fast_vote_win": 14,
            "fast_sabotage": 14,
            "solo_impostor_win": 20,
            "detective_10": 17,
            "perfect_score": 20,
            "played_100h": 15,
        }

        for achievement in achievements:
            has_achievement = cursor.execute("""
                SELECT 1 FROM player_achievements WHERE player_id = ? AND achievement_id = ?
            """, (player_id, achievement['achievement_id'])).fetchone()
            if has_achievement:
                continue

            award = False
            c = achievement['criteria']

            # Criterios básicos
            if c == "first_win" and (player['total_wins'] or 0) >= 1:
                award = True
            elif c == "mvp_10" and (player['mvp_count'] or 0) >= 10:
                award = True
            elif c == "impostor_20_wins" and (player['impostor_wins'] or 0) >= 20:
                award = True
            elif c == "crewmate_20_wins" and (player['crewmate_wins'] or 0) >= 20:
                award = True

            # Criterios extendidos
            elif c == "win_streak_5" and (player['win_streak'] or 0) >= 5:
                award = True
            elif c == "survive_10" and (player['survive_count'] or 0) >= 10:
                award = True
            elif c == "kills_10" and (player['total_kills'] or 0) >= 10:
                award = True
            elif c == "perfect_vote" and (player['votes_correct'] or 0) >= 1:
                award = True
            elif c == "sabotage_10" and (player['sabotage_wins'] or 0) >= 10:
                award = True
            elif c == "first_death_5" and (player['first_death_count'] or 0) >= 5:
                award = True
            elif c == "played_50":
                total_games = (player['total_wins'] or 0) + (player['total_losses'] or 0)
                if total_games >= 50:
                    award = True
            elif c == "score_100" and (player['score'] or 0) >= 100:
                award = True
            elif c == "no_death_win" and (player['wins_no_death'] or 0) >= 1:
                award = True
            elif c == "mvp_streak_3" and (player['mvp_streak'] or 0) >= 3:
                award = True
            elif c == "fast_vote_win" and player['fast_vote_win']:
                award = True
            elif c == "fast_sabotage" and player['fast_sabotage_win']:
                award = True
            elif c == "solo_impostor_win" and (player['solo_impostor_wins'] or 0) >= 1:
                award = True
            elif c == "detective_10" and (player['detective_wins'] or 0) >= 10:
                award = True
            elif c == "perfect_score" and (player['max_single_game_score'] or 0) >= 20:
                award = True
            elif c == "played_100h":
                if (player['total_played_minutes'] or 0) >= 100 * 60:
                    award = True

            if award:
                cursor.execute("""
                    INSERT INTO player_achievements (player_id, achievement_id)
                    VALUES (?, ?)
                """, (player_id, achievement['achievement_id']))

                extra_points = points_per_achievement.get(c, 10)
                cursor.execute("""
                    UPDATE players SET score = score + ? WHERE player_id = ?
                """, (extra_points, player_id))

                conn.commit()
                print(f"Jugador {player_id} obtuvo el logro: {achievement['name']} y recibió {extra_points} puntos extra.")
    if not os.path.exists("amongus.db"):
    print("🟠 Base de datos no encontrada, creando una nueva...")
    init_db()
    insert_achievements()
else:
    print("🟢 Base de datos encontrada")
#######################################
# COMANDO PARA AGREGAR PUNTOS MANUALMENTE
#######################################
@bot.command()
@commands.has_permissions(administrator=True)
async def addpoints(ctx, user: discord.Member, puntos: int, *, motivo: str = "Sin motivo"):
    if puntos <= 0:
        await ctx.send("❌ La cantidad de puntos a agregar debe ser mayor que cero.")
        return

    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO players (player_id, username)
            VALUES (?, ?)
            ON CONFLICT(player_id) DO UPDATE SET username = excluded.username
        """, (user.id, user.display_name))
        cursor.execute("""
            UPDATE players SET score = score + ? WHERE player_id = ?
        """, (puntos, user.id))
        conn.commit()

    await ctx.send(f"✅ Se agregaron **{puntos} puntos** a {user.display_name}.\n📝 Motivo: {motivo}")

#######################################
# COMANDO PARA RESTAR PUNTOS MANUALMENTE
#######################################
@bot.command()
@commands.has_permissions(administrator=True)
async def removepoints(ctx, user: discord.Member, puntos: int, *, motivo: str = "Sin motivo"):
    if puntos <= 0:
        await ctx.send("❌ La cantidad de puntos a eliminar debe ser mayor que cero.")
        return

    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO players (player_id, username)
            VALUES (?, ?)
            ON CONFLICT(player_id) DO UPDATE SET username = excluded.username
        """, (user.id, user.display_name))
        cursor.execute("SELECT score FROM players WHERE player_id = ?", (user.id,))
        result = cursor.fetchone()
        current = result[0] if result and result[0] is not None else 0
        new_score = max(0, current - puntos)
        cursor.execute("""
            UPDATE players SET score = ? WHERE player_id = ?
        """, (new_score, user.id))
        conn.commit()

    await ctx.send(f"⚠️ Se eliminaron **{puntos} puntos** de {user.display_name}.\n📝 Motivo: {motivo}\nPuntuación actual: {new_score}")

@bot.command()
async def partidas(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author

    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.match_id, m.start_time, m.impostors_win, m.win_method, mp.was_impostor, mp.won, mp.first_death
            FROM match_players mp
            JOIN matches m ON mp.match_id = m.match_id
            WHERE mp.player_id = ?
            ORDER BY m.start_time DESC
            LIMIT 10
        """, (user.id,))
        partidas = cursor.fetchall()

    if not partidas:
        await ctx.send(f"No se encontraron partidas registradas para {user.display_name}.")
        return

    embed = discord.Embed(
        title=f"Últimas partidas de {user.display_name}",
        color=discord.Color.blue()
    )
    for partida in partidas:
        fecha = partida["start_time"]
        resultado = "Ganó" if partida["won"] else "Perdió"
        rol = "Impostor" if partida["was_impostor"] else "Tripulante"
        victoria_impostor = "Impostores" if partida["impostors_win"] else "Tripulantes"
        metodo = partida["win_method"] or "Desconocido"
        primera_muerte = "Sí" if partida["first_death"] else "No"
        
        embed.add_field(
            name=f"Partida #{partida['match_id']} - {fecha}",
            value=(
                f"Rol: **{rol}**\n"
                f"Resultado: **{resultado}**\n"
                f"Ganó el bando: **{victoria_impostor}** vía **{metodo}**\n"
                f"Primera muerte: {primera_muerte}"
            ),
            inline=False
        )

    await ctx.send(embed=embed)

# ----------------------------
# FUNCIONES AUXILIARES (MODIFICADAS)
# ----------------------------
async def get_lobby_members(ctx):
    """Obtiene jugadores válidos en el canal de voz (incluyendo bots si es necesario)"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        return None
    
    voice_channel = ctx.author.voice.channel
    return [member for member in voice_channel.members if member.voice and not member.voice.afk]

async def register_match(guild_id, impostors_win, players_data, win_method=None, duration=0, mvp_id=None, double_points=False):
    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO matches (guild_id, impostors_win, win_method, duration_minutes, mvp_id)
            VALUES (?, ?, ?, ?, ?)
        """, (guild_id, impostors_win, win_method, duration, mvp_id))
        
        match_id = cursor.lastrowid
        
        for player_id, username, was_impostor, won, first_death in players_data:
            points = calculate_points(was_impostor, won, win_method, first_death, double_points)


            
            cursor.execute("""
                INSERT OR IGNORE INTO players (player_id, username)
                VALUES (?, ?)
            """, (player_id, username))
            
            if won:
                cursor.execute("""
                    UPDATE players SET
                        total_wins = total_wins + 1,
                        impostor_wins = impostor_wins + ?,
                        crewmate_wins = crewmate_wins + ?,
                        score = score + ?,
                        last_played = CURRENT_TIMESTAMP
                    WHERE player_id = ?
                """, (1 if was_impostor else 0, 0 if was_impostor else 1, points, player_id))
            else:
                cursor.execute("""
                    UPDATE players SET
                        total_losses = total_losses + 1,
                        score = score + ?,
                        last_played = CURRENT_TIMESTAMP
                    WHERE player_id = ?
                """, (points, player_id))
            
            cursor.execute("""
                INSERT INTO match_players (match_id, player_id, was_impostor, won, first_death)
                VALUES (?, ?, ?, ?, ?)
            """, (match_id, player_id, was_impostor, won, first_death))
        
        # Actualizar contador de MVP si existe
        if mvp_id:
            cursor.execute("""
                UPDATE players SET mvp_count = mvp_count + 1 WHERE player_id = ?
            """, (mvp_id,))
        
        conn.commit()
    for player_id, *_ in players_data:
        check_and_award_achievements(player_id)

    
    return match_id


# ----------------------------
# FUNCIÓN PARA OBTENER EMBED DE PARTIDA (REUTILIZABLE)
# ----------------------------
async def get_match_embed(guild, match_id: int):
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        
        match = conn.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match:
            return None
        
        players = conn.execute("""
            SELECT 
                mp.player_id,
                p.username,
                mp.was_impostor,
                mp.won,
                mp.first_death,
                p.score AS total_score
            FROM match_players mp
            JOIN players p ON mp.player_id = p.player_id
            WHERE mp.match_id = ?
        """, (match_id,)).fetchall()
        if not players:
            return None
        
        embed = discord.Embed(
            title=f"🎮 Detalles de Partida #{match_id}",
            color=0xff0000 if match['impostors_win'] else 0x00ff00,
            timestamp=datetime.strptime(match['start_time'], "%Y-%m-%d %H:%M:%S")
        )
        
        winner = f"{emojis.emoji_impostor} IMPOSTORES" if match['impostors_win'] else f"{emojis.emoji_tripulante} TRIPULACIÓN"
        embed.add_field(name="🏆 Ganador", value=winner, inline=True)
        
        if match['win_method']:
            method_text = {
                "kill": "🔪 Por kills",
                "vote": "🗳️ Por votación",
                "sabotage": "💣 Por sabotaje"
            }
            embed.add_field(name="Método de Victoria", value=method_text.get(match['win_method'], "Desconocido"), inline=True)
        
        if match['duration_minutes']:
            embed.add_field(name="⏱️ Duración", value=f"{match['duration_minutes']} minutos", inline=True)
        
        # Mostrar MVP
        if match['mvp_id']:
            mvp_player = conn.execute("SELECT username FROM players WHERE player_id = ?", (match['mvp_id'],)).fetchone()
            if mvp_player:
                embed.add_field(name="⭐ MVP de la partida", value=mvp_player['username'], inline=False)
        
        players_info = []
        for player in players:
            points = calculate_points(
                player['was_impostor'],
                player['won'],
                match['win_method'],
                player['first_death']
            )
            role = emojis.emoji_impostor if player['was_impostor'] else emojis.emoji_tripulante
            status = "✅ Ganó" if player['won'] else "❌ Perdió"
            fd = "💀" if player['first_death'] else ""
            
            players_info.append(
                f"{role} **{player['username']}** {fd}\n"
                f"» {status} | Puntos: **{'+' if points > 0 else ''}{points}** "
                f"(Total: {player['total_score']})"
            )
        
        embed.add_field(name=f"👥 Jugadores ({len(players)})", value="\n\n".join(players_info), inline=False)
        
        first_death = next((p for p in players if p['first_death']), None)
        if first_death:
            embed.set_footer(text=f"💀 Primera muerte: {first_death['username']}")
        
        return embed


# ----------------------------
# VISTAS INTERACTIVAS (MODIFICADAS)
# ----------------------------
class AmongUsView(View):
    def __init__(self, players: list[discord.Member], owner_id: int, double_points: bool = False):  # Asegurar tipo
        super().__init__(timeout=120)
        self.players = players
        self.selected_impostors = []
        self.win_method = None
        self.first_death = None
        self.impostors_win = None
        self.mvp = None
        self.antimvp = None
        self.owner_id = owner_id
        self.double_points = double_points

        
        # Selector de impostores con validación
        if not players:
            raise ValueError("¡No hay jugadores en el canal de voz!")
            
        impostor_select = Select(
            placeholder="Selecciona 1-3 impostores",
            min_values=1,
            max_values=min(3, len(players)),  # No permitir más impostores que jugadores
            options=[SelectOption(
                label=player.display_name[:100],  # Discord limita a 100 caracteres
                value=str(player.id),
                description=f"ID: {player.id}"
            ) for player in players]
        )
        impostor_select.callback = self.select_impostors
        self.add_item(impostor_select)
        self.double_points_btn = Button(
            label="Activar puntos dobles" if not self.double_points else "Desactivar puntos dobles",
            style=discord.ButtonStyle.secondary
        )
        self.double_points_btn.callback = self.toggle_double_points
        self.add_item(self.double_points_btn)
        cancel_btn = Button(label="❌ Cancelar partida", style=discord.ButtonStyle.danger)
        cancel_btn.callback = self.cancel
        self.add_item(cancel_btn)

    async def toggle_double_points(self, interaction: Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("⛔ Solo el creador puede cambiar esta opción.", ephemeral=True)
            return

        self.double_points = not self.double_points
        self.double_points_btn.label = "Activar puntos dobles" if not self.double_points else "Desactivar puntos dobles"
        await interaction.response.edit_message(view=self)

    async def cancel(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "⛔ Solo el creador de la partida puede cancelarla.",
                ephemeral=True
            )
            return

        await interaction.message.delete()
        self.stop() 

    async def select_impostors(self, interaction: Interaction):
        self.selected_impostors = [int(id) for id in interaction.data['values']]
        
        # Filtrar tripulantes (excluyendo impostores)
        self.crewmates = [p for p in self.players if p.id not in self.selected_impostors]
        
        # Validar que haya tripulantes disponibles
        if not self.crewmates:
            await interaction.response.edit_message(
                content="❌ Error: No hay tripulantes disponibles para seleccionar como primera muerte",
                view=None
            )
            self.stop()
            return
        
        # Mostrar selector de primera muerte SOLO con tripulantes
        death_view = View(timeout=60)
        
        death_select = Select(
            placeholder="Selecciona la primera muerte (tripulante)",
            min_values=1,
            max_values=1,
            options=[SelectOption(
                label=player.display_name[:100],
                value=str(player.id),
            ) for player in self.crewmates]  # Solo tripulantes
        )
        death_select.callback = self.select_first_death
        death_view.add_item(death_select)
        
        await interaction.response.send_message(
            "¿Quién fue la primera muerte? (solo tripulantes)",
            view=death_view,
            ephemeral=True
        )
    
    async def select_first_death(self, interaction: Interaction):
        self.first_death = int(interaction.data['values'][0])
        
        # Mostrar botones de resultado
        confirm_view = View(timeout=60)
        
        # Botones de resultado
        crew_win_btn = Button(style=discord.ButtonStyle.success, label="Tripulación gana", emoji="👨‍🚀")
        crew_win_btn.callback = partial(self.record_result, impostors_win=False)
        confirm_view.add_item(crew_win_btn)
        
        impostor_win_btn = Button(style=discord.ButtonStyle.danger, label="Impostores ganan", emoji="👿")
        impostor_win_btn.callback = partial(self.select_win_method, impostors_win=True)
        confirm_view.add_item(impostor_win_btn)
        
        await interaction.response.edit_message(
            content="¿Quién ganó?",
            view=confirm_view
        )
    
    async def select_win_method(self, interaction: Interaction, impostors_win: bool):
        self.impostors_win = impostors_win
        
        # Mostrar selector de método de victoria para impostores
        method_view = View(timeout=60)
        
        method_select = Select(
            placeholder="¿Cómo ganaron los impostores?",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(label="Por kills", value="kill"),
                SelectOption(label="Por votación", value="vote"),
                SelectOption(label="Por sabotaje", value="sabotage")
            ]
        )
        method_select.callback = partial(self.finalize_win_method, impostors_win=impostors_win)
        method_view.add_item(method_select)
        
        await interaction.response.edit_message(
            content="Selecciona el método de victoria de los impostores:",
            view=method_view
        )
    
    async def finalize_win_method(self, interaction: Interaction, impostors_win: bool):
        self.win_method = interaction.data['values'][0]
        await self.record_result(interaction, impostors_win)
    
    
    async def record_result(self, interaction: Interaction, impostors_win: bool):
        # Preparar datos de jugadores
        players_data = []
        for player in self.players:
            was_impostor = player.id in self.selected_impostors
            won = (was_impostor and impostors_win) or (not was_impostor and not impostors_win)
            first_death = (player.id == self.first_death)
            players_data.append((player.id, player.display_name, was_impostor, won, first_death))
        
        self.impostors_win = impostors_win
        
        # Mostrar selector de MVP antes de registrar partida
        mvp_view = View(timeout=60)
        
        mvp_select = Select(
            placeholder="Selecciona el MVP de la partida",
            min_values=1,
            max_values=1,
            options=[SelectOption(
                label=player.display_name[:100],
                value=str(player.id)
            ) for player in self.players]
        )
        mvp_select.callback = self.finalize_mvp
        mvp_view.add_item(mvp_select)
        
        await interaction.response.edit_message(
            content="Selecciona el MVP de la partida:",
            view=mvp_view
        )
    
    async def finalize_mvp(self, interaction: Interaction):
        self.mvp = int(interaction.data['values'][0])
        self.antimvp = None  # Valor por defecto

        class AntiMVPView(View):
            def __init__(self, parent):
                super().__init__(timeout=60)
                self.parent = parent
                self.selected_id = None

                self.select = Select(
                    placeholder="Selecciona al Anti-MVP (opcional)",
                    min_values=1,
                    max_values=1,
                    options=[
                        SelectOption(label=player.display_name[:100], value=str(player.id))
                        for player in self.parent.players
                    ]
                )
                self.select.callback = self.select_antimvp
                self.add_item(self.select)

            async def select_antimvp(self, interaction: Interaction):
                self.selected_id = int(interaction.data['values'][0])
                await interaction.response.send_message(f"❌ Anti-MVP seleccionado: <@{self.selected_id}>", ephemeral=True)

            @discord.ui.button(label="⏭️ Saltar", style=discord.ButtonStyle.gray)
            async def skip(self, interaction: Interaction, button: Button):
                self.parent.antimvp = None
                await self.finalize(interaction)

            @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.green)
            async def confirm(self, interaction: Interaction, button: Button):
                self.parent.antimvp = self.selected_id
                await self.finalize(interaction)

            async def finalize(self, interaction: Interaction):
                await self.parent.finalize_antimvp(interaction)

        await interaction.response.edit_message(
            content="❌ ¿Quién fue el Anti-MVP de la partida? (opcional)",
            view=AntiMVPView(self)
        )

    async def finalize_antimvp(self, interaction: Interaction):
        players_data = []
        for player in self.players:
            was_impostor = player.id in self.selected_impostors
            won = (was_impostor and self.impostors_win) or (not was_impostor and not self.impostors_win)
            first_death = (player.id == self.first_death)
            players_data.append((player.id, player.display_name, was_impostor, won, first_death))

        # Registrar partida
        match_id = await register_match(
            interaction.guild.id,
            self.impostors_win,
            players_data,
            self.win_method,
            mvp_id=self.mvp,
            double_points=self.double_points
        )




    # 🔻 Solo si se eligió Anti-MVP
        if self.antimvp is not None:
            with sqlite3.connect("amongus.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT score FROM players WHERE player_id = ?", (self.antimvp,))
                score = cursor.fetchone()[0] or 0
                new_score = max(score - 1, 0)
                cursor.execute("""
                    UPDATE players 
                    SET 
                        score = ?, 
                        antimvp_count = antimvp_count + 1
                    WHERE player_id = ?
                """, (new_score, self.antimvp))
                conn.commit()


        # Embed final
        embed = discord.Embed(
            title=f"🎮 Partida #{match_id} registrada",
            description=f"**{'IMPOSTORES' if self.impostors_win else 'TRIPULACIÓN'} ganan**",
            color=0xff0000 if self.impostors_win else 0x00ff00
        )

        impostor_names = [p.display_name for p in self.players if p.id in self.selected_impostors]
        embed.add_field(name="Impostores", value="\n".join(impostor_names), inline=False)

        method_text = {
            "kill": "Por kills (👿 +5 puntos)",
            "vote": "Por votación (🗳️ +6 puntos)",
            "sabotage": "Por sabotaje (💣 +8 puntos)"
        }
        if self.impostors_win and self.win_method:
            embed.add_field(name="Método de victoria", value=method_text.get(self.win_method, "Desconocido"), inline=False)

        mvp_player = next((p for p in self.players if p.id == self.mvp), None)
        antimvp_player = next((p for p in self.players if p.id == self.antimvp), None)
        if mvp_player:
            embed.add_field(name="⭐ MVP de la partida", value=mvp_player.display_name, inline=False)
        if self.antimvp is not None and antimvp_player:
            embed.add_field(name="❌ Anti-MVP", value=f"{antimvp_player.display_name} (-1 punto)", inline=False)

        first_death_player = next((p for p in self.players if p.id == self.first_death), None)
        if first_death_player:
            embed.add_field(name="Primera muerte", value=first_death_player.display_name, inline=False)

        # Puntos por jugador
        points_summary = []
        for player in self.players:
            was_impostor = player.id in self.selected_impostors
            won = (was_impostor and self.impostors_win) or (not was_impostor and not self.impostors_win)
            first_death = (player.id == self.first_death)
            points = calculate_points(was_impostor, won, self.win_method, first_death)
            if self.antimvp == player.id:
                points -= 1
            points_summary.append(f"{player.display_name}: {'+' if points > 0 else ''}{points} puntos")

        embed.add_field(name="📊 Puntos obtenidos", value="\n".join(points_summary), inline=False)
        embed.set_footer(text=f"Partida registrada por {interaction.user.display_name}")

        await interaction.response.edit_message(content="✅ Partida registrada", embed=embed, view=None)
        self.stop()



# ----------------------------
# BOTÓN PARA VER DETALLES DE PARTIDA
# ----------------------------
class MatchButton(Button):
    def __init__(self, match_id, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.match_id = match_id
    
    async def callback(self, interaction: Interaction):
        # Obtener los detalles de la partida
        embed = await get_match_embed(interaction.guild, self.match_id)
        
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"❌ No se encontró la partida #{self.match_id}",
                ephemeral=True
            )

# ----------------------------
# COMANDOS DEL BOT
# ----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def amongus(ctx, double_points: bool = False):
    """Inicia una nueva partida de Among Us (solo admins)"""
    lobby_members = await get_lobby_members(ctx)
    if not lobby_members:
        return await ctx.send("🔇 Debes estar en un canal de voz con jugadores")

    if len(lobby_members) < 4:
        return await ctx.send("👥 Se necesitan al menos 4 jugadores")

    view = AmongUsView(lobby_members, ctx.author.id, double_points=double_points)
    await ctx.send(
        "🎮 **Configurar Partida de Among Us**\n"
        "Selecciona los impostores (1-3):",
        view=view
    )

@bot.command()
async def topVictorias(ctx, rol: str):
    rol = rol.lower()
    if rol not in ['impostor', 'tripulante']:
        await ctx.send(
            "Por favor, especifica `impostor` o `tripulante` como argumento, por ejemplo:\n`$topVictorias impostor`"
        )
        return

    import sqlite3
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        jugadores = conn.execute("""
            SELECT
                p.username,
                SUM(CASE WHEN mp.was_impostor = 1 THEN 1 ELSE 0 END) AS impostor_partidas,
                SUM(CASE WHEN mp.was_impostor = 1 AND mp.won = 1 THEN 1 ELSE 0 END) AS impostor_victorias,
                SUM(CASE WHEN mp.was_impostor = 0 THEN 1 ELSE 0 END) AS tripu_partidas,
                SUM(CASE WHEN mp.was_impostor = 0 AND mp.won = 1 THEN 1 ELSE 0 END) AS tripu_victorias
            FROM players p
            JOIN match_players mp ON p.player_id = mp.player_id
            GROUP BY p.player_id
        """).fetchall()

    stats = []
    for j in jugadores:
        if rol == 'impostor':
            imp_j = j['impostor_partidas'] or 0
            if imp_j < 8:
                continue
            vict_imp = j['impostor_victorias'] or 0
            porc = (vict_imp / imp_j) * 100 if imp_j else 0
            stats.append((j['username'], porc, f"{vict_imp}/{imp_j}"))
        else:  # tripulante
            trp_j = j['tripu_partidas'] or 0
            if trp_j < 50:
                continue
            vict_trp = j['tripu_victorias'] or 0
            porc = (vict_trp / trp_j) * 100 if trp_j else 0
            stats.append((j['username'], porc, f"{vict_trp}/{trp_j}"))

    if not stats:
        await ctx.send(f"No hay jugadores con al menos 20 partidas como {rol}.")
        return

    stats.sort(key=lambda x: -x[1])  # Ordenar de mayor a menor porcentaje

    # Paginación: dividir en grupos de 10
    por_pagina = 10
    paginas = [stats[i:i+por_pagina] for i in range(0, len(stats), por_pagina)]
    total_paginas = len(paginas)

    def crear_embed(pagina_idx):
        embed = discord.Embed(
            title=f"🏆 Top victorias como {rol.capitalize()}",
            description=f"Página {pagina_idx+1} de {total_paginas}",
            color=0x27ae60
        )
        for i, (nombre, porc, detalles) in enumerate(paginas[pagina_idx], start=pagina_idx * por_pagina + 1):
            icono = emojis.emoji_impostor if rol == "impostor" else emojis.emoji_tripulante
            embed.add_field(
                name=f"{i}. {nombre}",
                value=f"{icono} **{porc:.1f}%** ({detalles})",
                inline=False
            )
        return embed

    class Navegacion(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)  # Timeout en 60 segundos
            self.pagina_actual = 0

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
        async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.pagina_actual > 0:
                self.pagina_actual -= 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)
            else:
                await interaction.response.defer()  # Evitar error si no se puede retroceder

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
        async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.pagina_actual < total_paginas - 1:
                self.pagina_actual += 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)
            else:
                await interaction.response.defer()  # Evitar error si no se puede avanzar

    await ctx.send(embed=crear_embed(0), view=Navegacion())
@bot.command()
async def stats(ctx, user: discord.Member = None):
    target = user or ctx.author
    
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        player_stats = conn.execute("SELECT * FROM players WHERE player_id = ?", (target.id,)).fetchone()
        if not player_stats:
            return await ctx.send(f"ℹ️ {target.display_name} no tiene estadísticas registradas")
        
        total_games = player_stats['total_wins'] + player_stats['total_losses']
        win_rate = (player_stats['total_wins'] / total_games) * 100 if total_games > 0 else 0
        
        last_match = conn.execute("""
            SELECT m.match_id, m.impostors_win, m.start_time, mp.was_impostor, mp.won, m.mvp_id
            FROM matches m
            JOIN match_players mp ON m.match_id = mp.match_id
            WHERE mp.player_id = ?
            ORDER BY m.start_time DESC
            LIMIT 1
        """, (target.id,)).fetchone()
    
    embed = discord.Embed(
        title=f"📊 Estadísticas de {target.display_name}",
        color=0x7289DA
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Campo nuevo: Win Rate
    embed.add_field(
        name="📈 Win Rate",
        value=f"{win_rate:.1f}% de victorias",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Victorias Totales",
        value=(
            f"{player_stats['total_wins']}\n"
            f"{emojis.emoji_impostor} Como impostor: {player_stats['impostor_wins']}\n"
            f"{emojis.emoji_tripulante} Como tripulación: {player_stats['crewmate_wins']}"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⭐ Puntuación Total",
        value=f"{player_stats['score']} puntos",
        inline=False
    )
    
    embed.add_field(
        name="🌟 MVPs obtenidos",
        value=f"{player_stats['mvp_count']} MVP(s)",
        inline=False
    )
    
    if last_match:
        role = f"{emojis.emoji_impostor} Impostor" if last_match['was_impostor'] else f"{emojis.emoji_tripulante} Tripulación"
        result = "✅ Ganó" if last_match['won'] else "❌ Perdió"
        mvp_text = ""
        if last_match['mvp_id'] == target.id:
            mvp_text = "\n🌟 Fue MVP en esta partida"
        
        embed.add_field(
            name="📅 Última partida",
            value=(
                f"Partida #{last_match['match_id']}\n"
                f"Rol: {role}\n"
                f"Resultado: {result}\n"
                f"Fecha: {last_match['start_time'][:10]}"
                f"{mvp_text}"
            ),
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command()
async def logros(ctx, user: discord.Member = None):
    # Aquí va tu código para mostrar logros
    target = user or ctx.author
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        achievements = conn.execute("""
            SELECT a.name, a.description, pa.date_earned
            FROM player_achievements pa
            JOIN achievements a ON pa.achievement_id = a.achievement_id
            WHERE pa.player_id = ?
        """, (target.id,)).fetchall()
    
    if not achievements:
        return await ctx.send(f"ℹ️ {target.display_name} no tiene logros aún.")
    
    embed = discord.Embed(
        title=f"🏅 Logros de {target.display_name}",
        color=0xFFD700
    )
    for ach in achievements:
        embed.add_field(
            name=ach['name'],
            value=f"{ach['description']}\n🗓️ Obtenido: {ach['date_earned'][:10]}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def logros_lista(ctx):
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        achievements = conn.execute("""
            SELECT name, description FROM achievements ORDER BY name
        """).fetchall()
    
    if not achievements:
        return await ctx.send("ℹ️ No hay logros definidos en la base de datos.")
    
    embed = discord.Embed(
        title="📜 Lista de logros disponibles",
        color=0x00ffff
    )
    for ach in achievements:
        embed.add_field(name=ach['name'], value=ach['description'], inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def tiene_logro(ctx, logro_nombre: str, user: discord.Member = None):
    target = user or ctx.author
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        logro = conn.execute("""
            SELECT achievement_id FROM achievements WHERE name = ?
        """, (logro_nombre,)).fetchone()
        if not logro:
            return await ctx.send(f"❌ El logro '{logro_nombre}' no existe.")
        
        tiene = conn.execute("""
            SELECT 1 FROM player_achievements WHERE player_id = ? AND achievement_id = ?
        """, (target.id, logro['achievement_id'])).fetchone()
    
    if tiene:
        await ctx.send(f"✅ {target.display_name} tiene el logro '{logro_nombre}'.")
    else:
        await ctx.send(f"❌ {target.display_name} no tiene el logro '{logro_nombre}'.")

@bot.command()
async def topMVP(ctx):
    """Muestra el ranking de jugadores por cantidad de MVPs"""
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        jugadores = conn.execute("""
            SELECT 
                username,
                mvp_count,
                score,
                total_wins,
                total_losses
            FROM players
            ORDER BY mvp_count DESC, score DESC
        """).fetchall()

    if not jugadores or all(j['mvp_count'] == 0 for j in jugadores):
        return await ctx.send("📭 No hay jugadores con MVPs aún.")

    por_pagina = 10
    paginas = [jugadores[i:i+por_pagina] for i in range(0, len(jugadores), por_pagina)]
    total_paginas = len(paginas)
    pagina_actual = 0

    def crear_embed(pagina_idx):
        embed = discord.Embed(
            title="🌟 Ranking de MVPs",
            description=f"Página {pagina_idx + 1}/{total_paginas}",
            color=0xFFD700
        )
        for idx, jugador in enumerate(paginas[pagina_idx], start=pagina_idx * por_pagina + 1):
            if jugador['mvp_count'] == 0:
                continue
            embed.add_field(
                name=f"{idx}. {jugador['username']}",
                value=(
                    f"🌟 MVPs: **{jugador['mvp_count']}**\n"
                    f"⭐ Puntos: {jugador['score']}\n"
                    f"🏆 Partidas ganadas: {jugador['total_wins']} | ❌ Perdidas: {jugador['total_losses']}"
                ),
                inline=False
            )
        return embed

    class Navegacion(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.pagina_actual = 0

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
        async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.pagina_actual > 0:
                self.pagina_actual -= 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)
            else:
                await interaction.response.defer()

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
        async def siguiente(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.pagina_actual < total_paginas - 1:
                self.pagina_actual += 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)
            else:
                await interaction.response.defer()

    await ctx.send(embed=crear_embed(pagina_actual), view=Navegacion())

@bot.command()
async def topPuntos(ctx):
    """Muestra el ranking de jugadores por puntos (score)"""
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        jugadores = conn.execute("""
            SELECT 
                username,
                score,
                total_wins,
                total_losses,
                (total_wins + total_losses) AS total_partidas
            FROM players
            ORDER BY score DESC
        """).fetchall()

    if not jugadores:
        return await ctx.send("📭 No hay jugadores registrados aún.")

    por_pagina = 10
    paginas = [jugadores[i:i + por_pagina] for i in range(0, len(jugadores), por_pagina)]
    total_paginas = len(paginas)
    pagina_actual = 0

    def crear_embed(pagina_idx):
        embed = discord.Embed(
            title="⭐ TOP de jugadores por puntos",
            description=f"Página {pagina_idx + 1}/{total_paginas}",
            color=0xffd700
        )
        for idx, jugador in enumerate(paginas[pagina_idx], start=pagina_idx * por_pagina + 1):
            embed.add_field(
                name=f"{idx}. {jugador['username']}",
                value=(
                    f"⭐ Puntos: **{jugador['score']}**\n"
                    f"🎮 Partidas: {jugador['total_partidas']} (🏆 {jugador['total_wins']} / ❌ {jugador['total_losses']})"
                ),
                inline=False
            )
        return embed

    class Navegacion(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.pagina_actual = 0

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
        async def anterior(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual > 0:
                self.pagina_actual -= 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
        async def siguiente(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual < total_paginas - 1:
                self.pagina_actual += 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)

    await ctx.send(embed=crear_embed(pagina_actual), view=Navegacion())



@bot.command()
async def partidasTotales(ctx):
    """Muestra TODAS las partidas de todos los usuarios con paginación"""
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        partidas = conn.execute("""
            SELECT 
                m.match_id,
                m.start_time,
                m.impostors_win,
                m.win_method,
                COUNT(mp.player_id) AS total_jugadores
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.match_id
            WHERE m.guild_id = ?
            GROUP BY m.match_id
            ORDER BY m.start_time DESC
        """, (ctx.guild.id,)).fetchall()

    if not partidas:
        return await ctx.send("📭 No hay partidas registradas aún.")

    partidas_por_pagina = 5
    paginas = [partidas[i:i+partidas_por_pagina] for i in range(0, len(partidas), partidas_por_pagina)]

    class PaginacionGlobal(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.pagina_actual = 0
            self.total_paginas = len(paginas)

        async def update_embed(self, interaction):
            embed = discord.Embed(
                title="🌍 Partidas registradas en el servidor",
                description=f"Página {self.pagina_actual + 1}/{self.total_paginas}",
                color=0x00bfff
            )
            for match in paginas[self.pagina_actual]:
                result = "👿 Impostores" if match["impostors_win"] else "👨‍🚀 Tripulación"
                metodo = match["win_method"] or "Desconocido"
                embed.add_field(
                    name=f"🎮 Partida #{match['match_id']} - {match['start_time'][:10]}",
                    value=(
                        f"Resultado: **{result}**\n"
                        f"Método: **{metodo}**\n"
                        f"Jugadores: **{match['total_jugadores']}**"
                    ),
                    inline=False
                )
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
        async def anterior(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual > 0:
                self.pagina_actual -= 1
                await self.update_embed(interaction)

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
        async def siguiente(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual < self.total_paginas - 1:
                self.pagina_actual += 1
                await self.update_embed(interaction)

    view = PaginacionGlobal()
    primer_embed = discord.Embed(
        title="🌍 Partidas registradas en el servidor",
        description=f"Página 1/{len(paginas)}",
        color=0x00bfff
    )
    for match in paginas[0]:
        result = "👿 Impostores" if match["impostors_win"] else "👨‍🚀 Tripulación"
        metodo = match["win_method"] or "Desconocido"
        primer_embed.add_field(
            name=f"🎮 Partida #{match['match_id']} - {match['start_time'][:10]}",
            value=(
                f"Resultado: **{result}**\n"
                f"Método: **{metodo}**\n"
                f"Jugadores: **{match['total_jugadores']}**"
            ),
            inline=False
        )

    await ctx.send(embed=primer_embed, view=view)

@bot.command()
async def totalPartidas(ctx):
    """Ranking global paginado de jugadores por partidas jugadas"""
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        jugadores = conn.execute("""
            SELECT 
                p.player_id,
                pl.username,
                COUNT(mp.match_id) AS partidas_jugadas
            FROM match_players mp
            JOIN players pl ON mp.player_id = pl.player_id
            LEFT JOIN players p ON p.player_id = mp.player_id
            GROUP BY mp.player_id
            ORDER BY partidas_jugadas DESC
        """).fetchall()

    if not jugadores:
        return await ctx.send("📭 No hay jugadores registrados aún.")

    por_pagina = 10
    paginas = [jugadores[i:i + por_pagina] for i in range(0, len(jugadores), por_pagina)]
    total_paginas = len(paginas)
    pagina_actual = 0

    def crear_embed(pagina_idx):
        embed = discord.Embed(
            title="📊 Ranking de Partidas Jugadas",
            description=f"Página {pagina_idx + 1}/{total_paginas}",
            color=0x3498db
        )
        for idx, jugador in enumerate(paginas[pagina_idx], start=pagina_idx * por_pagina + 1):
            embed.add_field(
                name=f"{idx}. {jugador['username']}",
                value=f"🎮 Partidas jugadas: **{jugador['partidas_jugadas']}**",
                inline=False
            )
        return embed

    class Navegacion(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.pagina_actual = 0

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey)
        async def anterior(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual > 0:
                self.pagina_actual -= 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey)
        async def siguiente(self, interaction: discord.Interaction, button: Button):
            if self.pagina_actual < total_paginas - 1:
                self.pagina_actual += 1
                await interaction.response.edit_message(embed=crear_embed(self.pagina_actual), view=self)

    await ctx.send(embed=crear_embed(pagina_actual), view=Navegacion())





@bot.command()
async def puntos(ctx, usuario: discord.Member = None):
    """Muestra los puntos acumulados de un jugador"""
    target = usuario or ctx.author
    
    with sqlite3.connect("amongus.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM players WHERE player_id = ?", (target.id,))
        result = cursor.fetchone()
        
    if not result or result[0] is None:
        return await ctx.send(f"ℹ️ {target.display_name} no tiene puntuación registrada")
    
    embed = discord.Embed(
        title=f"⭐ Puntos de {target.display_name}",
        description=f"**Puntuación acumulada:** {result[0]} puntos",
        color=0xFFD700
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Explicación del sistema de puntos
    embed.add_field(
        name="Sistema de Puntos",
        value=(
            f"{emojis.emoji_tripulante} **Tripulante Gana:** +3 puntos\n"
            f"{emojis.emoji_tripulante} **Primera Muerte (si gana):** +2 puntos extra\n"
            f"{emojis.emoji_tripulante} **Tripulante Pierde:** -4 puntos\n"
            f"{emojis.emoji_impostor} **Impostor Gana (kills):** +5 puntos\n"
            f"{emojis.emoji_impostor} **Impostor Gana (votación):** +6 puntos\n"
            f"{emojis.emoji_impostor} **Impostor Gana (sabotaje):** +8 puntos\n"
            f"{emojis.emoji_impostor} **Impostor Pierde:** -2 puntos"
        ),
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def partida(ctx, match_id: int):
    """Muestra detalles completos de una partida específica"""
    embed = await get_match_embed(ctx.guild, match_id)
    if embed:
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ No se encontró la partida #{match_id}")

@bot.command()
async def todas_partidas(ctx, filtro: str = None):
    """Muestra todas las partidas con botones para ver detalles"""
    # Consulta base con filtros
    base_query = """
        SELECT m.match_id, m.impostors_win, m.start_time, 
               COUNT(mp.player_id) as total_jugadores
        FROM matches m
        JOIN match_players mp ON m.match_id = mp.match_id
        WHERE m.guild_id = ?
    """
    params = [ctx.guild.id]
    
    # Filtros
    if filtro:
        if "impostor" in filtro.lower():
            base_query += " AND m.impostors_win = 1"
        elif "tripulacion" in filtro.lower() or "tripulación" in filtro.lower():
            base_query += " AND m.impostors_win = 0"
        elif "reciente" in filtro.lower():
            base_query += " AND date(m.start_time) >= date('now', '-7 days')"
    
    base_query += " GROUP BY m.match_id ORDER BY m.start_time DESC"
    
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        matches = conn.execute(base_query, params).fetchall()

    if not matches:
        return await ctx.send("📭 No hay partidas registradas" + (f" con filtro '{filtro}'" if filtro else ""))

    # Dividir en páginas de 5 partidas
    pages = [matches[i:i + 5] for i in range(0, len(matches), 5)]
    current_page = 0

    # Función para generar el embed con botones
    def create_embed(page):
        embed = discord.Embed(
            title=f"📜 Todas las partidas ({len(matches)} totales)",
            description=f"Página {page + 1}/{len(pages)}" + (f"\nFiltro: `{filtro}`" if filtro else ""),
            color=0x5865F2
        )
        
        # Vista con botones
        view = View(timeout=120)
        
        for match in pages[page]:
            result = "👿" if match['impostors_win'] else "👨‍🚀"
            date_str = match['start_time'][:10]
            
            embed.add_field(
                name=f"🎮 Partida #{match['match_id']} - {date_str}",
                value=(
                    f"**Resultado:** {result}\n"
                    f"**Jugadores:** {match['total_jugadores']}\n"
                    f"⬇️ Haz clic en el botón para ver detalles"
                ),
                inline=False
            )
            
            # Añadir botón para esta partida
            btn = MatchButton(
                match_id=match['match_id'],
                label=f"Ver #{match['match_id']}"
            )
            view.add_item(btn)
        
        # Botones de navegación si hay múltiples páginas
        if len(pages) > 1:
            if page > 0:
                prev_btn = Button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="prev")
                async def prev_callback(interaction):
                    nonlocal current_page
                    current_page = page - 1
                    embed, view = create_embed(current_page)
                    await interaction.response.edit_message(embed=embed, view=view)
                prev_btn.callback = prev_callback
                view.add_item(prev_btn)
            
            if page < len(pages) - 1:
                next_btn = Button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="next")
                async def next_callback(interaction):
                    nonlocal current_page
                    current_page = page + 1
                    embed, view = create_embed(current_page)
                    await interaction.response.edit_message(embed=embed, view=view)
                next_btn.callback = next_callback
                view.add_item(next_btn)
        
        return embed, view
    
    # Enviar primera página
    embed, view = create_embed(current_page)
    message = await ctx.send(embed=embed, view=view)

@bot.command()
async def partidas_usuario(ctx, usuario: discord.Member = None):
    """Muestra TODAS las partidas de un usuario con paginación"""
    target = usuario or ctx.author
    
    with sqlite3.connect("amongus.db") as conn:
        conn.row_factory = sqlite3.Row
        
        # Obtener todas las partidas del usuario
        matches = conn.execute("""
            SELECT 
                m.match_id, 
                m.impostors_win,
                m.start_time,
                mp.was_impostor,
                mp.won
            FROM match_players mp
            JOIN matches m ON mp.match_id = m.match_id
            WHERE mp.player_id = ?
            ORDER BY m.start_time DESC
        """, (target.id,)).fetchall()

    if not matches:
        return await ctx.send(f"📭 {target.display_name} no tiene partidas registradas")

    # Dividir en páginas de 5 partidas
    matches_per_page = 5
    pages = [matches[i:i + matches_per_page] for i in range(0, len(matches), matches_per_page)]
    total_pages = len(pages)
    current_page = 0

    # Función para crear el Embed
    def create_embed(page):
        embed = discord.Embed(
            title=f"🎮 Partidas de {target.display_name} (Página {page + 1}/{total_pages})",
            color=0x00ff00 if matches[0]['won'] else 0xff0000
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        for match in pages[page]:
            embed.add_field(
                name=f"#{match['match_id']} - {match['start_time'][:10]}",
                value=(
                    f"**Rol:** {'🕵️ Impostor' if match['was_impostor'] else '👨‍🚀 Tripulación'}\n"
                    f"**Resultado:** {'✅ Ganó' if match['won'] else '❌ Perdió'}\n"
                    f"**Ganador global:** {emojis.emoji_impostor if match['impostors_win'] else emojis.emoji_tripulante}"
                ),
                inline=False
            )
        return embed

    # Vista con botones de navegación
    class PaginationView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.current_page = 0

        @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.grey)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.current_page > 0:
                self.current_page -= 1
                await interaction.response.edit_message(embed=create_embed(self.current_page))

        @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.grey)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.current_page < total_pages - 1:
                self.current_page += 1
                await interaction.response.edit_message(embed=create_embed(self.current_page))

    # Enviar primera página
    view = PaginationView()
    await ctx.send(embed=create_embed(current_page), view=view)


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user.name}")
    print(f"🌐 En {len(bot.guilds)} servidor(es)")

    # Aquí agregas la impresión de comandos registrados
    print("Comandos registrados:")
    for cmd in bot.commands:
        print(f"- {cmd.name}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="partidas de Among Us | $help"
        )
    )


# ----------------------------
# EVENTOS DEL BOT
# ----------------------------

# ----------------------------
# EJECUCIÓN
# ----------------------------


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("🔴 Error: Token inválido")
    except Exception as e:
        print(f"🔴 Error inesperado: {str(e)}")
