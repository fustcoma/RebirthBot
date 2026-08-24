import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from database.database import connect


# ============================================================
# CONFIGURACIÓ
# ============================================================

LEVELS_ENABLED = True

# ------------------------------------------------------------
# XP
# ------------------------------------------------------------

MIN_XP = 0.5
MAX_XP = 1.5

XP_COOLDOWN = 20

BASE_XP_PER_LEVEL = 10

XP_GROWTH = 1.15


# ------------------------------------------------------------
# CANAL LEVEL UP
# ------------------------------------------------------------

LEVEL_UP_CHANNEL_ID = 1541038984116043877


# ============================================================
# ROLS PER NIVELL
# ============================================================

ROLE_LEVEL_10 = 1541040255539355740
ROLE_LEVEL_20 = 1541040393209122846
ROLE_LEVEL_50 = 1541040477992914994


LEVEL_ROLES = {
    10: ROLE_LEVEL_10,
    20: ROLE_LEVEL_20,
    50: ROLE_LEVEL_50
}


# ============================================================
# COOLDOWNS
# ============================================================

xp_cooldowns = {}


# ============================================================
# BASE DE DADES
# ============================================================

def create_levels_table():

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS levels (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            xp REAL NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        )
        """
    )

    connection.commit()

    # --------------------------------------------------------
    # COMPATIBILITAT AMB LA TAULA ANTIGA
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(levels)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "xp" not in columns:

        try:

            cursor.execute(
                """
                ALTER TABLE levels
                ADD COLUMN xp REAL NOT NULL DEFAULT 0
                """
            )

            connection.commit()

            print(
                "🔄 Base de dades: columna XP afegida."
            )

        except Exception as error:

            print(
                f"❌ Error actualitzant la base de dades: "
                f"{error}"
            )

    connection.close()


# ============================================================
# XP NECESSÀRIA PER NIVELL
# ============================================================

def xp_for_level(level: int) -> float:

    if level <= 0:
        return 0

    return (
        BASE_XP_PER_LEVEL
        * (XP_GROWTH ** (level - 1))
    )


# ============================================================
# XP TOTAL NECESSÀRIA PER ARRIBAR A UN NIVELL
# ============================================================

def total_xp_for_level(level: int) -> float:

    if level <= 0:
        return 0

    total = 0

    for current_level in range(1, level + 1):

        total += xp_for_level(
            current_level
        )

    return total


# ============================================================
# CALCULAR NIVELL A PARTIR DE XP
# ============================================================

def calculate_level(xp: float) -> int:

    level = 0
    required = xp_for_level(1)

    while xp >= required:

        level += 1

        required = (
            total_xp_for_level(
                level + 1
            )
        )

        if level > 1000:
            break

    return level


# ============================================================
# BARRA DE PROGRÉS
# ============================================================

def progress_bar(
    current: float,
    required: float,
    size: int = 20
) -> str:

    if required <= 0:

        return "█" * size

    percentage = current / required

    percentage = max(
        0,
        min(
            percentage,
            1
        )
    )

    filled = int(
        percentage * size
    )

    empty = size - filled

    return (
        "█" * filled
        + "░" * empty
    )


# ============================================================
# ACTUALITZAR ROLS
# ============================================================

async def update_level_roles(
    member: discord.Member,
    level: int
):

    bot_member = member.guild.me

    if bot_member is None:

        print(
            "❌ No he pogut obtenir el membre del bot."
        )

        return

    for required_level, role_id in LEVEL_ROLES.items():

        if role_id is None:
            continue

        role = member.guild.get_role(
            role_id
        )

        if role is None:

            print(
                f"❌ No trobo el rol amb ID {role_id}."
            )

            continue

        # ----------------------------------------------------
        # DONAR ROL
        # ----------------------------------------------------

        if level >= required_level:

            if role in member.roles:
                continue

            if role >= bot_member.top_role:

                print(
                    f"❌ No puc donar '{role.name}' a "
                    f"{member} perquè el rol del bot "
                    f"està per sota."
                )

                continue

            try:

                await member.add_roles(
                    role,
                    reason=(
                        f"Recompensa nivell "
                        f"{required_level}"
                    )
                )

                print(
                    f"✅ Rol '{role.name}' donat a "
                    f"{member}."
                )

            except discord.Forbidden:

                print(
                    f"❌ Discord no permet donar "
                    f"'{role.name}' a {member}."
                )

        # ----------------------------------------------------
        # TREURE ROL
        # ----------------------------------------------------

        else:

            if role not in member.roles:
                continue

            if role >= bot_member.top_role:

                print(
                    f"❌ No puc treure '{role.name}' a "
                    f"{member} perquè el rol del bot "
                    f"està per sota."
                )

                continue

            try:

                await member.remove_roles(
                    role,
                    reason=(
                        f"Ja no correspon al nivell "
                        f"{level}"
                    )
                )

                print(
                    f"🗑️ Rol '{role.name}' tret de "
                    f"{member}."
                )

            except discord.Forbidden:

                print(
                    f"❌ Discord no permet treure "
                    f"'{role.name}' de {member}."
                )


# ============================================================
# COG
# ============================================================

class Levels(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        create_levels_table()

        print(
            "📊 Sistema de nivells carregat."
        )


    # ========================================================
    # BOT READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(self):

        if getattr(
            self,
            "_levels_checked",
            False
        ):

            return

        self._levels_checked = True

        print(
            "📊 Comprovant nivells dels usuaris..."
        )

        await self.update_all_levels()


    # ========================================================
    # ACTUALITZAR TOTS ELS NIVELLS
    # ========================================================

    async def update_all_levels(self):

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT guild_id, user_id, xp, level
            FROM levels
            """
        )

        users = cursor.fetchall()

        connection.close()

        updated = 0

        for (
            guild_id,
            user_id,
            xp,
            old_level
        ) in users:

            real_level = calculate_level(
                xp
            )

            if real_level != old_level:

                connection = connect()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    UPDATE levels
                    SET level = ?
                    WHERE guild_id = ?
                    AND user_id = ?
                    """,
                    (
                        real_level,
                        guild_id,
                        user_id
                    )
                )

                connection.commit()
                connection.close()

                updated += 1

            guild = self.bot.get_guild(
                guild_id
            )

            if guild is None:
                continue

            member = guild.get_member(
                user_id
            )

            if member is None:
                continue

            await update_level_roles(
                member,
                real_level
            )

        print(
            f"📊 Nivells comprovats. "
            f"{updated} actualitzats."
        )


    # ========================================================
    # NOU MISSATGE
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

        if not LEVELS_ENABLED:
            return

        if message.author.bot:
            return

        if message.guild is None:
            return

        user_id = message.author.id

        # ----------------------------------------------------
        # COOLDOWN XP
        # ----------------------------------------------------

        now = time.monotonic()

        last_xp = xp_cooldowns.get(
            user_id
        )

        if last_xp is not None:

            if (
                now - last_xp
                < XP_COOLDOWN
            ):

                return

        xp_cooldowns[user_id] = now

        # ----------------------------------------------------
        # XP ALEATÒRIA
        # ----------------------------------------------------

        gained_xp = round(
            random.uniform(
                MIN_XP,
                MAX_XP
            ),
            2
        )

        guild_id = message.guild.id

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT xp, level
            FROM levels
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                guild_id,
                user_id
            )
        )

        result = cursor.fetchone()

        # ----------------------------------------------------
        # USUARI NO EXISTEIX
        # ----------------------------------------------------

        if result is None:

            old_xp = 0
            old_level = 0

            new_xp = gained_xp

            new_level = calculate_level(
                new_xp
            )

            cursor.execute(
                """
                INSERT INTO levels
                (
                    guild_id,
                    user_id,
                    xp,
                    level
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    guild_id,
                    user_id,
                    new_xp,
                    new_level
                )
            )

        # ----------------------------------------------------
        # USUARI EXISTENT
        # ----------------------------------------------------

        else:

            old_xp = float(
                result[0]
            )

            old_level = int(
                result[1]
            )

            new_xp = (
                old_xp
                + gained_xp
            )

            new_level = calculate_level(
                new_xp
            )

            cursor.execute(
                """
                UPDATE levels
                SET xp = ?, level = ?
                WHERE guild_id = ?
                AND user_id = ?
                """,
                (
                    new_xp,
                    new_level,
                    guild_id,
                    user_id
                )
            )

        connection.commit()
        connection.close()

        # ----------------------------------------------------
        # ACTUALITZAR ROLS
        # ----------------------------------------------------

        await update_level_roles(
            message.author,
            new_level
        )

        # ----------------------------------------------------
        # NO HA PUJAT DE NIVELL
        # ----------------------------------------------------

        if new_level <= old_level:

            return

        print(
            f"🎉 {message.author} ha pujat "
            f"del nivell {old_level} "
            f"al {new_level}!"
        )

        # ====================================================
        # CANAL LEVEL UP
        # ====================================================

        channel = self.bot.get_channel(
            LEVEL_UP_CHANNEL_ID
        )

        if channel is None:

            print(
                f"❌ No trobo el canal "
                f"{LEVEL_UP_CHANNEL_ID}"
            )

            return

        # ====================================================
        # EMBED LEVEL UP
        # ====================================================

        embed = discord.Embed(
            title=f"🎉 NIVELL {new_level}",
            description=(
                f"🎊 Enhorabona, "
                f"{message.author.mention}!\n\n"
                f"Has arribat al "
                f"**nivell {new_level}** "
                f"del servidor!"
            ),
            color=discord.Color.gold()
        )

        # ----------------------------------------------------
        # ROLS DESBLOQUEJATS
        # ----------------------------------------------------

        obtained_roles = []

        for (
            required_level,
            role_id
        ) in LEVEL_ROLES.items():

            if role_id is None:
                continue

            if (
                old_level
                < required_level
                <= new_level
            ):

                role = message.guild.get_role(
                    role_id
                )

                if role is not None:

                    obtained_roles.append(
                        role.mention
                    )

        if obtained_roles:

            embed.add_field(
                name="🏆 Recompensa",
                value=(
                    "Has desbloquejat:\n"
                    + "\n".join(
                        obtained_roles
                    )
                ),
                inline=False
            )

        # ----------------------------------------------------
        # NIVELLS IMPORTANTS
        # ----------------------------------------------------

        if new_level in LEVEL_ROLES:

            embed.add_field(
                name="⭐ Nivell important!",
                value=(
                    "Has assolit un dels "
                    "nivells especials del servidor!"
                ),
                inline=False
            )

        embed.set_thumbnail(
            url=message.author.display_avatar.url
        )

        embed.set_footer(
            text="RebirthMC Network • Nivells"
        )

        # ----------------------------------------------------
        # ENVIAR
        # ----------------------------------------------------

        try:

            await channel.send(
                content=message.author.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    roles=True
                )
            )

        except discord.Forbidden:

            print(
                "❌ No puc enviar el missatge "
                "al canal de nivells."
            )


    # ========================================================
    # /LEVEL
    # ========================================================

    @app_commands.command(
        name="level",
        description="Mostra el nivell i progrés d'un usuari."
    )
    @app_commands.describe(
        user="Usuari del qual vols veure el nivell"
    )
    async def level(
        self,
        interaction: discord.Interaction,
        user: discord.Member | None = None
    ):

        if not LEVELS_ENABLED:

            await interaction.response.send_message(
                "❌ El sistema de nivells està desactivat.",
                ephemeral=True
            )

            return

        target = (
            user
            if user is not None
            else interaction.user
        )

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT xp, level
            FROM levels
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                target.id
            )
        )

        result = cursor.fetchone()

        connection.close()

        if result is None:

            current_xp = 0.0
            current_level = 0

        else:

            current_xp = float(
                result[0]
            )

            current_level = int(
                result[1]
            )

        # ----------------------------------------------------
        # XP DEL NIVELL ACTUAL
        # ----------------------------------------------------

        current_level_start = (
            total_xp_for_level(
                current_level
            )
        )

        # ----------------------------------------------------
        # XP DEL SEGÜENT NIVELL
        # ----------------------------------------------------

        next_level = current_level + 1

        next_level_total = (
            total_xp_for_level(
                next_level
            )
        )

        # ----------------------------------------------------
        # XP ACTUAL DINS DEL NIVELL
        # ----------------------------------------------------

        xp_current_level = (
            current_xp
            - current_level_start
        )

        xp_needed = (
            next_level_total
            - current_level_start
        )

        if xp_needed <= 0:

            progress = 1

        else:

            progress = (
                xp_current_level
                / xp_needed
            )

        progress = max(
            0,
            min(
                progress,
                1
            )
        )

        # ----------------------------------------------------
        # BARRA
        # ----------------------------------------------------

        bar = progress_bar(
            xp_current_level,
            xp_needed,
            20
        )

        percentage = int(
            progress * 100
        )

        remaining = max(
            0,
            xp_needed - xp_current_level
        )

        # ====================================================
        # EMBED
        # ====================================================

        embed = discord.Embed(
            title="📊 Perfil de nivell",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.add_field(
            name="🏆 Nivell",
            value=f"**{current_level}**",
            inline=True
        )

        embed.add_field(
            name="✨ XP",
            value=f"**{current_xp:.2f}** XP",
            inline=True
        )

        embed.add_field(
            name="📈 Progrés",
            value=(
                f"`{bar}` **{percentage}%**\n"
                f"**{xp_current_level:.2f} / "
                f"{xp_needed:.2f} XP**\n"
                f"⬆️ Et falten **{remaining:.2f} XP**"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 Següent nivell",
            value=f"**Nivell {next_level}**",
            inline=True
        )

        # ----------------------------------------------------
        # ROLS DESBLOQUEJATS
        # ----------------------------------------------------

        unlocked_roles = []

        for (
            required_level,
            role_id
        ) in LEVEL_ROLES.items():

            if (
                current_level
                >= required_level
            ):

                role = interaction.guild.get_role(
                    role_id
                )

                if role is not None:

                    unlocked_roles.append(
                        role.mention
                    )

        if unlocked_roles:

            embed.add_field(
                name="🎭 Rols desbloquejats",
                value="\n".join(
                    unlocked_roles
                ),
                inline=False
            )

        embed.set_footer(
            text="RebirthMC Network • Nivells"
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /LEADERBOARD
    # ========================================================

    @app_commands.command(
        name="leaderboard",
        description="Mostra el top de nivells del servidor."
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction
    ):

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id, xp, level
            FROM levels
            WHERE guild_id = ?
            ORDER BY xp DESC
            LIMIT 20
            """,
            (
                interaction.guild.id,
            )
        )

        users = cursor.fetchall()

        connection.close()

        if not users:

            await interaction.response.send_message(
                "📊 Encara no hi ha ningú al rànquing.",
                ephemeral=True
            )

            return

        description = ""

        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉"
        }

        position = 1

        for (
            user_id,
            xp,
            level
        ) in users:

            member = interaction.guild.get_member(
                user_id
            )

            if member is None:

                name = f"Usuari {user_id}"

            else:

                name = member.mention

            medal = medals.get(
                position,
                f"**{position}.**"
            )

            description += (
                f"{medal} {name} — "
                f"**Nivell {level}** "
                f"• `{xp:.2f} XP`\n"
            )

            position += 1

        embed = discord.Embed(
            title="🏆 Leaderboard",
            description=description,
            color=discord.Color.gold()
        )

        embed.set_footer(
            text="RebirthMC Network • Top 20"
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # /SETLEVEL
    # NOMÉS ADMINISTRADORS
    # ========================================================

    @app_commands.command(
        name="setlevel",
        description="Estableix el nivell d'un usuari."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        user="Usuari",
        level="Nivell que vols establir"
    )
    async def setlevel(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        level: int
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Només els administradors poden "
                "utilitzar aquest comandament.",
                ephemeral=True
            )

            return

        if level < 0:

            await interaction.response.send_message(
                "❌ El nivell no pot ser negatiu.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # XP NECESSÀRIA PER AQUEST NIVELL
        # ----------------------------------------------------

        xp = total_xp_for_level(
            level
        )

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM levels
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                user.id
            )
        )

        result = cursor.fetchone()

        if result is None:

            cursor.execute(
                """
                INSERT INTO levels
                (
                    guild_id,
                    user_id,
                    xp,
                    level
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    interaction.guild.id,
                    user.id,
                    xp,
                    level
                )
            )

        else:

            cursor.execute(
                """
                UPDATE levels
                SET xp = ?, level = ?
                WHERE guild_id = ?
                AND user_id = ?
                """,
                (
                    xp,
                    level,
                    interaction.guild.id,
                    user.id
                )
            )

        connection.commit()
        connection.close()

        await update_level_roles(
            user,
            level
        )

        await interaction.response.send_message(
            f"✅ {user.mention} ara és "
            f"**nivell {level}**.\n"
            f"✨ XP establerta: **{xp:.2f}**",
            ephemeral=True
        )


    # ========================================================
    # /RESETLEVEL
    # NOMÉS ADMINISTRADORS
    # ========================================================

    @app_commands.command(
        name="resetlevel",
        description="Reinicia el nivell d'un usuari."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.describe(
        user="Usuari que vols reiniciar"
    )
    async def resetlevel(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Només els administradors poden "
                "utilitzar aquest comandament.",
                ephemeral=True
            )

            return

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM levels
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                user.id
            )
        )

        result = cursor.fetchone()

        if result is None:

            connection.close()

            await interaction.response.send_message(
                f"ℹ️ {user.mention} ja té el nivell "
                f"reiniciat.",
                ephemeral=True
            )

            return

        cursor.execute(
            """
            UPDATE levels
            SET xp = 0,
                level = 0
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                user.id
            )
        )

        connection.commit()
        connection.close()

        # ----------------------------------------------------
        # TREURE ROLS
        # ----------------------------------------------------

        await update_level_roles(
            user,
            0
        )

        # ----------------------------------------------------
        # CONFIRMACIÓ
        # ----------------------------------------------------

        await interaction.response.send_message(
            f"🔄 S'ha reiniciat el nivell de "
            f"{user.mention}.\n"
            f"📊 Ara té **nivell 0** i **0 XP**.",
            ephemeral=True
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Levels(bot)
    )