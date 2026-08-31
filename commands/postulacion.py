import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

POSTULACION_ENABLED = True

# Rol que aparecerá mencionado en la publicación
STAFF_ROLE_ID = 1541007404588859442

# Enlace de la solicitud
APPLICATION_URL = "https://prova.cat/"


# ============================================================
# COG
# ============================================================

class Postulacion(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # /POSTULACION
    # ========================================================

    @app_commands.command(
        name="postulacion",
        description="Publica la información para entrar al Staff."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def postulacion(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # ACTIVADO / DESACTIVADO
        # ----------------------------------------------------

        if not POSTULACION_ENABLED:

            await interaction.response.send_message(
                "❌ Las postulaciones están desactivadas.",
                ephemeral=True
            )

            return

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
        # OBTENER ROL
        # ----------------------------------------------------

        staff_role = interaction.guild.get_role(
            STAFF_ROLE_ID
        )

        if staff_role is not None:

            staff_mention = staff_role.mention

        else:

            staff_mention = f"<@&{STAFF_ROLE_ID}>"

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        embed.description = (
            "# 📜 POSTULACIÓN STAFF┃RebirthMC Network\n\n"

            "¿Quieres formar parte del equipo de "
            "RebirthMC? "
            f"**{staff_mention}**\n\n"

            "Estamos buscando personas comprometidas, "
            "activas y con ganas de aportar a la "
            "comunidad.\n\n"

            "## 📋 Requisitos básicos\n\n"

            "- Ser usuario Premium.\n"
            "- Tener 14 años o más.\n"
            "- Tener un buen micrófono.\n"
            "- No ser staff de otra Network.\n"
            "- Tener ganas de aprender y trabajar "
            "en equipo.\n\n"

            "## 🚀 Postúlate aquí:\n\n"

            f"👉 [**Haz clic aquí para postularte**]"
            f"({APPLICATION_URL})\n\n"

            "⚠️ **Las plazas son limitadas.** "
            "Si cumples los requisitos necesarios, "
            "nos pondremos en contacto contigo."
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        embed.set_footer(
            text="RebirthMC Network • Postulaciones Staff"
        )

        # ----------------------------------------------------
        # ENVIAR
        # ----------------------------------------------------

        await interaction.response.send_message(
            content=staff_mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                roles=True
            )
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):
    await bot.add_cog(
        Postulacion(bot)
    )