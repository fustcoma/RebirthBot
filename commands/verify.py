
import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

VERIFY_ROLE_ID = 1541142866129068082

# ------------------------------------------------------------
# ENLLAÇOS
# ------------------------------------------------------------

WEBSITE_URL = "https://rebirthmc.net"

STORE_URL = "https://store.rebirthmc.net"


# ============================================================
# COLORS
# ============================================================

VERIFY_COLOR = discord.Color.blurple()

RULES_COLOR = discord.Color.blurple()


# ============================================================
# TEXTOS
# ============================================================

VERIFY_TITLE = "🔐 VERIFICACIÓ"

VERIFY_DESCRIPTION = (
    "Benvingut/da al **Discord de RebirthMC**!\n\n"
    "Per poder accedir al servidor, primer t'has de "
    "verificar.\n\n"
    "Prem el botó **✅ Verificar** que trobaràs a "
    "continuació.\n\n"
    "Un cop verificat, rebràs automàticament el rol "
    "corresponent."
)


# ============================================================
# BOTÓ DE VERIFICACIÓ
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
                "❌ Aquest botó només funciona dins "
                "d'un servidor.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # OBTENIR ROL
        # ----------------------------------------------------

        role = interaction.guild.get_role(
            VERIFY_ROLE_ID
        )

        if role is None:

            await interaction.response.send_message(
                "❌ No he pogut trobar el rol de "
                "verificació.",
                ephemeral=True
            )

            print(
                f"❌ No trobo el rol de verificació "
                f"{VERIFY_ROLE_ID}."
            )

            return

        # ----------------------------------------------------
        # COMPROVAR SI JA ESTÀ VERIFICAT
        # ----------------------------------------------------

        if role in interaction.user.roles:

            await interaction.response.send_message(
                "✅ Ja estàs verificat!",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROVAR BOT
        # ----------------------------------------------------

        bot_member = interaction.guild.me

        if bot_member is None:

            await interaction.response.send_message(
                "❌ No he pogut obtenir la informació "
                "del bot.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # COMPROVAR JERARQUIA
        # ----------------------------------------------------

        if role >= bot_member.top_role:

            await interaction.response.send_message(
                "❌ No puc donar-te el rol de verificació "
                "perquè el rol del bot està per sota "
                "d'aquest rol.",
                ephemeral=True
            )

            print(
                f"❌ No puc donar el rol "
                f"'{role.name}'. El rol del bot "
                f"està per sota."
            )

            return

        # ----------------------------------------------------
        # DONAR ROL
        # ----------------------------------------------------

        try:

            await interaction.user.add_roles(
                role,
                reason="Verificació mitjançant botó"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tinc permisos per donar-te "
                "el rol de verificació.",
                ephemeral=True
            )

            print(
                "❌ Discord ha rebutjat l'addició "
                "del rol de verificació."
            )

            return

        except discord.HTTPException as error:

            await interaction.response.send_message(
                "❌ Hi ha hagut un error en verificar-te. "
                "Torna-ho a intentar.",
                ephemeral=True
            )

            print(
                f"❌ Error donant rol de verificació: "
                f"{error}"
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓ
        # ----------------------------------------------------

        await interaction.response.send_message(
            f"🎉 T'has verificat correctament!\n\n"
            f"Has rebut el rol {role.mention}.",
            ephemeral=True
        )


# ============================================================
# VIEW PERSISTENT
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
            "🔐 Sistema de verificació carregat."
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
        # REGISTRAR VIEW PERSISTENT
        # ----------------------------------------------------

        self.bot.add_view(
            VerifyView()
        )

        self.verify_view_added = True

        print(
            "🔐 Botó de verificació persistent carregat."
        )


    # ========================================================
    # /VERIFICAR
    # ========================================================

    @app_commands.command(
        name="verificar",
        description="Publica el missatge de verificació."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def verificar(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # COMPROVAR ADMIN
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Només els administradors poden "
                "utilitzar aquesta comanda.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Aquesta comanda només funciona "
                "dins d'un servidor.",
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
                "❌ No trobo el rol de verificació.\n\n"
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
            name="🛡️ Com funciona?",
            value=(
                "Prem **✅ Verificar** i rebràs "
                "automàticament el rol de verificat."
            ),
            inline=False
        )

        embed.add_field(
            name="📋 Important",
            value=(
                "Abans de participar al servidor, "
                "assegura't d'haver llegit les regles."
            ),
            inline=False
        )

        embed.set_footer(
            text="RebirthMC Network • Verificació"
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
                "❌ No tinc permisos per enviar "
                "missatges en aquest canal.",
                ephemeral=True
            )

            return

        except discord.HTTPException as error:

            print(
                f"❌ Error enviant verificació: "
                f"{error}"
            )

            await interaction.response.send_message(
                "❌ No he pogut publicar el missatge "
                "de verificació.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # CONFIRMACIÓ
        # ----------------------------------------------------

        await interaction.response.send_message(
            "✅ Missatge de verificació publicat.",
            ephemeral=True
        )


    # ========================================================
    # /RULES
    # ========================================================

    @app_commands.command(
        name="rules",
        description="Publica les regles del servidor."
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def rules(
        self,
        interaction: discord.Interaction
    ):

        # ----------------------------------------------------
        # COMPROVAR ADMIN
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Només els administradors poden "
                "utilitzar aquesta comanda.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ Aquesta comanda només funciona "
                "dins d'un servidor.",
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
                "Prohibido amenazar a players o staff "
                "members de DDoS, doxxing y amenazas "
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
        # ENLLAÇOS
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
        # CONFIRMACIÓ
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
