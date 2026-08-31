import asyncio
import random
import re
import sqlite3
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

GIVEAWAYS_ENABLED = True

# Rol que recibe las menciones de los sorteos
GIVEAWAY_ROLE_ID = 1541002745773957162

# Rol que significa que el usuario está verificado
VERIFIED_ROLE_ID = 1541142866129068082

# Canal / destino para reclamar premios
TICKET_CHANNEL_ID = 1540805821192085660

# Colores
GIVEAWAY_COLOR = discord.Color.blurple()
FINISHED_COLOR = discord.Color.gold()
ERROR_COLOR = discord.Color.red()

# Base de datos
DATABASE_PATH = (
    Path(__file__).parent.parent
    / "database"
    / "giveaways.db"
)


# ============================================================
# BASE DE DATOS
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def init_database():

    DATABASE_PATH.parent.mkdir(
        exist_ok=True
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL DEFAULT 0,
            prize TEXT NOT NULL,
            winners INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            ended INTEGER NOT NULL DEFAULT 0,
            host_id INTEGER,
            required_role_id INTEGER,
            required_level INTEGER NOT NULL DEFAULT 0,
            required_verified INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cursor.execute(
        "PRAGMA table_info(giveaways)"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    migrations = {

        "required_role_id":
            "ALTER TABLE giveaways "
            "ADD COLUMN required_role_id INTEGER",

        "required_level":
            "ALTER TABLE giveaways "
            "ADD COLUMN required_level INTEGER "
            "NOT NULL DEFAULT 0",

        "required_verified":
            "ALTER TABLE giveaways "
            "ADD COLUMN required_verified INTEGER "
            "NOT NULL DEFAULT 0",

        "host_id":
            "ALTER TABLE giveaways "
            "ADD COLUMN host_id INTEGER",
    }

    for column, sql in migrations.items():

        if column not in existing_columns:

            print(
                f"🔧 Añadiendo columna '{column}' "
                f"a la base de datos..."
            )

            cursor.execute(sql)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            giveaway_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (
                giveaway_id,
                user_id
            )
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS giveaway_winners (
            giveaway_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (
                giveaway_id,
                user_id
            )
        )
        """
    )

    connection.commit()
    connection.close()

    print("💾 Base de datos de sorteos preparada.")


# ============================================================
# DURACIÓN
# ============================================================

def parse_duration(duration):

    match = re.fullmatch(
        r"(\d+)(s|m|h|d)",
        duration.lower().strip()
    )

    if match is None:
        return None

    amount = int(
        match.group(1)
    )

    unit = match.group(2)

    if unit == "s":
        return amount

    if unit == "m":
        return amount * 60

    if unit == "h":
        return amount * 60 * 60

    if unit == "d":
        return amount * 60 * 60 * 24

    return None


# ============================================================
# PARTICIPANTES
# ============================================================

def get_participant_count(
    giveaway_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM giveaway_participants
        WHERE giveaway_id = ?
        """,
        (
            giveaway_id,
        )
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


def get_participants(
    giveaway_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM giveaway_participants
        WHERE giveaway_id = ?
        """,
        (
            giveaway_id,
        )
    )

    participants = [
        row[0]
        for row in cursor.fetchall()
    ]

    connection.close()

    return participants


# ============================================================
# REQUISITOS
# ============================================================

def get_user_level(
    guild_id,
    user_id
):

    levels_database = (
        Path(__file__).parent.parent
        / "database"
        / "database.db"
    )

    if not levels_database.exists():

        return 0

    try:

        connection = sqlite3.connect(
            levels_database
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT level
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

        connection.close()

        if result is None:
            return 0

        return int(result[0])

    except Exception as error:

        print(
            f"❌ Error obteniendo nivel: {error}"
        )

        return 0


def check_requirements(
    member,
    required_role_id,
    required_level,
    required_verified
):

    if required_role_id is not None:

        role = member.guild.get_role(
            required_role_id
        )

        if role is None:

            return (
                False,
                "❌ El rol requerido no existe."
            )

        if role not in member.roles:

            return (
                False,
                f"❌ Necesitas el rol "
                f"**{role.name}** para participar."
            )

    if required_level > 0:

        current_level = get_user_level(
            member.guild.id,
            member.id
        )

        if current_level < required_level:

            return (
                False,
                f"❌ Necesitas ser como mínimo "
                f"**nivel {required_level}**.\n"
                f"📊 Tu nivel: "
                f"**{current_level}**"
            )

    if required_verified:

        if VERIFIED_ROLE_ID is None:

            return (
                False,
                "❌ El sistema de verificación "
                "no está configurado."
            )

        verified_role = member.guild.get_role(
            VERIFIED_ROLE_ID
        )

        if verified_role is None:

            return (
                False,
                "❌ No encuentro el rol de verificado."
            )

        if verified_role not in member.roles:

            return (
                False,
                "❌ Debes estar verificado "
                "para participar."
            )

    return True, None


# ============================================================
# BOTÓN RECLAMAR PREMIO
# ============================================================

class ClaimPrizeView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            discord.ui.Button(
                label="Abrir un ticket",
                emoji="🎫",
                style=discord.ButtonStyle.link,
                url=(
                    f"https://discord.com/channels/"
                    f"@me/{TICKET_CHANNEL_ID}"
                )
            )
        )


# ============================================================
# VISTA DEL SORTEO (VIEW GIVEAWAY)
# ============================================================

class GiveawayView(
    discord.ui.View
):

    def __init__(
        self,
        bot,
        giveaway_id
    ):

        super().__init__(
            timeout=None
        )

        self.bot = bot
        self.giveaway_id = giveaway_id

        button = discord.ui.Button(
            label="Participar",
            emoji="🎁",
            style=discord.ButtonStyle.primary,
            custom_id=(
                f"giveaway_join:{giveaway_id}"
            )
        )

        button.callback = (
            self.join_giveaway
        )

        self.add_item(button)

    async def join_giveaway(
        self,
        interaction: discord.Interaction
    ):

        try:

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    ended,
                    end_time,
                    required_role_id,
                    required_level,
                    required_verified
                FROM giveaways
                WHERE id = ?
                """,
                (
                    self.giveaway_id,
                )
            )

            result = cursor.fetchone()

            if result is None:

                connection.close()

                await interaction.response.send_message(
                    "❌ Este sorteo ya no existe.",
                    ephemeral=True
                )

                return

            (
                ended,
                end_time,
                required_role_id,
                required_level,
                required_verified
            ) = result

            if (
                ended
                or int(time.time()) >= end_time
            ):

                connection.close()

                await interaction.response.send_message(
                    "❌ Este sorteo ya ha finalizado.",
                    ephemeral=True
                )

                return

            allowed, reason = check_requirements(
                interaction.user,
                required_role_id,
                required_level,
                required_verified
            )

            if not allowed:

                connection.close()

                await interaction.response.send_message(
                    reason,
                    ephemeral=True
                )

                return

            cursor.execute(
                """
                SELECT 1
                FROM giveaway_participants
                WHERE giveaway_id = ?
                AND user_id = ?
                """,
                (
                    self.giveaway_id,
                    interaction.user.id
                )
            )

            if cursor.fetchone() is not None:

                connection.close()

                await interaction.response.send_message(
                    "❌ Ya estás participando en este sorteo.",
                    ephemeral=True
                )

                return

            cursor.execute(
                """
                INSERT INTO giveaway_participants
                (
                    giveaway_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    self.giveaway_id,
                    interaction.user.id
                )
            )

            connection.commit()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM giveaway_participants
                WHERE giveaway_id = ?
                """,
                (
                    self.giveaway_id,
                )
            )

            participant_count = (
                cursor.fetchone()[0]
            )

            connection.close()

            await interaction.response.send_message(
                "🎉 ¡Te has apuntado al sorteo!",
                ephemeral=True
            )

            try:

                message = (
                    await interaction.channel.fetch_message(
                        interaction.message.id
                    )
                )

                if not message.embeds:
                    return

                embed = message.embeds[0]

                for index, field in enumerate(
                    embed.fields
                ):

                    if field.name == "👥 Participantes":

                        embed.set_field_at(
                            index,
                            name="👥 Participantes",
                            value=(
                                f"**{participant_count}**"
                            ),
                            inline=True
                        )

                        break

                await message.edit(
                    embed=embed,
                    view=self
                )

            except Exception as error:

                print(
                    "❌ Error actualizando "
                    f"participantes: {error}"
                )

        except Exception as error:

            print(
                f"❌ Error participando en el sorteo: {error}"
            )

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    "❌ Ha habido un error "
                    "intentando participar.",
                    ephemeral=True
                )


# ============================================================
# COG
# ============================================================

class Giveaways(
    commands.Cog
):

    def __init__(
        self,
        bot
    ):

        self.bot = bot
        self.tasks = {}

        init_database()

    # ========================================================
    # CARGA DEL COG
    # ========================================================

    async def cog_load(self):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                message_id,
                end_time
            FROM giveaways
            WHERE ended = 0
            """
        )

        giveaways = cursor.fetchall()

        connection.close()

        for (
            giveaway_id,
            message_id,
            end_time
        ) in giveaways:

            if message_id:

                try:

                    self.bot.add_view(
                        GiveawayView(
                            self.bot,
                            giveaway_id
                        ),
                        message_id=message_id
                    )

                except Exception as error:

                    print(
                        f"❌ Error cargando "
                        f"vista #{giveaway_id}: {error}"
                    )

            task = asyncio.create_task(
                self.wait_for_giveaway(
                    giveaway_id,
                    end_time
                )
            )

            self.tasks[
                giveaway_id
            ] = task

        print(
            f"🎉 {len(giveaways)} sorteo(s) cargado(s)."
        )

    # ========================================================
    # ESPERAR
    # ========================================================

    async def wait_for_giveaway(
        self,
        giveaway_id,
        end_time
    ):

        remaining = (
            end_time -
            int(time.time())
        )

        if remaining > 0:

            await asyncio.sleep(
                remaining
            )

        else:

            print(
                f"⏰ El sorteo #{giveaway_id} "
                f"ya había terminado mientras el bot "
                f"estaba apagado."
            )

        await self.end_giveaway(
            giveaway_id,
            late=remaining <= 0
        )

    # ========================================================
    # /GIVEAWAY
    # ========================================================

    @app_commands.command(
        name="giveaway",
        description="Crea un sorteo."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        duration="Duración: 30s, 10m, 1h, 2d...",
        winners="Número de ganadores",
        prize="Premio del sorteo",
        required_role="Rol necesario para participar",
        required_level="Nivel mínimo necesario",
        verified="Exigir cuenta verificada"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: int,
        prize: str,
        required_role: discord.Role | None = None,
        required_level: int = 0,
        verified: bool = False
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            if not GIVEAWAYS_ENABLED:

                await interaction.followup.send(
                    "❌ Los sorteos están desactivados.",
                    ephemeral=True
                )

                return

            seconds = parse_duration(
                duration
            )

            if seconds is None:

                await interaction.followup.send(
                    "❌ Duración incorrecta.\n\n"
                    "`30s` → 30 segundos\n"
                    "`10m` → 10 minutos\n"
                    "`2h` → 2 horas\n"
                    "`3d` → 3 días",
                    ephemeral=True
                )

                return

            if seconds < 10:

                await interaction.followup.send(
                    "❌ El sorteo debe durar "
                    "como mínimo **10 segundos**.",
                    ephemeral=True
                )

                return

            if winners < 1:

                await interaction.followup.send(
                    "❌ Debe haber al menos "
                    "un ganador.",
                    ephemeral=True
                )

                return

            if winners > 50:

                await interaction.followup.send(
                    "❌ No puedes tener más de "
                    "**50 ganadores**.",
                    ephemeral=True
                )

                return

            if not prize.strip():

                await interaction.followup.send(
                    "❌ Debes especificar un premio.",
                    ephemeral=True
                )

                return

            if required_level < 0:

                await interaction.followup.send(
                    "❌ El nivel no puede ser negativo.",
                    ephemeral=True
                )

                return

            if verified:

                if VERIFIED_ROLE_ID is None:

                    await interaction.followup.send(
                        "❌ No está configurado "
                        "`VERIFIED_ROLE_ID`.",
                        ephemeral=True
                    )

                    return

                verified_role = (
                    interaction.guild.get_role(
                        VERIFIED_ROLE_ID
                    )
                )

                if verified_role is None:

                    await interaction.followup.send(
                        "❌ No encuentro el rol de verificado.",
                        ephemeral=True
                    )

                    return

            end_time = int(
                time.time() +
                seconds
            )

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO giveaways
                (
                    guild_id,
                    channel_id,
                    message_id,
                    prize,
                    winners,
                    end_time,
                    host_id,
                    required_role_id,
                    required_level,
                    required_verified
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction.guild.id,
                    interaction.channel.id,
                    0,
                    prize,
                    winners,
                    end_time,
                    interaction.user.id,
                    (
                        required_role.id
                        if required_role
                        else None
                    ),
                    required_level,
                    1 if verified else 0
                )
            )

            giveaway_id = cursor.lastrowid

            connection.commit()
            connection.close()

            role = interaction.guild.get_role(
                GIVEAWAY_ROLE_ID
            )

            if role:

                role_mention = role.mention

            else:

                role_mention = (
                    f"<@&{GIVEAWAY_ROLE_ID}>"
                )

            embed = discord.Embed(
                color=GIVEAWAY_COLOR
            )

            embed.description = (
                "# 🏆 SORTEO\n\n"
                "### 📋 Información del sorteo\n\n"
                f"- **Premio:** {prize}\n"
                f"- **Organizado por:** "
                f"**{interaction.user.mention}**\n"
                f"- **Termina en:** "
                f"<t:{end_time}:F> "
                f"(<t:{end_time}:R>)\n\n"
                f"- **Ganadores:** "
                f"**{winners}**"
            )

            requirements = []

            if required_role:

                requirements.append(
                    f"🎭 {required_role.mention}"
                )

            if required_level > 0:

                requirements.append(
                    f"📊 Nivel **{required_level}+**"
                )

            if verified:

                verified_role = (
                    interaction.guild.get_role(
                        VERIFIED_ROLE_ID
                    )
                )

                if verified_role:

                    requirements.append(
                        f"✅ {verified_role.mention}"
                    )

                else:

                    requirements.append(
                        "✅ Cuenta verificada"
                    )

            if requirements:

                embed.add_field(
                    name="🔒 Requisitos",
                    value="\n".join(
                        requirements
                    ),
                    inline=False
                )

            embed.add_field(
                name="👥 Participantes",
                value="**0**",
                inline=True
            )

            embed.set_footer(
                text=f"Sorteo #{giveaway_id}"
            )

            view = GiveawayView(
                self.bot,
                giveaway_id
            )

            message = await interaction.channel.send(
                content=role_mention,
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(
                    roles=True
                )
            )

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE giveaways
                SET message_id = ?
                WHERE id = ?
                """,
                (
                    message.id,
                    giveaway_id
                )
            )

            connection.commit()
            connection.close()

            task = asyncio.create_task(
                self.wait_for_giveaway(
                    giveaway_id,
                    end_time
                )
            )

            self.tasks[
                giveaway_id
            ] = task

            await interaction.followup.send(
                f"✅ ¡Sorteo **#{giveaway_id}** creado!",
                ephemeral=True
            )

        except Exception as error:

            print(
                "❌ ERROR CREANDO EL SORTEO:"
            )

            print(
                repr(error)
            )

            await interaction.followup.send(
                "❌ Ha habido un error creando "
                "el sorteo.\n"
                "Mira la consola del bot para ver "
                "el error.",
                ephemeral=True
            )

    # ========================================================
    # FINALIZAR SORTEO
    # ========================================================

    async def end_giveaway(
        self,
        giveaway_id,
        late=False
    ):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                guild_id,
                channel_id,
                message_id,
                prize,
                winners
            FROM giveaways
            WHERE id = ?
            AND ended = 0
            """,
            (
                giveaway_id,
            )
        )

        giveaway = cursor.fetchone()

        if giveaway is None:

            connection.close()

            return

        (
            guild_id,
            channel_id,
            message_id,
            prize,
            winner_count
        ) = giveaway

        cursor.execute(
            """
            SELECT user_id
            FROM giveaway_participants
            WHERE giveaway_id = ?
            """,
            (
                giveaway_id,
            )
        )

        participants = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            UPDATE giveaways
            SET ended = 1
            WHERE id = ?
            """,
            (
                giveaway_id,
            )
        )

        connection.commit()
        connection.close()

        self.tasks.pop(
            giveaway_id,
            None
        )

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
                    f"❌ No puedo encontrar el canal: {error}"
                )

                return

        try:

            message = await channel.fetch_message(
                message_id
            )

        except Exception as error:

            print(
                f"❌ No puedo encontrar el mensaje: {error}"
            )

            return

        # ====================================================
        # SIN PARTICIPANTES
        # ====================================================

        if not participants:

            embed = discord.Embed(
                color=ERROR_COLOR
            )

            embed.description = (
                "# 🎉 SORTEO FINALIZADO\n\n"
                "### ❌ No ha habido participantes.\n\n"
                f"**Premio:** {prize}"
            )

            if late:

                embed.description += (
                    "\n\n"
                    "⚠️ **¡Disculpas por el retraso!**\n"
                    "El bot estaba cerrado cuando "
                    "el sorteo debía finalizar."
                )

            embed.set_footer(
                text=f"Sorteo #{giveaway_id}"
            )

            await message.edit(
                embed=embed,
                view=ClaimPrizeView()
            )

            return

        # ====================================================
        # GANADORES
        # ====================================================

        winner_count = min(
            winner_count,
            len(participants)
        )

        winners = random.sample(
            participants,
            winner_count
        )

        connection = get_connection()
        cursor = connection.cursor()

        for user_id in winners:

            cursor.execute(
                """
                INSERT OR IGNORE INTO giveaway_winners
                (
                    giveaway_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    giveaway_id,
                    user_id
                )
            )

        connection.commit()
        connection.close()

        # ====================================================
        # MENCIONES
        # ====================================================

        winner_mentions = "\n".join(
            f"**<@{user_id}>**"
            for user_id in winners
        )

        # ====================================================
        # EMBED FINAL
        # ====================================================

        embed = discord.Embed(
            color=FINISHED_COLOR
        )

        embed.description = (
            "# 🎉 SORTEO FINALIZADO\n\n"
            "### 🏆 ¡Felicidades a los ganadores!\n\n"
            f"{winner_mentions}\n\n"
            f"🎁 **Premio:** {prize}\n\n"
            "🎫 **Podéis abrir un ticket para "
            "reclamar vuestro premio.**"
        )

        if late:

            embed.description += (
                "\n\n"
                "⚠️ **¡Disculpas por el retraso!**\n"
                "El bot estaba cerrado cuando "
                "el sorteo debía finalizar."
            )

        embed.set_footer(
            text=f"Sorteo #{giveaway_id}"
        )

        await message.edit(
            embed=embed,
            view=ClaimPrizeView()
        )

        # ====================================================
        # AVISO EN EL SERVIDOR
        # ====================================================

        mentions = " ".join(
            f"<@{user_id}>"
            for user_id in winners
        )

        await channel.send(
            f"# 🎉 SORTEO FINALIZADO\n\n"
            f"🏆 **¡Enhorabuena a los ganadores!**\n\n"
            f"{mentions}\n\n"
            f"🎁 ¡Habéis ganado **{prize}**!\n"
            f"🎫 Abrid un ticket para reclamar vuestro premio."
        )

        # ====================================================
        # AVISO POR MD (MENSAJE PRIVADO)
        # ====================================================

        for user_id in winners:

            try:

                user = self.bot.get_user(
                    user_id
                )

                if user is None:

                    user = await self.bot.fetch_user(
                        user_id
                    )

                # --------------------------------------------
                # EMBED PRIVADO
                # --------------------------------------------

                dm_embed = discord.Embed(
                    color=FINISHED_COLOR
                )

                dm_embed.description = (
                    "# 🏆 ¡ENHORABUENA!\n\n"
                    f"¡Has ganado el sorteo "
                    f"**#{giveaway_id}** de **RebirthMC Network**!\n\n"
                    f"🎁 **Premio**\n"
                    f"```{prize}```\n\n"
                    "🎫 **¿Cómo reclamar el premio?**\n"
                    "Abre un ticket en el servidor e indica "
                    "que has ganado este sorteo.\n\n"
                    f"🏆 **Sorteo:** #{giveaway_id}\n"
                    "⏰ **¡No te olvides de reclamarlo!**"
                )

                dm_embed.set_footer(
                    text="RebirthMC Network • Sorteos"
                )

                dm_view = ClaimPrizeView()

                await user.send(
                    embed=dm_embed,
                    view=dm_view
                )

                print(
                    f"📩 MD enviado a {user} "
                    f"por el sorteo #{giveaway_id}."
                )

            except discord.Forbidden:

                print(
                    f"⚠️ No puedo enviar MD a "
                    f"{user_id}: los mensajes privados "
                    f"están cerrados."
                )

            except discord.HTTPException as error:

                print(
                    f"❌ Error enviando MD a "
                    f"{user_id}: {error}"
                )

            except Exception as error:

                print(
                    f"❌ Error inesperado enviando "
                    f"MD a {user_id}: {error}"
                )

    # ========================================================
    # /END
    # ========================================================

    @app_commands.command(
        name="end",
        description="Finaliza un sorteo inmediatamente."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        giveaway_id="ID del sorteo"
    )
    async def end(
        self,
        interaction: discord.Interaction,
        giveaway_id: int
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT ended, guild_id
            FROM giveaways
            WHERE id = ?
            """,
            (
                giveaway_id,
            )
        )

        result = cursor.fetchone()

        connection.close()

        if result is None:

            await interaction.followup.send(
                "❌ No existe este sorteo.",
                ephemeral=True
            )

            return

        ended, guild_id = result

        if guild_id != interaction.guild.id:

            await interaction.followup.send(
                "❌ Este sorteo no es de este servidor.",
                ephemeral=True
            )

            return

        if ended:

            await interaction.followup.send(
                "❌ Este sorteo ya ha finalizado.",
                ephemeral=True
            )

            return

        await self.end_giveaway(
            giveaway_id
        )

        await interaction.followup.send(
            f"🛑 Sorteo **#{giveaway_id}** finalizado.",
            ephemeral=True
        )

    # ========================================================
    # /REROLL
    # ========================================================

    @app_commands.command(
        name="reroll",
        description="Elige nuevos ganadores."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        giveaway_id="ID del sorteo",
        winners="Número de nuevos ganadores"
    )
    async def reroll(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
        winners: int = 1
    ):

        await interaction.response.defer()

        if winners < 1:

            await interaction.followup.send(
                "❌ Debe haber al menos "
                "un ganador."
            )

            return

        if winners > 50:

            await interaction.followup.send(
                "❌ No puedes elegir más de "
                "**50 ganadores**."
            )

            return

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                guild_id,
                ended,
                prize
            FROM giveaways
            WHERE id = ?
            """,
            (
                giveaway_id,
            )
        )

        giveaway = cursor.fetchone()

        if giveaway is None:

            connection.close()

            await interaction.followup.send(
                "❌ No existe este sorteo."
            )

            return

        (
            guild_id,
            ended,
            prize
        ) = giveaway

        if guild_id != interaction.guild.id:

            connection.close()

            await interaction.followup.send(
                "❌ Este sorteo no es "
                "de este servidor."
            )

            return

        if not ended:

            connection.close()

            await interaction.followup.send(
                "❌ El sorteo todavía no ha terminado."
            )

            return

        cursor.execute(
            """
            SELECT user_id
            FROM giveaway_participants
            WHERE giveaway_id = ?
            """,
            (
                giveaway_id,
            )
        )

        participants = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.execute(
            """
            SELECT user_id
            FROM giveaway_winners
            WHERE giveaway_id = ?
            """,
            (
                giveaway_id,
            )
        )

        previous_winners = {
            row[0]
            for row in cursor.fetchall()
        }

        connection.close()

        available = [
            user_id
            for user_id in participants
            if user_id not in previous_winners
        ]

        if not available:

            await interaction.followup.send(
                "❌ No quedan participantes "
                "que no hayan ganado anteriormente."
            )

            return

        winners = random.sample(
            available,
            min(
                winners,
                len(available)
            )
        )

        connection = get_connection()
        cursor = connection.cursor()

        for user_id in winners:

            cursor.execute(
                """
                INSERT OR IGNORE INTO giveaway_winners
                (
                    giveaway_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    giveaway_id,
                    user_id
                )
            )

        connection.commit()
        connection.close()

        mentions = " ".join(
            f"<@{user_id}>"
            for user_id in winners
        )

        # ----------------------------------------------------
        # AVISO SERVIDOR
        # ----------------------------------------------------

        await interaction.followup.send(
            f"# 🔄 REROLL\n\n"
            f"🎉 Nuevo(s) ganador(es):\n"
            f"{mentions}\n\n"
            f"🎁 Premio: **{prize}**"
        )

        # ----------------------------------------------------
        # AVISO MD
        # ----------------------------------------------------

        for user_id in winners:

            try:

                user = self.bot.get_user(
                    user_id
                )

                if user is None:

                    user = await self.bot.fetch_user(
                        user_id
                    )

                dm_embed = discord.Embed(
                    color=FINISHED_COLOR
                )

                dm_embed.description = (
                    "# 🎉 ¡HAS GANADO!\n\n"
                    "Has sido elegido como "
                    "**nuevo ganador** en el reroll "
                    f"del sorteo **#{giveaway_id}**!\n\n"
                    f"🎁 **Premio**\n"
                    f"```{prize}```\n\n"
                    "🎫 **Para reclamarlo**\n"
                    "Abre un ticket en el servidor e indica "
                    f"que has ganado el sorteo "
                    f"**#{giveaway_id}**.\n\n"
                    "⚡ ¡No te olvides de reclamar el premio!"
                )

                dm_embed.set_footer(
                    text="RebirthMC Network • Reroll de Sorteo"
                )

                await user.send(
                    embed=dm_embed,
                    view=ClaimPrizeView()
                )

                print(
                    f"📩 MD de reroll enviado a "
                    f"{user} por el sorteo #{giveaway_id}."
                )

            except discord.Forbidden:

                print(
                    f"⚠️ No puedo enviar MD a {user_id}."
                )

            except Exception as error:

                print(
                    f"❌ Error enviando MD de reroll "
                    f"a {user_id}: {error}"
                )

    # ========================================================
    # /GIVEAWAYLIST
    # ========================================================

    @app_commands.command(
        name="giveawaylist",
        description="Muestra los sorteos activos."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def giveawaylist(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                prize,
                winners,
                end_time,
                channel_id
            FROM giveaways
            WHERE guild_id = ?
            AND ended = 0
            ORDER BY end_time ASC
            """,
            (
                interaction.guild.id,
            )
        )

        giveaways = cursor.fetchall()

        connection.close()

        if not giveaways:

            await interaction.followup.send(
                "📋 No hay ningún sorteo activo.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🎁 Sorteos activos",
            color=GIVEAWAY_COLOR
        )

        for (
            giveaway_id,
            prize,
            winners,
            end_time,
            channel_id
        ) in giveaways:

            count = get_participant_count(
                giveaway_id
            )

            channel = (
                interaction.guild.get_channel(
                    channel_id
                )
            )

            if channel:

                channel_text = channel.mention

            else:

                channel_text = (
                    f"`{channel_id}`"
                )

            embed.add_field(
                name=(
                    f"🎁 Sorteo #{giveaway_id} "
                    f"— {prize}"
                ),
                value=(
                    f"👥 Participantes: **{count}**\n"
                    f"🏆 Ganadores: **{winners}**\n"
                    f"⏰ Termina: "
                    f"<t:{end_time}:R>\n"
                    f"📍 Canal: {channel_text}"
                ),
                inline=False
            )

        embed.set_footer(
            text="Sistema de Sorteos"
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )


# ============================================================
# CONFIGURACIÓN DE INICIO (SETUP)
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Giveaways(bot)
    )