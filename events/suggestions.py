
import sqlite3
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

SUGGESTIONS_ENABLED = True

SUGGESTIONS_CHANNEL_ID = 1540809266485661836

LIKE_EMOJI = "👍"
DISLIKE_EMOJI = "👎"


# ============================================================
# BASE DE DADES
# ============================================================

DATABASE_PATH = (
    Path(__file__).parent.parent
    / "database"
    / "suggestions.db"
)


# ============================================================
# COLORS
# ============================================================

SUGGESTION_COLOR = discord.Color.blurple()
ACCEPTED_COLOR = discord.Color.green()
REJECTED_COLOR = discord.Color.red()
CONSIDER_COLOR = discord.Color.gold()


# ============================================================
# ESTATS
# ============================================================

STATUS_PENDING = "PENDING"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_REJECTED = "REJECTED"
STATUS_CONSIDER = "CONSIDER"


# ============================================================
# DATABASE
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
# OBTENIR SUGGERIMENT
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
# CANVIAR ESTAT
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
# ESTAT → TEXT + COLOR
# ============================================================

def get_status_data(
    status
):

    if status == STATUS_ACCEPTED:

        return (
            "🟢 ACCEPTAT",
            ACCEPTED_COLOR
        )

    if status == STATUS_REJECTED:

        return (
            "🔴 REBUTJAT",
            REJECTED_COLOR
        )

    if status == STATUS_CONSIDER:

        return (
            "🟡 EN CONSIDERACIÓ",
            CONSIDER_COLOR
        )

    return (
        "⚪ PENDENT",
        SUGGESTION_COLOR
    )


# ============================================================
# COMPTAR REACCIONS
# ============================================================

def get_reaction_count(
    message,
    emoji
):

    for reaction in message.reactions:

        if str(reaction.emoji) == emoji:

            # El bot té la seva pròpia reacció,
            # per tant no la comptem.

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
        f"# 💡 SUGGERIMENT #{suggestion_id}\n\n"

        f"👤 **Autor:** {author.mention}\n\n"

        f"💬 **Suggeriment:**\n"
        f"{suggestion}\n\n"

        f"👍 **{likes}**     "
        f"👎 **{dislikes}**\n\n"

        f"{status_text}"
    )

    embed.set_footer(
        text=(
            "RebirthMC Network • Suggeriments"
        )
    )

    return embed


# ============================================================
# ACTUALITZAR MISSATGE
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
            "💡 Sistema de suggeriments carregat."
        )


    # ========================================================
    # ON MESSAGE
    #
    # Si algú escriu directament al canal de
    # suggeriments, eliminem el missatge i
    # avisem l'usuari per privat.
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        # ----------------------------------------------------
        # SISTEMA ACTIVAT?
        # ----------------------------------------------------

        if not SUGGESTIONS_ENABLED:

            return

        # ----------------------------------------------------
        # NOMÉS CANAL DE SUGGERIMENTS
        # ----------------------------------------------------

        if message.channel.id != SUGGESTIONS_CHANNEL_ID:

            return

        # ----------------------------------------------------
        # IGNORAR BOTS
        # ----------------------------------------------------

        if message.author.bot:

            return

        # ----------------------------------------------------
        # ESBORRAR MISSATGE
        # ----------------------------------------------------

        try:

            await message.delete()

        except discord.NotFound:

            return

        except discord.Forbidden:

            print(
                "❌ No tinc permisos per "
                "esborrar missatges al canal "
                "de suggeriments."
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error esborrant missatge "
                f"de suggeriments: {error}"
            )

            return

        # ----------------------------------------------------
        # AVISAR L'USUARI
        # ----------------------------------------------------

        try:

            await message.author.send(
                "❌ **No pots escriure directament "
                "en aquest canal.**\n\n"
                "💡 Per enviar un suggeriment has "
                "d'utilitzar el comandament "
                "**`/suggeriments`**."
            )

        except discord.Forbidden:

            # L'usuari té els missatges privats tancats.
            pass

        except discord.HTTPException as error:

            print(
                f"❌ Error enviant l'avís "
                f"a {message.author}: {error}"
            )


    # ========================================================
    # REACCIÓ AFEGIDA
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
    # REACCIÓ ELIMINADA
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
    # ACTUALITZAR DES DE REACCIÓ
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

        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------

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
                    f"❌ Error obtenint canal: "
                    f"{error}"
                )

                return

        # ----------------------------------------------------
        # MISSATGE
        # ----------------------------------------------------

        try:

            message = await channel.fetch_message(
                message_id
            )

        except discord.NotFound:

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error obtenint missatge: "
                f"{error}"
            )

            return

        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------

        guild = message.guild

        if guild is None:

            return

        # ----------------------------------------------------
        # AUTOR
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ACTUALITZAR
        # ----------------------------------------------------

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
                f"❌ Error actualitzant "
                f"suggeriment #{suggestion_id}: "
                f"{error}"
            )


    # ========================================================
    # /SUGGERIMENTS
    # ========================================================

    @app_commands.command(
        name="suggeriments",
        description="Envia un suggeriment."
    )
    @app_commands.describe(
        suggeriment=(
            "El suggeriment que vols proposar."
        )
    )
    async def suggeriments(
        self,
        interaction: discord.Interaction,
        suggeriment: str
    ):

        # ----------------------------------------------------
        # RESPONDRE IMMEDIATAMENT
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        # ----------------------------------------------------
        # ACTIVAT
        # ----------------------------------------------------

        if not SUGGESTIONS_ENABLED:

            await interaction.followup.send(
                "❌ El sistema de suggeriments "
                "està desactivat.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        suggeriment = suggeriment.strip()

        if not suggeriment:

            await interaction.followup.send(
                "❌ Has d'escriure un suggeriment.",
                ephemeral=True
            )

            return

        if len(suggeriment) > 2000:

            await interaction.followup.send(
                "❌ El suggeriment no pot superar "
                "els **2000 caràcters**.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.followup.send(
                "❌ Aquest comandament només "
                "funciona dins d'un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CANAL
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
                    f"❌ No puc obtenir el canal "
                    f"de suggeriments: {error}"
                )

                await interaction.followup.send(
                    "❌ No he pogut trobar el canal "
                    "de suggeriments.",
                    ephemeral=True
                )

                return

        # ----------------------------------------------------
        # CREAR REGISTRE
        # ----------------------------------------------------

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
                    suggeriment,
                    STATUS_PENDING,
                    int(time.time())
                )
            )

            suggestion_id = cursor.lastrowid

            connection.commit()
            connection.close()

        except Exception as error:

            print(
                f"❌ Error SQLite creant "
                f"suggeriment: {error}"
            )

            await interaction.followup.send(
                "❌ No he pogut guardar "
                "el suggeriment.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = create_suggestion_embed(
            suggestion_id,
            interaction.user,
            suggeriment,
            likes=0,
            dislikes=0,
            status=STATUS_PENDING
        )

        # ----------------------------------------------------
        # PUBLICAR
        # ----------------------------------------------------

        try:

            message = await channel.send(
                embed=embed
            )

        except Exception as error:

            print(
                f"❌ Error publicant suggeriment: "
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
                "❌ No he pogut publicar "
                "el suggeriment.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # GUARDAR MESSAGE ID
        # ----------------------------------------------------

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
                f"❌ Error guardant message_id: "
                f"{error}"
            )

        # ----------------------------------------------------
        # AFEGIR REACCIONS
        # ----------------------------------------------------

        try:

            await message.add_reaction(
                LIKE_EMOJI
            )

            await message.add_reaction(
                DISLIKE_EMOJI
            )

        except discord.Forbidden:

            print(
                "❌ No tinc permisos per "
                "afegir reaccions."
            )

        except discord.HTTPException as error:

            print(
                f"❌ Error afegint reaccions: "
                f"{error}"
            )

        # ----------------------------------------------------
        # CONFIRMACIÓ
        # ----------------------------------------------------

        await interaction.followup.send(
            f"✅ El teu suggeriment "
            f"**#{suggestion_id}** s'ha publicat a "
            f"{channel.mention}.",
            ephemeral=True
        )


    # ========================================================
    # /ACCEPT
    # ========================================================

    @app_commands.command(
        name="accept",
        description="Accepta un suggeriment."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID del suggeriment."
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
        description="Rebutja un suggeriment."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID del suggeriment."
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
        description="Posa un suggeriment en consideració."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        suggestion_id="ID del suggeriment."
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
    # CANVIAR ESTAT
    # ========================================================

    async def change_status(
        self,
        interaction,
        suggestion_id,
        new_status
    ):

        # ----------------------------------------------------
        # RESPONDRE IMMEDIATAMENT
        # ----------------------------------------------------

        await interaction.response.defer(
            ephemeral=True
        )

        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.followup.send(
                "❌ Aquest comandament només "
                "funciona dins d'un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # OBTENIR SUGGERIMENT
        # ----------------------------------------------------

        suggestion = get_suggestion(
            suggestion_id
        )

        if suggestion is None:

            await interaction.followup.send(
                "❌ No existeix aquest suggeriment.",
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

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if guild_id != interaction.guild.id:

            await interaction.followup.send(
                "❌ Aquest suggeriment "
                "no pertany a aquest servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CANVIAR ESTAT
        # ----------------------------------------------------

        success = set_status(
            suggestion_id,
            new_status,
            interaction.user.id
        )

        if not success:

            await interaction.followup.send(
                "❌ No s'ha pogut actualitzar "
                "el suggeriment.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------

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
                    f"❌ Error obtenint canal: "
                    f"{error}"
                )

                await interaction.followup.send(
                    "⚠️ L'estat s'ha guardat a "
                    "SQLite, però no he trobat "
                    "el canal.",
                    ephemeral=True
                )

                return

        # ----------------------------------------------------
        # MISSATGE
        # ----------------------------------------------------

        try:

            message = await channel.fetch_message(
                message_id
            )

        except discord.NotFound:

            await interaction.followup.send(
                "⚠️ L'estat s'ha guardat, però "
                "el missatge ja no existeix.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error obtenint missatge: "
                f"{error}"
            )

            await interaction.followup.send(
                "⚠️ L'estat s'ha guardat, però "
                "no he pogut obtenir el missatge.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # AUTOR
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ACTUALITZAR EMBED
        # ----------------------------------------------------

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
                f"❌ Error actualitzant embed: "
                f"{error}"
            )

            await interaction.followup.send(
                "⚠️ L'estat s'ha guardat a "
                "SQLite, però no he pogut "
                "actualitzar l'embed.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓ
        # ----------------------------------------------------

        status_text, _ = get_status_data(
            new_status
        )

        await interaction.followup.send(
            f"✅ El suggeriment "
            f"**#{suggestion_id}** ara està com "
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

