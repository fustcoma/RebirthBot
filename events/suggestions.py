
import sqlite3
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

SUGGESTIONS_ENABLED = True

SUGGESTIONS_CHANNEL_ID = 1540809266485661836

LIKE_EMOJI = "👍"
DISLIKE_EMOJI = "👎"


# ============================================================
# BASE DE DATOS
# ============================================================

DATABASE_PATH = (
    Path(__file__).parent.parent
    / "database"
    / "suggestions.db"
)


# ============================================================
# COLORES
# ============================================================

SUGGESTION_COLOR = discord.Color.blurple()
ACCEPTED_COLOR = discord.Color.green()
REJECTED_COLOR = discord.Color.red()
CONSIDER_COLOR = discord.Color.gold()


# ============================================================
# ESTADOS
# ============================================================

STATUS_PENDING = "PENDING"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_REJECTED = "REJECTED"
STATUS_CONSIDER = "CONSIDER"


# ============================================================
# BASE DE DATOS - FUNCIONES
# ============================================================

def get_connection():

    DATABASE_PATH.parent.mkdir(
        exist_ok=True
    )

    return sqlite3.connect(
        DATABASE_PATH
    )


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            suggestion TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            moderator_id INTEGER,
            created_at INTEGER NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# OBTENER SUGERENCIA
# ============================================================

def get_suggestion(
    suggestion_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            guild_id,
            channel_id,
            message_id,
            user_id,
            suggestion,
            status,
            moderator_id,
            created_at
        FROM suggestions
        WHERE id = ?
        """,
        (
            suggestion_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ============================================================
# CAMBIAR ESTADO
# ============================================================

def set_status(
    suggestion_id,
    status,
    moderator_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE suggestions
        SET
            status = ?,
            moderator_id = ?
        WHERE id = ?
        """,
        (
            status,
            moderator_id,
            suggestion_id
        )
    )

    changed = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return changed


# ============================================================
# ESTADO → TEXTO + COLOR
# ============================================================

def get_status_data(
    status
):

    if status == STATUS_ACCEPTED:

        return (
            "🟢 ACEPTADA",
            ACCEPTED_COLOR
        )

    if status == STATUS_REJECTED:

        return (
            "🔴 RECHAZADA",
            REJECTED_COLOR
        )

    if status == STATUS_CONSIDER:

        return (
            "🟡 EN CONSIDERACIÓN",
            CONSIDER_COLOR
        )

    return (
        "⚪ PENDIENTE",
        SUGGESTION_COLOR
    )


# ============================================================
# CONTAR REACCIONES
# ============================================================

def get_reaction_count(
    message,
    emoji
):

    for reaction in message.reactions:

        if str(reaction.emoji) == emoji:

            # El bot tiene su propia reacción,
            # por lo tanto no la contamos.

            count = reaction.count - 1

            return max(
                count,
                0
            )

    return 0


# ============================================================
# CREAR EMBED
# ============================================================

def create_suggestion_embed(
    suggestion_id,
    author,
    suggestion,
    likes=0,
    dislikes=0,
    status=STATUS_PENDING
):

    status_text, color = get_status_data(
        status
    )

    embed = discord.Embed(
        color=color
    )

    embed.description = (
        f"# 💡 SUGERENCIA #{suggestion_id}\n\n"

        f"👤 **Autor:** {author.mention}\n\n"

        f"💬 **Sugerencia:**\n"
        f"{suggestion}\n\n"

        f"👍 **{likes}**     "
        f"👎 **{dislikes}**\n\n"

        f"{status_text}"
    )

    embed.set_footer(
        text=(
            "RebirthMC Network • Sugerencias"
        )
    )

    return embed


# ============================================================
# CREAR TEXT INFORMATIU
# ============================================================

def create_suggestion_info_embed():

    embed = discord.Embed(
        color=SUGGESTION_COLOR
    )

    embed.description = (
        "💡 **SUGERIMENTS**\n\n"

        "Tens una idea per millorar "
        "**RebirthMC Network**? Aquest és el lloc!\n\n"

        "Escriu la teva proposta i serà publicada "
        "aquí perquè la comunitat pugui votar-la.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📝 **COM PROPOSAR UNA IDEA**\n\n"

        "Utilitza **`/sugerencias`** i escriu la teva "
        "proposta de manera clara.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🗳️ **COM VOTAR**\n\n"

        "👍 — **M'agrada / A favor**\n"
        "👎 — **No m'agrada / En contra**\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📊 **ESTATS DELS SUGGERIMENTS**\n\n"

        "⚪ **PENDENT** — Encara no ha estat revisat.\n\n"

        "🟡 **EN CONSIDERACIÓ** — L'equip està "
        "valorant la idea.\n\n"

        "🟢 **ACCEPTAT** — La proposta ha estat acceptada.\n\n"

        "🔴 **REBUTJAT** — La proposta ha estat rebutjada.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "⚠️ **IMPORTANT**\n\n"

        "Intenta que els suggeriments siguin respectuosos, "
        "útils i relacionats amb el servidor.\n\n"

        "Els suggeriments poden ser revisats i modificats "
        "d'estat per l'equip de moderació."
    )

    embed.set_footer(
        text=(
            "RebirthMC Network • Sistema de suggeriments"
        )
    )

    return embed


# ============================================================
# ACTUALIZAR MENSAJE
# ============================================================

async def update_suggestion_message(
    message,
    suggestion_id,
    author,
    suggestion,
    status
):

    likes = get_reaction_count(
        message,
        LIKE_EMOJI
    )

    dislikes = get_reaction_count(
        message,
        DISLIKE_EMOJI
    )

    embed = create_suggestion_embed(
        suggestion_id=suggestion_id,
        author=author,
        suggestion=suggestion,
        likes=likes,
        dislikes=dislikes,
        status=status
    )

    await message.edit(
        embed=embed
    )


# ============================================================
# COG
# ============================================================

class Suggestions(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        init_database()

        self.ready_done = False


    # ========================================================
    # READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(
        self
    ):

        if self.ready_done:

            return

        self.ready_done = True

        print(
            "💡 Sistema de sugerencias cargado."
        )


    # ========================================================
    # ON MESSAGE
    #
    # Si alguien escribe directamente en el canal de
    # sugerencias, eliminamos el mensaje y
    # avisamos al usuario por privado.
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        if not SUGGESTIONS_ENABLED:

            return

        if message.channel.id != SUGGESTIONS_CHANNEL_ID:

            return

        if message.author.bot:

            return

        try:

            await message.delete()

        except discord.NotFound:

            return

        except discord.Forbidden:

            print(
                "❌ No tengo permisos para "
                "borrar mensajes en el canal "
                "de sugerencias."
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error borrando mensaje "
                f"de sugerencias: {error}"
            )

            return

        try:

            await message.author.send(
                "❌ **No puedes escribir directamente "
                "en este canal.**\n\n"
                "💡 Para enviar una sugerencia debes "
                "utilizar el comando "
                "**`/sugerencias`**."
            )

        except discord.Forbidden:

            pass

        except discord.HTTPException as error:

            print(
                f"❌ Error enviando el aviso "
                f"a {message.author}: {error}"
            )


    # ========================================================
    # REACCIÓN AÑADIDA
    # ========================================================

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload
    ):

        if not SUGGESTIONS_ENABLED:

            return

        if payload.channel_id != SUGGESTIONS_CHANNEL_ID:

            return

        if self.bot.user is not None:

            if payload.user_id == self.bot.user.id:

                return

        emoji = str(
            payload.emoji
        )

        if emoji not in (
            LIKE_EMOJI,
            DISLIKE_EMOJI
        ):

            return

        await self.update_from_reaction(
            payload.message_id
        )


    # ========================================================
    # REACCIÓN ELIMINADA
    # ========================================================

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload
    ):

        if not SUGGESTIONS_ENABLED:

            return

        if payload.channel_id != SUGGESTIONS_CHANNEL_ID:

            return

        emoji = str(
            payload.emoji
        )

        if emoji not in (
            LIKE_EMOJI,
            DISLIKE_EMOJI
        ):

            return

        await self.update_from_reaction(
            payload.message_id
        )


    # ========================================================
    # ACTUALIZAR DESDE REACCIÓN
    # ========================================================

    async def update_from_reaction(
        self,
        message_id
    ):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                channel_id,
                user_id,
                suggestion,
                status
            FROM suggestions
            WHERE message_id = ?
            """,
            (
                message_id,
            )
        )

        result = cursor.fetchone()

        connection.close()

        if result is None:

            return

        (
            suggestion_id,
            channel_id,
            user_id,
            suggestion_text,
            status
        ) = result

        channel = self.bot.get_channel(
            channel_id
        )

        if channel is None:

            try:

                channel = await self.bot.fetch_channel(
                    channel_id
                )

            except Exception as error:

                print(
                    f"❌ Error obteniendo canal: "
                    f"{error}"
                )

                return

        try:

            message = await channel.fetch_message(
                message_id
            )

        except discord.NotFound:

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error obteniendo mensaje: "
                f"{error}"
            )

            return

        guild = message.guild

        if guild is None:

            return

        member = guild.get_member(
            user_id
        )

        if member is None:

            try:

                member = await guild.fetch_member(
                    user_id
                )

            except Exception:

                class MentionMember:

                    def __init__(
                        self,
                        user_id
                    ):

                        self.mention = (
                            f"<@{user_id}>"
                        )

                member = MentionMember(
                    user_id
                )

        try:

            await update_suggestion_message(
                message,
                suggestion_id,
                member,
                suggestion_text,
                status
            )

        except Exception as error:

            print(
                f"❌ Error actualizando "
                f"sugerencia #{suggestion_id}: "
                f"{error}"
            )


    # ========================================================
    # /SUGERENCIAS
    # ========================================================

    @app_commands.command(
        name="sugerencias",
        description="Envía una sugerencia."
    )
    @app_commands.describe(
        sugerencia=(
            "La sugerencia que quieres proponer."
        )
    )
    async def sugerencias(
        self,
        interaction: discord.Interaction,
        sugerencia: str
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        if not SUGGESTIONS_ENABLED:

            await interaction.followup.send(
                "❌ El sistema de sugerencias "
                "está desactivado.",
                ephemeral=True
            )

            return

        sugerencia = sugerencia.strip()

        if not sugerencia:

            await interaction.followup.send(
                "❌ Debes escribir una sugerencia.",
                ephemeral=True
            )

            return

        if len(sugerencia) > 2000:

            await interaction.followup.send(
                "❌ La sugerencia no puede superar "
                "los **2000 caracteres**.",
                ephemeral=True
            )

            return

        if interaction.guild is None:

            await interaction.followup.send(
                "❌ Este comando solo "
                "funciona dentro de un servidor.",
                ephemeral=True
            )

            return

        channel = self.bot.get_channel(
            SUGGESTIONS_CHANNEL_ID
        )

        if channel is None:

            try:

                channel = await self.bot.fetch_channel(
                    SUGGESTIONS_CHANNEL_ID
                )

            except Exception as error:

                print(
                    f"❌ No puedo obtener el canal "
                    f"de sugerencias: {error}"
                )

                await interaction.followup.send(
                    "❌ No he podido encontrar el canal "
                    "de sugerencias.",
                    ephemeral=True
                )

                return

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO suggestions
                (
                    guild_id,
                    channel_id,
                    message_id,
                    user_id,
                    suggestion,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction.guild.id,
                    SUGGESTIONS_CHANNEL_ID,
                    0,
                    interaction.user.id,
                    sugerencia,
                    STATUS_PENDING,
                    int(time.time())
                )
            )

            suggestion_id = cursor.lastrowid

            connection.commit()
            connection.close()

        except Exception as error:

            print(
                f"❌ Error SQLite creando "
                f"sugerencia: {error}"
            )

            await interaction.followup.send(
                "❌ No he podido guardar "
                "la sugerencia.",
                ephemeral=True
            )

            return

        embed = create_suggestion_embed(
            suggestion_id,
            interaction.user,
            sugerencia,
            likes=0,
            dislikes=0,
            status=STATUS_PENDING
        )

        try:

            message = await channel.send(
                embed=embed
            )

        except Exception as error:

            print(
                f"❌ Error publicando sugerencia: "
                f"{error}"
            )

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM suggestions
                WHERE id = ?
                """,
                (
                    suggestion_id,
                )
            )

            connection.commit()
            connection.close()

            await interaction.followup.send(
                "❌ No he podido publicar "
                "la sugerencia.",
                ephemeral=True
            )

            return

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE suggestions
                SET message_id = ?
                WHERE id = ?
                """,
                (
                    message.id,
                    suggestion_id
                )
            )

            connection.commit()
            connection.close()

        except Exception as error:

            print(
                f"❌ Error guardando message_id: "
                f"{error}"
            )

        try:

            await message.add_reaction(
                LIKE_EMOJI
            )

            await message.add_reaction(
                DISLIKE_EMOJI
            )

        except discord.Forbidden:

            print(
                "❌ No tengo permisos para "
                "añadir reacciones."
            )

        except discord.HTTPException as error:

            print(
                f"❌ Error añadiendo reacciones: "
                f"{error}"
            )

        await interaction.followup.send(
            f"✅ Tu sugerencia "
            f"**#{suggestion_id}** se ha publicado en "
            f"{channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /SUGERENCIATEXT
    #
    # Publica el mensaje informativo del sistema
    # de sugerencias en el canal configurado.
    # Solo administradores.
    # ========================================================

    @app_commands.command(
        name="sugerenciatext",
        description="Publica el mensaje informativo de sugerencias."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def sugerenciatext(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        if not SUGGESTIONS_ENABLED:

            await interaction.followup.send(
                "❌ El sistema de sugerencias "
                "está desactivado.",
                ephemeral=True
            )

            return

        if interaction.guild is None:

            await interaction.followup.send(
                "❌ Este comando solo "
                "funciona dentro de un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROBAR ADMINISTRADOR
        # ----------------------------------------------------

        if not isinstance(
            interaction.user,
            discord.Member
        ):

            await interaction.followup.send(
                "❌ No se ha podido comprobar "
                "tus permisos.",
                ephemeral=True
            )

            return

        if not interaction.user.guild_permissions.administrator:

            await interaction.followup.send(
                "❌ Necesitas ser administrador "
                "para utilizar este comando.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # BUSCAR CANAL
        # ----------------------------------------------------

        channel = self.bot.get_channel(
            SUGGESTIONS_CHANNEL_ID
        )

        if channel is None:

            try:

                channel = await self.bot.fetch_channel(
                    SUGGESTIONS_CHANNEL_ID
                )

            except Exception as error:

                print(
                    f"❌ No puedo obtener el canal "
                    f"de sugerencias: {error}"
                )

                await interaction.followup.send(
                    "❌ No he podido encontrar "
                    "el canal de sugerencias.",
                    ephemeral=True
                )

                return

        # ----------------------------------------------------
        # CREAR EMBED
        # ----------------------------------------------------

        embed = create_suggestion_info_embed()

        # ----------------------------------------------------
        # PUBLICAR
        # ----------------------------------------------------

        try:

            await channel.send(
                embed=embed
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ No tengo permisos para enviar "
                "mensajes en el canal de sugerencias.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error publicando el texto "
                f"de sugerencias: {error}"
            )

            await interaction.followup.send(
                "❌ No he podido publicar "
                "el mensaje informativo.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓN
        # ----------------------------------------------------

        await interaction.followup.send(
            f"✅ El mensaje informativo de sugerencias "
            f"se ha publicado en {channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /ACCEPT
    # ========================================================

    @app_commands.command(
        name="accept",
        description="Acepta una sugerencia."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID de la sugerencia."
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        suggestion_id: int
    ):

        await self.change_status(
            interaction,
            suggestion_id,
            STATUS_ACCEPTED
        )


    # ========================================================
    # /REJECT
    # ========================================================

    @app_commands.command(
        name="reject",
        description="Rechaza una sugerencia."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID de la sugerencia."
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        suggestion_id: int
    ):

        await self.change_status(
            interaction,
            suggestion_id,
            STATUS_REJECTED
        )


    # ========================================================
    # /CONSIDER
    # ========================================================

    @app_commands.command(
        name="consider",
        description="Pone una sugerencia en consideración."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID de la sugerencia."
    )
    async def consider(
        self,
        interaction: discord.Interaction,
        suggestion_id: int
    ):

        await self.change_status(
            interaction,
            suggestion_id,
            STATUS_CONSIDER
        )


    # ========================================================
    # CAMBIAR ESTADO
    # ========================================================

    async def change_status(
        self,
        interaction,
        suggestion_id,
        new_status
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        if interaction.guild is None:

            await interaction.followup.send(
                "❌ Este comando solo "
                "funciona dentro de un servidor.",
                ephemeral=True
            )

            return

        suggestion = get_suggestion(
            suggestion_id
        )

        if suggestion is None:

            await interaction.followup.send(
                "❌ No existe esta sugerencia.",
                ephemeral=True
            )

            return

        (
            database_id,
            guild_id,
            channel_id,
            message_id,
            user_id,
            suggestion_text,
            old_status,
            old_moderator,
            created_at
        ) = suggestion

        if guild_id != interaction.guild.id:

            await interaction.followup.send(
                "❌ Esta sugerencia "
                "no pertenece a este servidor.",
                ephemeral=True
            )

            return

        success = set_status(
            suggestion_id,
            new_status,
            interaction.user.id
        )

        if not success:

            await interaction.followup.send(
                "❌ No se ha podido actualizar "
                "la sugerencia.",
                ephemeral=True
            )

            return

        channel = self.bot.get_channel(
            channel_id
        )

        if channel is None:

            try:

                channel = await self.bot.fetch_channel(
                    channel_id
                )

            except Exception as error:

                print(
                    f"❌ Error obteniendo canal: "
                    f"{error}"
                )

                await interaction.followup.send(
                    "⚠️ El estado se ha guardado en "
                    "SQLite, pero no he encontrado "
                    "el canal.",
                    ephemeral=True
                )

                return

        try:

            message = await channel.fetch_message(
                message_id
            )

        except discord.NotFound:

            await interaction.followup.send(
                "⚠️ El estado se ha guardado, pero "
                "el mensaje ya no existe.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error obteniendo mensaje: "
                f"{error}"
            )

            await interaction.followup.send(
                "⚠️ El estado se ha guardado, pero "
                "no he podido obtener el mensaje.",
                ephemeral=True
            )

            return

        member = interaction.guild.get_member(
            user_id
        )

        if member is None:

            try:

                member = await interaction.guild.fetch_member(
                    user_id
                )

            except Exception:

                class MentionMember:

                    def __init__(
                        self,
                        user_id
                    ):

                        self.mention = (
                            f"<@{user_id}>"
                        )

                member = MentionMember(
                    user_id
                )

        try:

            await update_suggestion_message(
                message,
                suggestion_id,
                member,
                suggestion_text,
                new_status
            )

        except Exception as error:

            print(
                f"❌ Error actualizando embed: "
                f"{error}"
            )

            await interaction.followup.send(
                "⚠️ El estado se ha guardado en "
                "SQLite, pero no he podido "
                "actualizar el embed.",
                ephemeral=True
            )

            return

        status_text, _ = get_status_data(
            new_status
        )

        await interaction.followup.send(
            f"✅ La sugerencia "
            f"**#{suggestion_id}** ahora está como "
            f"**{status_text}**.",
            ephemeral=True
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot
):

    await bot.add_cog(
        Suggestions(bot)
    )

