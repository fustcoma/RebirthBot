import discord
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

LOGS_ENABLED = True

LOG_CHANNEL_ID = 1541046106161684561


# ============================================================
# FUNCIÓ PER ENVIAR LOGS
# ============================================================

async def send_log(
    bot,
    title,
    description,
    color=discord.Color.blurple(),
    fields=None
):

    # --------------------------------------------------------
    # SISTEMA DESACTIVAT
    # --------------------------------------------------------

    if not LOGS_ENABLED:
        return

    # --------------------------------------------------------
    # BUSCAR CANAL
    # --------------------------------------------------------

    channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel is None:

        print(
            f"❌ No trobo el canal de logs "
            f"{LOG_CHANNEL_ID}"
        )

        return

    # --------------------------------------------------------
    # CREAR EMBED
    # --------------------------------------------------------

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )

    # --------------------------------------------------------
    # AFEGIR FIELDS
    # --------------------------------------------------------

    if fields:

        for name, value, inline in fields:

            embed.add_field(
                name=name,
                value=value,
                inline=inline
            )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    embed.set_footer(
        text="RebirthMC Network • Logs"
    )

    # --------------------------------------------------------
    # ENVIAR
    # --------------------------------------------------------

    try:

        await channel.send(
            embed=embed
        )

    except discord.Forbidden:

        print(
            "❌ No tinc permisos per enviar "
            "logs al canal."
        )

    except Exception as error:

        print(
            f"❌ Error enviant log: {error}"
        )


# ============================================================
# COG
# ============================================================

class Logs(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    # ========================================================
    # MEMBRE ENTRA
    # ========================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):

        await send_log(

            self.bot,

            "👋 Membre nou",

            f"{member.mention} ha entrat al servidor.",

            discord.Color.green(),

            [

                (
                    "👤 Usuari",
                    f"{member} (`{member.id}`)",
                    False
                ),

                (
                    "📅 Compte creat",
                    discord.utils.format_dt(
                        member.created_at,
                        style="F"
                    ),
                    False
                )

            ]
        )

    # ========================================================
    # MEMBRE SURT
    # ========================================================

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member
    ):

        await send_log(

            self.bot,

            "🚪 Membre ha sortit",

            f"**{member}** ha sortit del servidor.",

            discord.Color.red(),

            [

                (
                    "👤 Usuari",
                    f"{member} (`{member.id}`)",
                    False
                )

            ]
        )

    # ========================================================
    # CANVI DE ROLS
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before,
        after
    ):

        before_roles = set(
            before.roles
        )

        after_roles = set(
            after.roles
        )

        # ----------------------------------------------------
        # ROLS AFEGITS
        # ----------------------------------------------------

        added_roles = (
            after_roles - before_roles
        )

        # ----------------------------------------------------
        # ROLS TRETS
        # ----------------------------------------------------

        removed_roles = (
            before_roles - after_roles
        )

        # ----------------------------------------------------
        # SI NO HI HA CANVIS
        # ----------------------------------------------------

        if not added_roles and not removed_roles:

            return

        # ----------------------------------------------------
        # DESCRIPCIÓ
        # ----------------------------------------------------

        description = (
            f"Canvis de rols de "
            f"{after.mention}"
        )

        fields = []

        if added_roles:

            added_text = "\n".join(
                role.mention
                for role in added_roles
                if role.name != "@everyone"
            )

            if added_text:

                fields.append(
                    (
                        "➕ Rols afegits",
                        added_text,
                        False
                    )
                )

        if removed_roles:

            removed_text = "\n".join(
                role.mention
                for role in removed_roles
                if role.name != "@everyone"
            )

            if removed_text:

                fields.append(
                    (
                        "➖ Rols eliminats",
                        removed_text,
                        False
                    )
                )

        if not fields:

            return

        await send_log(

            self.bot,

            "🎭 Canvi de rols",

            description,

            discord.Color.orange(),

            fields
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Logs(bot)
    )