
import discord
from discord.ext import commands


# ============================================================
# CONFIGURACIÓ
# ============================================================

# Rol que reben els boosters
BOOSTER_ROLE_ID = 1541155895390769193


# ============================================================
# COG
# ============================================================

class Booster(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ========================================================
    # BOOST / UNBOOST
    # ========================================================

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):

        # ----------------------------------------------------
        # COMPROVAR SI HA COMENÇAT A FER BOOST
        # ----------------------------------------------------

        if before.premium_since is None and after.premium_since is not None:

            role = after.guild.get_role(
                BOOSTER_ROLE_ID
            )

            if role is None:
                print(
                    f"❌ No trobo el rol de Booster "
                    f"({BOOSTER_ROLE_ID})"
                )
                return

            # Ja té el rol
            if role in after.roles:
                return

            try:

                await after.add_roles(
                    role,
                    reason="Ha fet Boost al servidor"
                )

                print(
                    f"🚀 {after} ha fet Boost i "
                    f"ha rebut el rol {role.name}."
                )

            except discord.Forbidden:

                print(
                    "❌ No tinc permisos per donar "
                    "el rol de Booster."
                )

            except discord.HTTPException as error:

                print(
                    f"❌ Error donant el rol de Booster: "
                    f"{error}"
                )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Booster(bot)
    )

