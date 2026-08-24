import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

from database.database import connect
from events.logs import send_log


# ============================================================
# CONFIGURACIÓ
# ============================================================

MODERATION_LOGS_ENABLED = True

# A partir de quants warns → timeout
WARN_TIMEOUT_AT = 5

# Durada del timeout automàtic
WARN_TIMEOUT_MINUTES = 10

# A partir de quants warns → kick
WARN_KICK_AT = 6


# ============================================================
# COG
# ============================================================

class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # LOG
    # ========================================================

    async def moderation_log(
        self,
        title,
        description,
        color,
        fields=None
    ):

        if not MODERATION_LOGS_ENABLED:
            return

        try:
            await send_log(
                self.bot,
                title,
                description,
                color,
                fields
            )
        except Exception as e:
            print(f"[LOG ERROR] {e}")

    # ========================================================
    # SISTEMA CENTRAL DE WARNS
    # ========================================================

    async def add_warning(
        self,
        guild,
        member,
        moderator,
        reason
    ):
        """
        Afegeix un warn i comprova les accions automàtiques.

        Retorna:
        warning_count
        automatic_timeout
        automatic_kick
        """

        connection = connect()
        cursor = connection.cursor()

        # Assegurem que la taula existeix
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            INSERT INTO warnings
            (
                guild_id,
                user_id,
                moderator_id,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                guild.id,
                member.id,
                moderator.id,
                reason
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                guild.id,
                member.id
            )
        )

        warning_count = cursor.fetchone()[0]

        connection.close()

        automatic_timeout = False
        automatic_kick = False

        # ====================================================
        # TIMEOUT
        # ====================================================

        if warning_count == WARN_TIMEOUT_AT:

            try:
                await member.timeout(
                    timedelta(
                        minutes=WARN_TIMEOUT_MINUTES
                    ),
                    reason=f"Automàtic: {warning_count} warns"
                )

                automatic_timeout = True

            except discord.Forbidden:
                print(
                    f"[AUTOMOD] No puc fer timeout a {member}."
                )

            except Exception as e:
                print(
                    f"[AUTOMOD] Error timeout: {e}"
                )

        # ====================================================
        # KICK
        # ====================================================

        elif warning_count >= WARN_KICK_AT:

            try:
                await member.kick(
                    reason=f"Automàtic: {warning_count} warns"
                )

                automatic_kick = True

            except discord.Forbidden:
                print(
                    f"[AUTOMOD] No puc expulsar {member}."
                )

            except Exception as e:
                print(
                    f"[AUTOMOD] Error kick: {e}"
                )

        return (
            warning_count,
            automatic_timeout,
            automatic_kick
        )

    # ========================================================
    # /KICK
    # ========================================================

    @app_commands.command(
        name="kick",
        description="Expulsa un membre del servidor."
    )
    @app_commands.default_permissions(
        kick_members=True
    )
    @app_commands.describe(
        member="Membre que vols expulsar",
        reason="Motiu de l'expulsió"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sense motiu especificat"
    ):

        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                "❌ No tens permís per expulsar membres.",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message(
                "❌ No et pots expulsar a tu mateix.",
                ephemeral=True
            )
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "❌ No pots expulsar el propietari del servidor.",
                ephemeral=True
            )
            return

        try:

            await member.kick(reason=reason)

            embed = discord.Embed(
                title="👢 Membre expulsat",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="👤 Usuari",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="👮 Moderador",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="📝 Motiu",
                value=reason,
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            await self.moderation_log(
                "👢 Membre expulsat",
                f"{member.mention} ha estat expulsat.",
                discord.Color.orange(),
                [
                    (
                        "👤 Usuari",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motiu",
                        reason,
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puc expulsar aquest membre. "
                "Comprova la jerarquia dels rols.",
                ephemeral=True
            )

    # ========================================================
    # /BAN
    # ========================================================

    @app_commands.command(
        name="ban",
        description="Baneja un membre del servidor."
    )
    @app_commands.default_permissions(
        ban_members=True
    )
    @app_commands.describe(
        member="Membre que vols banear",
        reason="Motiu del ban"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sense motiu especificat"
    ):

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "❌ No tens permís per banear membres.",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message(
                "❌ No et pots banear a tu mateix.",
                ephemeral=True
            )
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "❌ No pots banear el propietari del servidor.",
                ephemeral=True
            )
            return

        try:

            await member.ban(reason=reason)

            embed = discord.Embed(
                title="🔨 Membre banejat",
                color=discord.Color.red()
            )

            embed.add_field(
                name="👤 Usuari",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="👮 Moderador",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="📝 Motiu",
                value=reason,
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            await self.moderation_log(
                "🔨 Membre banejat",
                f"{member.mention} ha estat banejat.",
                discord.Color.red(),
                [
                    (
                        "👤 Usuari",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motiu",
                        reason,
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puc banear aquest membre. "
                "Comprova la jerarquia dels rols.",
                ephemeral=True
            )

    # ========================================================
    # /UNBAN
    # ========================================================

    @app_commands.command(
        name="unban",
        description="Desbaneja un usuari."
    )
    @app_commands.default_permissions(
        ban_members=True
    )
    @app_commands.describe(
        user_id="ID de l'usuari que vols desbanear",
        reason="Motiu del desban"
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Sense motiu especificat"
    ):

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "❌ No tens permís per desbanear membres.",
                ephemeral=True
            )
            return

        try:
            user = await self.bot.fetch_user(int(user_id))

        except ValueError:
            await interaction.response.send_message(
                "❌ La ID no és vàlida.",
                ephemeral=True
            )
            return

        try:

            await interaction.guild.unban(
                user,
                reason=reason
            )

            await interaction.response.send_message(
                f"✅ **{user}** ha estat desbanejat."
            )

            await self.moderation_log(
                "🔓 Membre desbanejat",
                f"{user.mention} ha estat desbanejat.",
                discord.Color.green(),
                [
                    (
                        "👤 Usuari",
                        f"{user} (`{user.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motiu",
                        reason,
                        True
                    )
                ]
            )

        except discord.NotFound:

            await interaction.response.send_message(
                "❌ Aquest usuari no està banejat.",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tinc permís per desbanear.",
                ephemeral=True
            )

    # ========================================================
    # /TIMEOUT
    # ========================================================

    @app_commands.command(
        name="timeout",
        description="Posa un membre en timeout."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    @app_commands.describe(
        member="Membre que vols posar en timeout",
        minutes="Durada en minuts",
        reason="Motiu del timeout"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str = "Sense motiu especificat"
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tens permís per posar membres en timeout.",
                ephemeral=True
            )
            return

        if minutes <= 0 or minutes > 40320:
            await interaction.response.send_message(
                "❌ La durada ha de ser entre 1 minut i 28 dies.",
                ephemeral=True
            )
            return

        try:

            await member.timeout(
                timedelta(minutes=minutes),
                reason=reason
            )

            await interaction.response.send_message(
                f"⏱️ **{member}** ha estat posat en "
                f"timeout durant **{minutes} minuts**."
            )

            await self.moderation_log(
                "⏱️ Timeout",
                f"{member.mention} ha estat posat en timeout.",
                discord.Color.yellow(),
                [
                    (
                        "👤 Usuari",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "⏱️ Durada",
                        f"{minutes} minuts",
                        True
                    ),
                    (
                        "📝 Motiu",
                        reason,
                        False
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puc posar aquest membre en timeout. "
                "Comprova la jerarquia dels rols.",
                ephemeral=True
            )

    # ========================================================
    # /CLEAR
    # ========================================================

    @app_commands.command(
        name="clear",
        description="Elimina missatges del canal."
    )
    @app_commands.default_permissions(
        manage_messages=True
    )
    @app_commands.describe(
        amount="Nombre de missatges que vols eliminar"
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: int
    ):

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ No tens permís per eliminar missatges.",
                ephemeral=True
            )
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "❌ Has d'especificar entre 1 i 100 missatges.",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            deleted = await interaction.channel.purge(
                limit=amount
            )

            await interaction.followup.send(
                f"🧹 He eliminat **{len(deleted)} missatges**.",
                ephemeral=True
            )

            await self.moderation_log(
                "🧹 Missatges eliminats",
                f"S'han eliminat missatges a "
                f"{interaction.channel.mention}.",
                discord.Color.orange(),
                [
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "💬 Canal",
                        interaction.channel.mention,
                        True
                    ),
                    (
                        "🗑️ Quantitat",
                        str(len(deleted)),
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ No tinc permís per gestionar els missatges.",
                ephemeral=True
            )

    # ========================================================
    # /WARN
    # ========================================================

    @app_commands.command(
        name="warn",
        description="Avisa un membre del servidor."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    @app_commands.describe(
        member="Membre que vols advertir",
        reason="Motiu de l'avís"
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sense motiu especificat"
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tens permís per advertir membres.",
                ephemeral=True
            )
            return

        (
            warning_count,
            automatic_timeout,
            automatic_kick
        ) = await self.add_warning(
            interaction.guild,
            member,
            interaction.user,
            reason
        )

        embed = discord.Embed(
            title="⚠️ Warn",
            description=f"{member.mention} ha rebut un warn.",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📝 Motiu",
            value=reason,
            inline=False
        )

        embed.add_field(
            name="📊 Total de warns",
            value=f"**{warning_count}**",
            inline=True
        )

        if automatic_timeout:
            embed.add_field(
                name="⏱️ Acció automàtica",
                value=f"Timeout de **{WARN_TIMEOUT_MINUTES} minuts**",
                inline=False
            )

        if automatic_kick:
            embed.add_field(
                name="👢 Acció automàtica",
                value="El membre ha estat expulsat automàticament.",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

        await self.moderation_log(
            "⚠️ Nou warn",
            f"{member.mention} ha rebut un warn.",
            discord.Color.orange(),
            [
                (
                    "👤 Usuari",
                    f"{member} (`{member.id}`)",
                    False
                ),
                (
                    "👮 Moderador",
                    interaction.user.mention,
                    True
                ),
                (
                    "📝 Motiu",
                    reason,
                    True
                ),
                (
                    "📊 Total de warns",
                    str(warning_count),
                    True
                )
            ]
        )

    # ========================================================
    # /WARNS
    # ========================================================

    @app_commands.command(
        name="warns",
        description="Mostra els avisos d'un membre."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    async def warns(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tens permís.",
                ephemeral=True
            )
            return

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            SELECT id, moderator_id, reason, timestamp
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            ORDER BY id ASC
            """,
            (
                interaction.guild.id,
                member.id
            )
        )

        warnings = cursor.fetchall()

        connection.close()

        if not warnings:
            await interaction.response.send_message(
                f"✅ **{member}** no té cap warn.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"⚠️ Warns de {member}",
            color=discord.Color.orange()
        )

        for warning in warnings:

            warning_id = warning[0]
            moderator_id = warning[1]
            reason = warning[2]
            timestamp = warning[3]

            embed.add_field(
                name=f"Warn #{warning_id}",
                value=(
                    f"📝 **Motiu:** {reason}\n"
                    f"👮 **Moderador:** <@{moderator_id}>\n"
                    f"🕐 **Data:** {timestamp}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ========================================================
    # /UNWARN
    # ========================================================

    @app_commands.command(
        name="unwarn",
        description="Elimina un warn concret."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    async def unwarn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        warning_id: int
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tens permís.",
                ephemeral=True
            )
            return

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT reason
            FROM warnings
            WHERE id = ?
            AND guild_id = ?
            AND user_id = ?
            """,
            (
                warning_id,
                interaction.guild.id,
                member.id
            )
        )

        warning = cursor.fetchone()

        if warning is None:
            connection.close()

            await interaction.response.send_message(
                "❌ Aquest warn no existeix.",
                ephemeral=True
            )
            return

        cursor.execute(
            """
            DELETE FROM warnings
            WHERE id = ?
            AND guild_id = ?
            AND user_id = ?
            """,
            (
                warning_id,
                interaction.guild.id,
                member.id
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                member.id
            )
        )

        remaining = cursor.fetchone()[0]

        connection.close()

        await interaction.response.send_message(
            f"✅ S'ha eliminat el warn **#{warning_id}** "
            f"de {member.mention}.\n"
            f"📊 Warns actuals: **{remaining}**"
        )

        await self.moderation_log(
            "↩️ Warn eliminat",
            f"S'ha eliminat un warn de {member.mention}.",
            discord.Color.green()
        )

    # ========================================================
    # /UNWARNALL
    # ========================================================

    @app_commands.command(
        name="unwarnall",
        description="Elimina tots els warns d'un membre."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    async def unwarnall(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tens permís.",
                ephemeral=True
            )
            return

        connection = connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM warnings
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (
                interaction.guild.id,
                member.id
            )
        )

        count = cursor.rowcount

        connection.commit()
        connection.close()

        await interaction.response.send_message(
            f"🧹 S'han eliminat **{count} warns** "
            f"de {member.mention}."
        )

        await self.moderation_log(
            "🧹 Tots els warns eliminats",
            f"S'han eliminat tots els warns de {member.mention}.",
            discord.Color.green()
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Moderation(bot)
    )