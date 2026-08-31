import asyncio

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

TICKETS_ENABLED = True

# Canal donde se envía el panel
TICKET_PANEL_CHANNEL_ID = 1540805821192085660

# Prefijo de los canales
TICKET_NAME_PREFIX = "ticket-"

# Tiempo antes de eliminar un ticket
DELETE_DELAY = 2


# ============================================================
# CATEGORÍAS
# ============================================================

# 🛠️ SOPORTE
TICKET_CATEGORY_SUPPORT_ID = 1541010963707465829

# 💰 COMPRAS
TICKET_CATEGORY_PURCHASES_ID = 1541010963707465829

# 🚨 REPORTE
TICKET_CATEGORY_REPORT_ID = 1541010963707465829

# 👮 STAFF
TICKET_CATEGORY_STAFF_ID = 1541010963707465829

# 🎉 SORTEOS
# PON AQUÍ LA ID REAL
TICKET_CATEGORY_GIVEAWAYS_ID = 1541010963707465829


# ============================================================
# TEXTOS
# ============================================================

PANEL_TITLE = "🎫 Sistema de Tickets"

PANEL_DESCRIPTION = (
    "¿Necesitas ayuda?\n\n"
    "Selecciona el tipo de ticket que deseas abrir:"
)

CLOSE_BUTTON_TEXT = "Cerrar ticket"


# ============================================================
# COLORES
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
# INFORMACIÓN DE CATEGORÍAS
# ============================================================

TICKET_TYPES = {

    # --------------------------------------------------------
    # 🛠️ SOPORTE
    # --------------------------------------------------------

    "support": {

        "name": "Soporte",

        "emoji": "🛠️",

        "category_id":
            TICKET_CATEGORY_SUPPORT_ID,

        "prefix": "soporte"
    },


    # --------------------------------------------------------
    # 💰 COMPRAS
    # --------------------------------------------------------

    "purchases": {

        "name": "Compras",

        "emoji": "💰",

        "category_id":
            TICKET_CATEGORY_PURCHASES_ID,

        "prefix": "compra"
    },


    # --------------------------------------------------------
    # 🚨 REPORTE
    # --------------------------------------------------------

    "report": {

        "name": "Reporte",

        "emoji": "🚨",

        "category_id":
            TICKET_CATEGORY_REPORT_ID,

        "prefix": "reporte"
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
    # 🎉 SORTEOS
    # --------------------------------------------------------

    "giveaways": {

        "name": "Sorteos",

        "emoji": "🎉",

        "category_id":
            TICKET_CATEGORY_GIVEAWAYS_ID,

        "prefix": "sorteo"
    }
}


# ============================================================
# COMPROBAR STAFF
# ============================================================

def is_staff(member: discord.Member):

    return member.guild_permissions.manage_channels


# ============================================================
# BOTÓN CERRAR
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
        # COMPROBAR QUE ES UN TICKET
        # ----------------------------------------------------

        if not channel.name.startswith(
            TICKET_NAME_PREFIX
        ):

            await interaction.response.send_message(

                "❌ Este canal no es un ticket.",

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

                    "❌ Solo el creador del ticket "
                    "o el staff puede cerrarlo.",

                    ephemeral=True
                )

                return


        # ----------------------------------------------------
        # AVISO
        # ----------------------------------------------------

        await interaction.response.send_message(

            f"🔒 Este ticket se cerrará en "
            f"**{DELETE_DELAY} segundos**..."
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
                    f"Ticket cerrado por "
                    f"{interaction.user}"
                )
            )

        except discord.NotFound:

            pass

        except discord.Forbidden:

            print(

                f"❌ No puedo eliminar "
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
    # COMPROBAR CATEGORÍA CONFIGURADA
    # --------------------------------------------------------

    if not category_id:

        await interaction.response.send_message(

            f"❌ La categoría de "
            f"**{data['name']}** aún no está configurada.",

            ephemeral=True
        )

        print(

            f"❌ Falta configurar la categoría "
            f"{data['name']}."
        )

        return


    # --------------------------------------------------------
    # BUSCAR CATEGORÍA
    # --------------------------------------------------------

    category = guild.get_channel(
        category_id
    )

    if category is None:

        await interaction.response.send_message(

            f"❌ No he encontrado la categoría de "
            f"**{data['name']}**.",

            ephemeral=True
        )

        return


    # --------------------------------------------------------
    # COMPROBAR SI YA TIENE TICKET
    # --------------------------------------------------------

    for channel in category.channels:

        if channel.topic == str(member.id):

            await interaction.response.send_message(

                f"❌ Ya tienes un ticket abierto de "
                f"**{data['name']}**: "
                f"{channel.mention}",

                ephemeral=True
            )

            return


    # --------------------------------------------------------
    # RESPONDER
    # --------------------------------------------------------

    await interaction.response.defer(
        ephemeral=True
    )


    # --------------------------------------------------------
    # NOMBRE DEL CANAL
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
                    f"creado por {member}"
                )
            )
        )

    except discord.Forbidden:

        await interaction.followup.send(

            "❌ No tengo permisos para crear "
            "canales.",

            ephemeral=True
        )

        return


    except Exception as error:

        print(

            f"❌ Error creando ticket: "
            f"{error}"
        )

        await interaction.followup.send(

            "❌ Ha ocurrido un error creando "
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

            f"¡Hola {member.mention}!\n\n"

            f"Has abierto un ticket de "
            f"**{data['name']}**.\n\n"

            "Explica tu problema o pregunta "
            "y un miembro del equipo te atenderá."
        ),

        color=TICKET_COLORS[
            ticket_type
        ]
    )


    # --------------------------------------------------------
    # USUARIO
    # --------------------------------------------------------

    embed.add_field(

        name="👤 Usuario",

        value=member.mention,

        inline=True
    )


    # --------------------------------------------------------
    # CATEGORÍA
    # --------------------------------------------------------

    embed.add_field(

        name="📁 Categoría",

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

            "Cuando ya no necesites ayuda, "
            "presiona 🔒 Cerrar ticket."
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

            f"❌ No puedo enviar el mensaje "
            f"a {ticket_channel.name}"
        )


    # --------------------------------------------------------
    # CONFIRMACIÓN
    # --------------------------------------------------------

    await interaction.followup.send(

        f"✅ Ticket de **{data['name']}** creado: "
        f"{ticket_channel.mention}",

        ephemeral=True
    )


    print(

        f"🎫 Ticket creado: "
        f"{ticket_channel.name} "
        f"({data['name']}) "
        f"por {member}"
    )


# ============================================================
# 🛠️ BOTÓN SOPORTE
# ============================================================

class SupportTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Soporte",

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
# 💰 BOTÓN COMPRAS
# ============================================================

class PurchasesTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Compras",

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
# 🚨 BOTÓN REPORTE
# ============================================================

class ReportTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Reporte",

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
# 👮 BOTÓN STAFF
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
# 🎉 BOTÓN SORTEOS
# ============================================================

class GiveawaysTicketButton(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(

            label="Sorteos",

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
    # BOTONES PERSISTENTES
    # ========================================================

    async def cog_load(self):

        self.bot.add_view(
            TicketPanel()
        )

        self.bot.add_view(
            TicketView()
        )

        print(
            "🎫 Botones de tickets persistentes cargados."
        )


    # ========================================================
    # /ticketpanel
    # ========================================================

    @app_commands.command(

        name="ticketpanel",

        description=(
            "Envía el panel para abrir tickets."
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

                "❌ No tienes permiso para hacer esto.",

                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ACTIVADO
        # ----------------------------------------------------

        if not TICKETS_ENABLED:

            await interaction.response.send_message(

                "❌ Los tickets están desactivados.",

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

                "❌ No he encontrado el canal del panel.",

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
        # SOPORTE
        # ----------------------------------------------------

        embed.add_field(

            name="🛠️ Soporte",

            value=(

                "Problemas, dudas o ayuda "
                "general."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # COMPRAS
        # ----------------------------------------------------

        embed.add_field(

            name="💰 Compras",

            value=(

                "Compras, pagos o problemas "
                "con productos."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # REPORTE
        # ----------------------------------------------------

        embed.add_field(

            name="🚨 Reporte",

            value=(

                "Reportar usuarios o problemas "
                "en el servidor."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # STAFF
        # ----------------------------------------------------

        embed.add_field(

            name="👮 Staff",

            value=(

                "Contactar directamente con "
                "el equipo de staff."
            ),

            inline=True
        )


        # ----------------------------------------------------
        # SORTEOS
        # ----------------------------------------------------

        embed.add_field(

            name="🎉 Sorteos",

            value=(

                "Problemas o consultas "
                "relacionadas con sorteos."
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

            f"✅ Panel enviado a "
            f"{channel.mention}",

            ephemeral=True
        )


        print(

            f"🎫 Panel de tickets enviado a "
            f"#{channel.name}"
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Tickets(bot)
    )