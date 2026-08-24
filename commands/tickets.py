
import asyncio

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

TICKETS_ENABLED = True

# Canal on s'envia el panell
TICKET_PANEL_CHANNEL_ID = 1540805821192085660

# Prefix dels canals
TICKET_NAME_PREFIX = "ticket-"

# Temps abans d'eliminar un ticket
DELETE_DELAY = 2


# ============================================================
# CATEGORIES
# ============================================================

# 🛠️ SUPORT
TICKET_CATEGORY_SUPPORT_ID = 1541010963707465829

# 💰 COMPRES
TICKET_CATEGORY_PURCHASES_ID = 1541010963707465829

# 🚨 REPORT
TICKET_CATEGORY_REPORT_ID = 1541010963707465829

# 👮 STAFF
TICKET_CATEGORY_STAFF_ID = 1541010963707465829

# 🎉 SORTEJOS
# POSA AQUÍ LA ID REAL
TICKET_CATEGORY_GIVEAWAYS_ID = 1541010963707465829


# ============================================================
# TEXTOS
# ============================================================

PANEL_TITLE = "🎫 Sistema de Tickets"

PANEL_DESCRIPTION = (
    "Necessites ajuda?\n\n"
    "Selecciona el tipus de ticket que vols obrir:"
)

CLOSE_BUTTON_TEXT = "Tancar ticket"


# ============================================================
# COLORS
# ============================================================

PANEL_COLOR = discord.Color.blue()

TICKET_COLORS = {

    "support":
        discord.Color.blue(),

    "purchases":
        discord.Color.gold(),

    "report":
        discord.Color.red(),

    "staff":
        discord.Color.purple(),

    "giveaways":
        discord.Color.green()
}


# ============================================================
# INFORMACIÓ DE CATEGORIES
# ============================================================

TICKET_TYPES = {

    # --------------------------------------------------------
    # 🛠️ SUPORT
    # --------------------------------------------------------

    "support": {

        "name": "Suport",

        "emoji": "🛠️",

        "category_id":
            TICKET_CATEGORY_SUPPORT_ID,

        "prefix": "suport"
    },


    # --------------------------------------------------------
    # 💰 COMPRES
    # --------------------------------------------------------

    "purchases": {

        "name": "Compres",

        "emoji": "💰",

        "category_id":
            TICKET_CATEGORY_PURCHASES_ID,

        "prefix": "compra"
    },


    # --------------------------------------------------------
    # 🚨 REPORT
    # --------------------------------------------------------

    "report": {

        "name": "Report",

        "emoji": "🚨",

        "category_id":
            TICKET_CATEGORY_REPORT_ID,

        "prefix": "report"
    },


    # --------------------------------------------------------
    # 👮 STAFF
    # --------------------------------------------------------

    "staff": {

        "name": "Staff",

        "emoji": "👮",

        "category_id":
            TICKET_CATEGORY_STAFF_ID,

        "prefix": "staff"
    },


    # --------------------------------------------------------
    # 🎉 SORTEJOS
    # --------------------------------------------------------

    "giveaways": {

        "name": "Sortejos",

        "emoji": "🎉",

        "category_id":
            TICKET_CATEGORY_GIVEAWAYS_ID,

        "prefix": "sorteig"
    }
}


# ============================================================
# COMPROVAR STAFF
# ============================================================

def is_staff(member: discord.Member):

    return member.guild_permissions.manage_channels


# ============================================================
# BOTÓ TANCAR
# ============================================================

class CloseTicketButton(discord.ui.Button):

    def __init__(self):

        super().__init__(

            label=CLOSE_BUTTON_TEXT,

            emoji="🔒",

            style=discord.ButtonStyle.danger,

            custom_id="ticket_close"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.channel


        # ----------------------------------------------------
        # COMPROVAR QUE ÉS UN TICKET
        # ----------------------------------------------------

        if not channel.name.startswith(
            TICKET_NAME_PREFIX
        ):

            await interaction.response.send_message(

                "❌ Aquest canal no és un ticket.",

                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # CREATOR ID
        # ----------------------------------------------------

        creator_id = channel.topic


        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------

        if not is_staff(interaction.user):

            if (

                creator_id is None

                or
                str(interaction.user.id)
                != creator_id

            ):

                await interaction.response.send_message(

                    "❌ Només el creador del ticket "
                    "o el staff pot tancar-lo.",

                    ephemeral=True
                )

                return


        # ----------------------------------------------------
        # AVÍS
        # ----------------------------------------------------

        await interaction.response.send_message(

            f"🔒 Aquest ticket es tancarà en "
            f"**{DELETE_DELAY} segons**..."
        )


        # ----------------------------------------------------
        # ESPERAR
        # ----------------------------------------------------

        await asyncio.sleep(
            DELETE_DELAY
        )


        # ----------------------------------------------------
        # ELIMINAR
        # ----------------------------------------------------

        try:

            await channel.delete(

                reason=(
                    f"Ticket tancat per "
                    f"{interaction.user}"
                )
            )

        except discord.NotFound:

            pass

        except discord.Forbidden:

            print(

                f"❌ No puc eliminar "
                f"{channel.name}"
            )


# ============================================================
# VIEW DEL TICKET
# ============================================================

class TicketView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            CloseTicketButton()
        )


# ============================================================
# CREAR TICKET
# ============================================================

async def create_ticket(

    interaction: discord.Interaction,

    ticket_type: str

):

    guild = interaction.guild

    member = interaction.user

    data = TICKET_TYPES[ticket_type]

    category_id = data["category_id"]


    # --------------------------------------------------------
    # COMPROVAR CATEGORIA CONFIGURADA
    # --------------------------------------------------------

    if not category_id:

        await interaction.response.send_message(

            f"❌ La categoria de "
            f"**{data['name']}** encara no està configurada.",

            ephemeral=True
        )

        print(

            f"❌ Falta configurar la categoria "
            f"{data['name']}."
        )

        return


    # --------------------------------------------------------
    # BUSCAR CATEGORIA
    # --------------------------------------------------------

    category = guild.get_channel(
        category_id
    )

    if category is None:

        await interaction.response.send_message(

            f"❌ No he trobat la categoria de "
            f"**{data['name']}**.",

            ephemeral=True
        )

        return


    # --------------------------------------------------------
    # COMPROVAR SI JA TÉ TICKET
    # --------------------------------------------------------

    for channel in category.channels:

        if channel.topic == str(member.id):

            await interaction.response.send_message(

                f"❌ Ja tens un ticket obert de "
                f"**{data['name']}**: "
                f"{channel.mention}",

                ephemeral=True
            )

            return


    # --------------------------------------------------------
    # RESPONDRE
    # --------------------------------------------------------

    await interaction.response.defer(
        ephemeral=True
    )


    # --------------------------------------------------------
    # NOM DEL CANAL
    # --------------------------------------------------------

    username = member.name.lower()[:20]

    channel_name = (

        f"{TICKET_NAME_PREFIX}"

        f"{data['prefix']}-"

        f"{username}"
    )


    # --------------------------------------------------------
    # PERMISOS
    # --------------------------------------------------------

    overwrites = {

        guild.default_role:

            discord.PermissionOverwrite(

                view_channel=False
            ),


        member:

            discord.PermissionOverwrite(

                view_channel=True,

                send_messages=True,

                read_message_history=True,

                attach_files=True
            ),


        guild.me:

            discord.PermissionOverwrite(

                view_channel=True,

                send_messages=True,

                manage_channels=True,

                manage_messages=True,

                read_message_history=True
            )
    }


    # --------------------------------------------------------
    # CREAR CANAL
    # --------------------------------------------------------

    try:

        ticket_channel = (

            await guild.create_text_channel(

                name=channel_name,

                category=category,

                topic=str(member.id),

                overwrites=overwrites,

                reason=(

                    f"Ticket de "
                    f"{data['name']} "
                    f"creat per {member}"
                )
            )
        )

    except discord.Forbidden:

        await interaction.followup.send(

            "❌ No tinc permisos per crear "
            "canals.",

            ephemeral=True
        )

        return


    except Exception as error:

        print(

            f"❌ Error creant ticket: "
            f"{error}"
        )

        await interaction.followup.send(

            "❌ Hi ha hagut un error creant "
            "el ticket.",

            ephemeral=True
        )

        return


    # ========================================================
    # EMBED
    # ========================================================

    embed = discord.Embed(

        title=(

            f"{data['emoji']} "
            f"Ticket de {data['name']}"
        ),

        description=(

            f"Hola {member.mention}!\n\n"

            f"Has obert un ticket de "
            f"**{data['name']}**.\n\n"

            "Explica el teu problema o pregunta "
            "i un membre de l'equip t'ajudarà."
        ),

        color=TICKET_COLORS[
            ticket_type
        ]
    )


    # --------------------------------------------------------
    # USUARI
    # --------------------------------------------------------

    embed.add_field(

        name="👤 Usuari",

        value=member.mention,

        inline=True
    )


    # --------------------------------------------------------
    # CATEGORIA
    # --------------------------------------------------------

    embed.add_field(

        name="📁 Categoria",

        value=(

            f"{data['emoji']} "
            f"{data['name']}"
        ),

        inline=True
    )


    # --------------------------------------------------------
    # TICKET
    # --------------------------------------------------------

    embed.add_field(

        name="🎫 Ticket",

        value=f"`{ticket_channel.name}`",

        inline=False
    )


    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    embed.set_footer(

        text=(

            "Quan ja no necessitis ajuda, "
            "prem 🔒 Tancar ticket."
        )
    )


    # --------------------------------------------------------
    # ENVIAR
    # --------------------------------------------------------

    try:

        await ticket_channel.send(

            content=member.mention,

            embed=embed,

            view=TicketView()
        )

    except discord.Forbidden:

        print(

            f"❌ No puc enviar el missatge "
            f"a {ticket_channel.name}"
        )


    # --------------------------------------------------------
    # CONFIRMACIÓ
    # --------------------------------------------------------

    await interaction.followup.send(

        f"✅ Ticket de **{data['name']}** creat: "
        f"{ticket_channel.mention}",

        ephemeral=True
    )


    print(

        f"🎫 Ticket creat: "
        f"{ticket_channel.name} "
        f"({data['name']}) "
        f"per {member}"
    )


# ============================================================
# 🛠️ BOTÓ SUPORT
# ============================================================

class SupportTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Suport",

            emoji="🛠️",

            style=discord.ButtonStyle.primary,

            custom_id="ticket_support"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(

            interaction,

            "support"
        )


# ============================================================
# 💰 BOTÓ COMPRES
# ============================================================

class PurchasesTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Compres",

            emoji="💰",

            style=discord.ButtonStyle.success,

            custom_id="ticket_purchases"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(

            interaction,

            "purchases"
        )


# ============================================================
# 🚨 BOTÓ REPORT
# ============================================================

class ReportTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Report",

            emoji="🚨",

            style=discord.ButtonStyle.danger,

            custom_id="ticket_report"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(

            interaction,

            "report"
        )


# ============================================================
# 👮 BOTÓ STAFF
# ============================================================

class StaffTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Staff",

            emoji="👮",

            style=discord.ButtonStyle.secondary,

            custom_id="ticket_staff"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(

            interaction,

            "staff"
        )


# ============================================================
# 🎉 BOTÓ SORTEJOS
# ============================================================

class GiveawaysTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Sortejos",

            emoji="🎉",

            style=discord.ButtonStyle.success,

            custom_id="ticket_giveaways"
        )


    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await create_ticket(

            interaction,

            "giveaways"
        )


# ============================================================
# PANEL DE TICKETS
# ============================================================

class TicketPanel(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


        # ----------------------------------------------------
        # FILA 1
        # ----------------------------------------------------

        self.add_item(
            SupportTicketButton()
        )

        self.add_item(
            PurchasesTicketButton()
        )

        self.add_item(
            ReportTicketButton()
        )

        self.add_item(
            StaffTicketButton()
        )


        # ----------------------------------------------------
        # FILA 2
        # ----------------------------------------------------

        self.add_item(
            GiveawaysTicketButton()
        )


# ============================================================
# COG
# ============================================================

class Tickets(commands.Cog):

    def __init__(self, bot):

        self.bot = bot


    # ========================================================
    # BOTONS PERSISTENTS
    # ========================================================

    async def cog_load(self):

        self.bot.add_view(
            TicketPanel()
        )

        self.bot.add_view(
            TicketView()
        )

        print(
            "🎫 Botons de tickets persistents carregats."
        )


    # ========================================================
    # /ticketpanel
    # ========================================================

    @app_commands.command(

        name="ticketpanel",

        description=(
            "Envia el panell per obrir tickets."
        )
    )

    @app_commands.default_permissions(
        manage_channels=True
    )

    async def ticketpanel(

        self,

        interaction: discord.Interaction

    ):

        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------

        if not interaction.user.guild_permissions.manage_channels:

            await interaction.response.send_message(

                "❌ No tens permís per fer això.",

                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ACTIVAT
        # ----------------------------------------------------

        if not TICKETS_ENABLED:

            await interaction.response.send_message(

                "❌ Els tickets estan desactivats.",

                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------

        channel = interaction.guild.get_channel(

            TICKET_PANEL_CHANNEL_ID
        )

        if channel is None:

            await interaction.response.send_message(

                "❌ No he trobat el canal del panell.",

                ephemeral=True
            )

            return


        # ====================================================
        # EMBED
        # ====================================================

        embed = discord.Embed(

            title=PANEL_TITLE,

            description=PANEL_DESCRIPTION,

            color=PANEL_COLOR
        )


        # ----------------------------------------------------
        # SUPORT
        # ----------------------------------------------------

        embed.add_field(

            name="🛠️ Suport",

            value=(

                "Problemes, dubtes o ajuda "
                "general."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # COMPRES
        # ----------------------------------------------------

        embed.add_field(

            name="💰 Compres",

            value=(

                "Compres, pagaments o problemes "
                "amb productes."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # REPORT
        # ----------------------------------------------------

        embed.add_field(

            name="🚨 Report",

            value=(

                "Reportar usuaris o problemes "
                "al servidor."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # STAFF
        # ----------------------------------------------------

        embed.add_field(

            name="👮 Staff",

            value=(

                "Contactar directament amb "
                "l'equip de staff."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # SORTEJOS
        # ----------------------------------------------------

        embed.add_field(

            name="🎉 Sortejos",

            value=(

                "Problemes o consultes "
                "relacionades amb sorteigs."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        embed.set_footer(

            text=(
                "Sistema de tickets • "
                "RebirthMC Network"
            )
        )


        # ====================================================
        # ENVIAR
        # ====================================================

        await channel.send(

            embed=embed,

            view=TicketPanel()
        )


        await interaction.response.send_message(

            f"✅ Panell enviat a "
            f"{channel.mention}",

            ephemeral=True
        )


        print(

            f"🎫 Panell de tickets enviat a "
            f"#{channel.name}"
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Tickets(bot)
    )

