import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

POSTULACION_ENABLED = True

# Rol que apareixerà mencionat a la publicació
STAFF_ROLE_ID = 1541007404588859442

# Enllaç de l'aplicació
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
        description="Publica la informació per entrar a l'Staff."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def postulacion(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # ACTIVAT / DESACTIVAT
        # ----------------------------------------------------

        if not POSTULACION_ENABLED:

            await interaction.response.send_message(
                "❌ Les postulacions estan desactivades.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROVAR ADMIN
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Només els administradors poden "
                "utilitzar aquest comandament.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # OBTENIR ROL
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
            "# 📜 POSTULACIÓ STAFF┃RebirthMC Network\n\n"

            "Vols formar part de l'equip de "
            "RebirthMC? "
            f"**{staff_mention}**\n\n"

            "Estem buscant persones compromeses, "
            "actives i amb ganes d'aportar a la "
            "comunitat.\n\n"

            "## 📋 Requisits bàsics\n\n"

            "- Ser usuari Premium.\n"
            "- Tenir 14 anys o més.\n"
            "- Tenir un bon micròfon.\n"
            "- No ser staff d'una altra Network.\n"
            "- Tenir ganes d'aprendre i treballar "
            "en equip.\n\n"

            "## 🚀 Postula't aquí:\n\n"

            f"👉 [**Clica aquí per postular-te**]"
            f"({APPLICATION_URL})\n\n"

            "⚠️ **Les places són limitades.** "
            "Si compleixes els requisits necessaris, "
            "ens posarem en contacte amb tu."
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        embed.set_footer(
            text="RebirthMC Network • Postulacions Staff"
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