import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

VERIFY_ROLE_ID = 1541142866129068082

# ------------------------------------------------------------
# ENLACES
# ------------------------------------------------------------

WEBSITE_URL = "https://rebirthmc.net"

STORE_URL = "https://store.rebirthmc.net"


# ============================================================
# COLORES
# ============================================================

VERIFY_COLOR = discord.Color.blurple()

RULES_COLOR = discord.Color.blurple()


# ============================================================
# TEXTOS
# ============================================================

VERIFY_TITLE = "🔐 VERIFICACIÓN"

VERIFY_DESCRIPTION = (
    "¡Bienvenido/a al **Discord de RebirthMC**!\n\n"
    "Para poder acceder al servidor, primero te tienes "
    "que verificar.\n\n"
    "Presiona el botón **✅ Verificar** que encontrarás a "
    "continuación.\n\n"
    "Una vez verificado, recibirás automáticamente el rol "
    "correspondiente."
)


# ============================================================
# BOTÓN DE VERIFICACIÓN
# ============================================================

class VerifyButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="Verificar",
            emoji="✅",
            style=discord.ButtonStyle.success,
            custom_id="rebirthmc_verify_button"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Este botón solo funciona dentro "
                "de un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # OBTENER ROL
        # ----------------------------------------------------

        role = interaction.guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ No he podido encontrar el rol de "
                "verificación.",
                ephemeral=True
            )

            print(
                f"❌ No encuentro el rol de verificación "
                f"{VERIFY_ROLE_ID}."
            )

            return

        # ----------------------------------------------------
        # COMPROBAR SI YA ESTÁ VERIFICADO
        # ----------------------------------------------------

        if role in interaction.user.roles:

            await interaction.response.send_message(
                "✅ ¡Ya estás verificado!",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROBAR BOT
        # ----------------------------------------------------

        bot_member = interaction.guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ No he podido obtener la información "
                "del bot.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROBAR JERARQUÍA
        # ----------------------------------------------------

        if role >= bot_member.top_role:

            await interaction.response.send_message(
                "❌ No puedo darte el rol de verificación "
                "porque el rol del bot está por debajo "
                "de este rol.",
                ephemeral=True
            )

            print(
                f"❌ No puedo dar el rol "
                f"'{role.name}'. El rol del bot "
                f"está por debajo."
            )

            return

        # ----------------------------------------------------
        # DAR ROL
        # ----------------------------------------------------

        try:

            await interaction.user.add_roles(
                role,
                reason="Verificación mediante botón"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tengo permisos para darte "
                "el rol de verificación.",
                ephemeral=True
            )

            print(
                "❌ Discord ha rechazado la adición "
                "del rol de verificación."
            )

            return

        except discord.HTTPException as error:

            await interaction.response.send_message(
                "❌ Ha ocurrido un error al verificarte. "
                "Vuelve a intentarlo.",
                ephemeral=True
            )

            print(
                f"❌ Error dando rol de verificación: "
                f"{error}"
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓN
        # ----------------------------------------------------

        await interaction.response.send_message(
            f"🎉 ¡Te has verificado correctamente!\n\n"
            f"Has recibido el rol {role.mention}.",
            ephemeral=True
        )


# ============================================================
# VIEW PERSISTENTE
# ============================================================

class VerifyView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            VerifyButton()
        )


# ============================================================
# COG
# ============================================================

class Verify(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.verify_view_added = False

        print(
            "🔐 Sistema de verificación cargado."
        )


    # ========================================================
    # READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(
        self
    ):

        if self.verify_view_added:

            return

        # ----------------------------------------------------
        # REGISTRAR VIEW PERSISTENTE
        # ----------------------------------------------------

        self.bot.add_view(
            VerifyView()
        )

        self.verify_view_added = True

        print(
            "🔐 Botón de verificación persistentemente cargado."
        )


    # ========================================================
    # /VERIFICAR
    # ========================================================

    @app_commands.command(
        name="verificar",
        description="Publica el mensaje de verificación."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def verificar(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # COMPROBAR ADMIN
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Solo los administradores pueden "
                "utilizar este comando.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Este comando solo funciona "
                "dentro de un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # ROL
        # ----------------------------------------------------

        role = interaction.guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ No encuentro el rol de verificación.\n\n"
                f"ID: `{VERIFY_ROLE_ID}`",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title=VERIFY_TITLE,
            description=VERIFY_DESCRIPTION,
            color=VERIFY_COLOR
        )

        embed.add_field(
            name="🛡️ ¿Cómo funciona?",
            value=(
                "Presiona **✅ Verificar** y recibirás "
                "automáticamente el rol de verificado."
            ),
            inline=False
        )

        embed.add_field(
            name="📋 Importante",
            value=(
                "Antes de participar en el servidor, "
                "asegúrate de haber leído las reglas."
            ),
            inline=False
        )

        embed.set_footer(
            text="RebirthMC Network • Verificación"
        )

        # ----------------------------------------------------
        # ENVIAR
        # ----------------------------------------------------

        try:

            await interaction.channel.send(
                embed=embed,
                view=VerifyView()
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tengo permisos para enviar "
                "mensajes en este canal.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error enviando verificación: "
                f"{error}"
            )

            await interaction.response.send_message(
                "❌ No he podido publicar el mensaje "
                "de verificación.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓN
        # ----------------------------------------------------

        await interaction.response.send_message(
            "✅ Mensaje de verificación publicado.",
            ephemeral=True
        )


    # ========================================================
    # /RULES
    # ========================================================

    @app_commands.command(
        name="rules",
        description="Publica las reglas del servidor."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def rules(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # COMPROBAR ADMIN
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Solo los administradores pueden "
                "utilizar este comando.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Este comando solo funciona "
                "dentro de un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="📜 REGLAS DE DISCORD",
            description=(
                "## BIENVENIDOS AL DISCORD DE REBIRTHMC\n\n"
                "Antes de participar en nuestra comunidad, "
                "asegúrate de leer y respetar las siguientes "
                "reglas."
            ),
            color=RULES_COLOR
        )

        # ----------------------------------------------------
        # REGLAS
        # ----------------------------------------------------

        embed.add_field(
            name="📢 Publicidad",
            value=(
                "Prohibido publicitar sitios web, "
                "servidores o cualquier otro tipo "
                "de servicio."
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Comportamiento",
            value=(
                "Prohibido el uso de lenguaje inapropiado "
                "o soez (comportamiento tóxico) "
                "en chats/voz."
            ),
            inline=False
        )

        embed.add_field(
            name="🔒 Información personal",
            value=(
                "Prohibido enviar información personal "
                "(IPs, IRLs, etc.)."
            ),
            inline=False
        )

        embed.add_field(
            name="⚖️ Sanciones",
            value=(
                "Prohibido discutir sobre una sanción, "
                "strike, mute, etc."
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Amenazas",
            value=(
                "Prohibido amenazar a jugadores o miembros "
                "del staff de DDoS, doxxing y amenazas "
                "de muerte."
            ),
            inline=False
        )

        embed.add_field(
            name="👤 Nombres",
            value=(
                "Prohibido usar nombres inapropiados "
                "o indescifrables en Discord."
            ),
            inline=False
        )

        # ----------------------------------------------------
        # ENLACES
        # ----------------------------------------------------

        embed.add_field(
            name="🔗 ENLACES ÚTILES",
            value=(
                f"🌐 **Sitio web:** [Acceder]({WEBSITE_URL})\n"
                f"🛒 **Tienda:** [Acceder]({STORE_URL})"
            ),
            inline=False
        )

        embed.set_footer(
            text="RebirthMC Network • Reglas de Discord"
        )

        # ----------------------------------------------------
        # PUBLICAR
        # ----------------------------------------------------

        try:

            await interaction.channel.send(
                embed=embed
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tengo permisos para enviar "
                "mensajes en este canal.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error enviando reglas: "
                f"{error}"
            )

            await interaction.response.send_message(
                "❌ No he podido publicar las reglas.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓN
        # ----------------------------------------------------

        await interaction.response.send_message(
            "✅ Reglas publicadas correctamente.",
            ephemeral=True
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot
):

    await bot.add_cog(
        Verify(bot)
    )