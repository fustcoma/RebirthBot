import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

from database.database import connect
from events.logs import send_log


# ============================================================
# CONFIGURACIÓN
# ============================================================

MODERATION_LOGS_ENABLED = True

# A partir de cuántos warns → timeout
WARN_TIMEOUT_AT = 5

# Duración del timeout automático
WARN_TIMEOUT_MINUTES = 10

# A partir de cuántos warns → kick
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
        Añade un warn y comprueba las acciones automáticas.

        Retorna:
        warning_count
        automatic_timeout
        automatic_kick
        """

        connection = connect()
        cursor = connection.cursor()

        # Aseguramos que la tabla existe
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
                    reason=f"Automático: {warning_count} warns"
                )

                automatic_timeout = True

            except discord.Forbidden:
                print(
                    f"[AUTOMOD] No puedo aplicar timeout a {member}."
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
                    reason=f"Automático: {warning_count} warns"
                )

                automatic_kick = True

            except discord.Forbidden:
                print(
                    f"[AUTOMOD] No puedo expulsar a {member}."
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
        description="Expulsa a un miembro del servidor."
    )
    @app_commands.default_permissions(
        kick_members=True
    )
    @app_commands.describe(
        member="Miembro que quieres expulsar",
        reason="Motivo de la expulsión"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sin motivo especificado"
    ):

        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(
                "❌ No tienes permiso para expulsar miembros.",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message(
                "❌ No te puedes expulsar a ti mismo.",
                ephemeral=True
            )
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "❌ No puedes expulsar al dueño del servidor.",
                ephemeral=True
            )
            return

        try:

            await member.kick(reason=reason)

            embed = discord.Embed(
                title="👢 Miembro expulsado",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="👤 Usuario",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="👮 Moderador",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="📝 Motivo",
                value=reason,
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            await self.moderation_log(
                "👢 Miembro expulsado",
                f"{member.mention} ha sido expulsado.",
                discord.Color.orange(),
                [
                    (
                        "👤 Usuario",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motivo",
                        reason,
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puedo expulsar a este miembro. "
                "Comprueba la jerarquía de los roles.",
                ephemeral=True
            )

    # ========================================================
    # /BAN
    # ========================================================

    @app_commands.command(
        name="ban",
        description="Banea a un miembro del servidor."
    )
    @app_commands.default_permissions(
        ban_members=True
    )
    @app_commands.describe(
        member="Miembro que quieres banear",
        reason="Motivo del ban"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sin motivo especificado"
    ):

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "❌ No tienes permiso para banear miembros.",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message(
                "❌ No te puedes banear a ti mismo.",
                ephemeral=True
            )
            return

        if member == interaction.guild.owner:
            await interaction.response.send_message(
                "❌ No puedes banear al dueño del servidor.",
                ephemeral=True
            )
            return

        try:

            await member.ban(reason=reason)

            embed = discord.Embed(
                title="🔨 Miembro baneado",
                color=discord.Color.red()
            )

            embed.add_field(
                name="👤 Usuario",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="👮 Moderador",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="📝 Motivo",
                value=reason,
                inline=True
            )

            await interaction.response.send_message(
                embed=embed
            )

            await self.moderation_log(
                "🔨 Miembro baneado",
                f"{member.mention} ha sido baneado.",
                discord.Color.red(),
                [
                    (
                        "👤 Usuario",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motivo",
                        reason,
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puedo banear a este miembro. "
                "Comprueba la jerarquía de los roles.",
                ephemeral=True
            )

    # ========================================================
    # /UNBAN
    # ========================================================

    @app_commands.command(
        name="unban",
        description="Desbanea a un usuario."
    )
    @app_commands.default_permissions(
        ban_members=True
    )
    @app_commands.describe(
        user_id="ID del usuario que quieres desbanear",
        reason="Motivo del desban"
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Sin motivo especificado"
    ):

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "❌ No tienes permiso para desbanear miembros.",
                ephemeral=True
            )
            return

        try:
            user = await self.bot.fetch_user(int(user_id))

        except ValueError:
            await interaction.response.send_message(
                "❌ La ID no es válida.",
                ephemeral=True
            )
            return

        try:

            await interaction.guild.unban(
                user,
                reason=reason
            )

            await interaction.response.send_message(
                f"✅ **{user}** ha sido desbaneado."
            )

            await self.moderation_log(
                "🔓 Miembro desbaneado",
                f"{user.mention} ha sido desbaneado.",
                discord.Color.green(),
                [
                    (
                        "👤 Usuario",
                        f"{user} (`{user.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "📝 Motivo",
                        reason,
                        True
                    )
                ]
            )

        except discord.NotFound:

            await interaction.response.send_message(
                "❌ Este usuario no está baneado.",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tengo permiso para desbanear.",
                ephemeral=True
            )

    # ========================================================
    # /TIMEOUT
    # ========================================================

    @app_commands.command(
        name="timeout",
        description="Aplica un timeout a un miembro."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    @app_commands.describe(
        member="Miembro al que quieres aplicar timeout",
        minutes="Duración en minutos",
        reason="Motivo del timeout"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str = "Sin motivo especificado"
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tienes permiso para aplicar timeout a miembros.",
                ephemeral=True
            )
            return

        if minutes <= 0 or minutes > 40320:
            await interaction.response.send_message(
                "❌ La duración debe ser de entre 1 minuto y 28 días.",
                ephemeral=True
            )
            return

        try:

            await member.timeout(
                timedelta(minutes=minutes),
                reason=reason
            )

            await interaction.response.send_message(
                f"⏱️ **{member}** ha recibido un "
                f"timeout de **{minutes} minutos**."
            )

            await self.moderation_log(
                "⏱️ Timeout",
                f"Se ha aplicado un timeout a {member.mention}.",
                discord.Color.yellow(),
                [
                    (
                        "👤 Usuario",
                        f"{member} (`{member.id}`)",
                        False
                    ),
                    (
                        "👮 Moderador",
                        interaction.user.mention,
                        True
                    ),
                    (
                        "⏱️ Duración",
                        f"{minutes} minutos",
                        True
                    ),
                    (
                        "📝 Motivo",
                        reason,
                        False
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puedo aplicar timeout a este miembro. "
                "Comprueba la jerarquía de los roles.",
                ephemeral=True
            )

    # ========================================================
    # /CLEAR
    # ========================================================

    @app_commands.command(
        name="clear",
        description="Elimina mensajes del canal."
    )
    @app_commands.default_permissions(
        manage_messages=True
    )
    @app_commands.describe(
        amount="Número de mensajes que quieres eliminar"
    )
    async def clear(
        self,
        interaction: discord.Interaction,
        amount: int
    ):

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ No tienes permiso para eliminar mensajes.",
                ephemeral=True
            )
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "❌ Debes especificar entre 1 y 100 mensajes.",
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
                f"🧹 He eliminado **{len(deleted)} mensajes**.",
                ephemeral=True
            )

            await self.moderation_log(
                "🧹 Mensajes eliminados",
                f"Se han eliminado mensajes en "
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
                        "🗑️ Cantidad",
                        str(len(deleted)),
                        True
                    )
                ]
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ No tengo permiso para gestionar los mensajes.",
                ephemeral=True
            )

    # ========================================================
    # /WARN
    # ========================================================

    @app_commands.command(
        name="warn",
        description="Advierte a un miembro del servidor."
    )
    @app_commands.default_permissions(
        moderate_members=True
    )
    @app_commands.describe(
        member="Miembro al que quieres advertir",
        reason="Motivo de la advertencia"
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Sin motivo especificado"
    ):

        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "❌ No tienes permiso para advertir a miembros.",
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
            description=f"{member.mention} ha recibido un warn.",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📝 Motivo",
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
                name="⏱️ Acción automática",
                value=f"Timeout de **{WARN_TIMEOUT_MINUTES} minutos**",
                inline=False
            )

        if automatic_kick:
            embed.add_field(
                name="👢 Acción automática",
                value="El miembro ha sido expulsado automáticamente.",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

        await self.moderation_log(
            "⚠️ Nuevo warn",
            f"{member.mention} ha recibido un warn.",
            discord.Color.orange(),
            [
                (
                    "👤 Usuario",
                    f"{member} (`{member.id}`)",
                    False
                ),
                (
                    "👮 Moderador",
                    interaction.user.mention,
                    True
                ),
                (
                    "📝 Motivo",
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
        description="Muestra las advertencias de un miembro."
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
                "❌ No tienes permiso.",
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
                f"✅ **{member}** no tiene ningún warn.",
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
                    f"📝 **Motivo:** {reason}\n"
                    f"👮 **Moderador:** <@{moderator_id}>\n"
                    f"🕐 **Fecha:** {timestamp}"
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
        description="Elimina un warn concreto."
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
                "❌ No tienes permiso.",
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
                "❌ Este warn no existe.",
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
            f"✅ Se ha eliminado el warn **#{warning_id}** "
            f"de {member.mention}.\n"
            f"📊 Warns actuales: **{remaining}**"
        )

        await self.moderation_log(
            "↩️ Warn eliminado",
            f"Se ha eliminado un warn de {member.mention}.",
            discord.Color.green()
        )

    # ========================================================
    # /UNWARNALL
    # ========================================================

    @app_commands.command(
        name="unwarnall",
        description="Elimina todos los warns de un miembro."
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
                "❌ No tienes permiso.",
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
            f"🧹 Se han eliminado **{count} warns** "
            f"de {member.mention}."
        )

        await self.moderation_log(
            "🧹 Todos los warns eliminados",
            f"Se han eliminado todos los warns de {member.mention}.",
            discord.Color.green()
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Moderation(bot)
    )