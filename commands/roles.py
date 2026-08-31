import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

ROLES_ENABLED = True


# ============================================================
# IDS DE LOS ROLES
# ============================================================

ROLE_SORTEJOS = 1541002745773957162
ROLE_EVENTS = 1541007380735590420
ROLE_ACTUALITZACIONS = 1541007515502907432
ROLE_APLICACIO = 1541007404588859442


# ============================================================
# VIEW DE LOS AUTOROLES
# ============================================================

class AutoRolesView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    # ========================================================
    # 🏆 SORTEOS
    # ========================================================

    @discord.ui.button(
        label="Sorteos",
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
            "sorteos"
        )

    # ========================================================
    # 📅 EVENTOS
    # ========================================================

    @discord.ui.button(
        label="Eventos",
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
            "los eventos"
        )

    # ========================================================
    # 🗂️ ACTUALIZACIONES
    # ========================================================

    @discord.ui.button(
        label="Actualizaciones",
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
            "las actualizaciones"
        )

    # ========================================================
    # 💼 APLICACIÓN
    # ========================================================

    @discord.ui.button(
        label="Aplicación",
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
            "las aplicaciones"
        )

    # ========================================================
    # DAR / QUITAR ROL
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
                "❌ Este botón solo funciona "
                "dentro de un servidor.",
                ephemeral=True
            )

            return

        role = guild.get_role(
            role_id
        )

        if role is None:

            await interaction.response.send_message(
                "❌ No he podido encontrar este rol.",
                ephemeral=True
            )

            return

        member = interaction.user

        # ====================================================
        # YA TIENE EL ROL → QUITAR
        # ====================================================

        if role in member.roles:

            try:

                await member.remove_roles(
                    role,
                    reason="Autorol"
                )

                await interaction.response.send_message(
                    f"❌ Ya no recibirás notificaciones de "
                    f"**{role_name}**.",
                    ephemeral=True
                )

            except discord.Forbidden:

                await interaction.response.send_message(
                    "❌ No puedo quitarte este rol.\n"
                    "Comprueba que mi rol esté "
                    "por encima de este rol.",
                    ephemeral=True
                )

            return

        # ====================================================
        # NO TIENE EL ROL → DAR
        # ====================================================

        try:

            await member.add_roles(
                role,
                reason="Autorol"
            )

            await interaction.response.send_message(
                f"✅ ¡Ahora recibirás notificaciones de "
                f"**{role_name}**!",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puedo darte este rol.\n"
                "Comprueba que mi rol esté "
                "por encima de este rol.",
                ephemeral=True
            )


# ============================================================
# COG
# ============================================================

class Roles(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    # ========================================================
    # CARGAR VIEW PERSISTENTE
    # ========================================================

    async def cog_load(self):

        if ROLES_ENABLED:

            self.bot.add_view(
                AutoRolesView()
            )

            print(
                "🎨 Sistema de autoroles cargado."
            )

    # ========================================================
    # /ROLES
    # ========================================================

    @app_commands.command(
        name="roles",
        description="Publica el menú de autoroles."
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
                "❌ Los autoroles están desactivados.",
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
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            color=discord.Color.blurple()
        )

        embed.description = (
            "# 🎨 Autoroles\n\n"

            "Personaliza tu experiencia "
            "y recibe información importante "
            "al instante.\n\n"

            "Selecciona los roles que quieras "
            "tener haciendo clic en los botones de abajo."
        )

        embed.set_footer(
            text=(
                "Puedes cambiar tus "
                "preferencias en cualquier momento."
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