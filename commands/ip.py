import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

IP_ENABLED = True

# Si és True, només els administradors poden utilitzar /ip
IP_ADMIN_ONLY = True


# ============================================================
# COG
# ============================================================

class IP(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # /IP
    # ========================================================

    @app_commands.command(
        name="ip",
        description="Mostra la informació per connectar al servidor."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def ip(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # ACTIVAT / DESACTIVAT
        # ----------------------------------------------------

        if not IP_ENABLED:

            await interaction.response.send_message(
                "❌ El comandament /ip està desactivat.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------

        if IP_ADMIN_ONLY:

            if not interaction.user.guild_permissions.administrator:

                await interaction.response.send_message(
                    "❌ Només els administradors poden "
                    "utilitzar aquest comandament.",
                    ephemeral=True
                )

                return

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🖥️ INFORMACIÓ DEL SERVIDOR",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🌐 RadminVPN",
            value=(
                "**Usuari:** `aleixpeix`\n"
                "**Contrasenya:** `julian`"
            ),
            inline=False
        )

        embed.add_field(
            name="🔌 Connexió",
            value=(
                "**IP:** `26.89.63.157`\n"
                "**Versió:** `1.8.x`"
            ),
            inline=False
        )

        embed.set_footer(
            text="RebirthMC Network"
        )

        await interaction.response.send_message(
            embed=embed
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        IP(bot)
    )