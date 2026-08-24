import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

ROLES_ENABLED = True


# ============================================================
# IDS DELS ROLS
# ============================================================

ROLE_SORTEJOS = 1541002745773957162
ROLE_EVENTS = 1541007380735590420
ROLE_ACTUALITZACIONS = 1541007515502907432
ROLE_APLICACIO = 1541007404588859442


# ============================================================
# VIEW DELS AUTOROLS
# ============================================================

class AutoRolesView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    # ========================================================
    # 🏆 SORTEJOS
    # ========================================================

    @discord.ui.button(
        label="Sortejos",
        emoji="🏆",
        style=discord.ButtonStyle.primary,
        custom_id="autorole_sortejos"
    )
    async def sortejor_role(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            ROLE_SORTEJOS,
            "sortejos"
        )

    # ========================================================
    # 📅 EVENTS
    # ========================================================

    @discord.ui.button(
        label="Events",
        emoji="📅",
        style=discord.ButtonStyle.primary,
        custom_id="autorole_events"
    )
    async def events_role(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            ROLE_EVENTS,
            "els events"
        )

    # ========================================================
    # 🗂️ ACTUALITZACIONS
    # ========================================================

    @discord.ui.button(
        label="Actualitzacions",
        emoji="🗂️",
        style=discord.ButtonStyle.primary,
        custom_id="autorole_actualitzacions"
    )
    async def actualitzacions_role(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            ROLE_ACTUALITZACIONS,
            "les actualitzacions"
        )

    # ========================================================
    # 💼 APLICACIÓ
    # ========================================================

    @discord.ui.button(
        label="Aplicació",
        emoji="💼",
        style=discord.ButtonStyle.primary,
        custom_id="autorole_aplicacio"
    )
    async def aplicacio_role(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.toggle_role(
            interaction,
            ROLE_APLICACIO,
            "les aplicacions"
        )

    # ========================================================
    # DONAR / TREURE ROL
    # ========================================================

    async def toggle_role(
        self,
        interaction: discord.Interaction,
        role_id: int,
        role_name: str
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ Aquest botó només funciona "
                "dins d'un servidor.",
                ephemeral=True
            )

            return

        role = guild.get_role(
            role_id
        )

        if role is None:

            await interaction.response.send_message(
                "❌ No he pogut trobar aquest rol.",
                ephemeral=True
            )

            return

        member = interaction.user

        # ====================================================
        # JA TÉ EL ROL → TREURE
        # ====================================================

        if role in member.roles:

            try:

                await member.remove_roles(
                    role,
                    reason="Autorol"
                )

                await interaction.response.send_message(
                    f"❌ Ja no rebràs notificacions de "
                    f"**{role_name}**.",
                    ephemeral=True
                )

            except discord.Forbidden:

                await interaction.response.send_message(
                    "❌ No puc treure't aquest rol.\n"
                    "Comprova que el meu rol estigui "
                    "per sobre d'aquest rol.",
                    ephemeral=True
                )

            return

        # ====================================================
        # NO TÉ EL ROL → DONAR
        # ====================================================

        try:

            await member.add_roles(
                role,
                reason="Autorol"
            )

            await interaction.response.send_message(
                f"✅ Ara rebràs notificacions de "
                f"**{role_name}**!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puc donar-te aquest rol.\n"
                "Comprova que el meu rol estigui "
                "per sobre d'aquest rol.",
                ephemeral=True
            )


# ============================================================
# COG
# ============================================================

class Roles(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    # ========================================================
    # CARREGAR VIEW PERSISTENT
    # ========================================================

    async def cog_load(self):

        if ROLES_ENABLED:

            self.bot.add_view(
                AutoRolesView()
            )

            print(
                "🎨 Sistema d'autoroles carregat."
            )

    # ========================================================
    # /ROLES
    # ========================================================

    @app_commands.command(
        name="roles",
        description="Publica el menú d'autoroles."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def roles(
        self,
        interaction: discord.Interaction
    ):

        if not ROLES_ENABLED:

            await interaction.response.send_message(
                "❌ Els autoroles estan desactivats.",
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
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        embed.description = (
            "# 🎨 Autoroles\n\n"

            "Personalitza la teva experiència "
            "i rep informació important "
            "a l'instant.\n\n"

            "Selecciona els rols que vulguis "
            "tenir fent clic als botons de sota."
        )

        embed.set_footer(
            text=(
                "Pots canviar les teves "
                "preferències en qualsevol moment."
            )
        )

        # ----------------------------------------------------
        # ENVIAR
        # ----------------------------------------------------

        await interaction.response.send_message(
            embed=embed,
            view=AutoRolesView()
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Roles(bot)
    )