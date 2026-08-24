import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓ
# ============================================================

load_dotenv()

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()

intents.message_content = True

intents.members = True


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(

    command_prefix="!",

    intents=intents
)


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print(
        f"✅ Connectat com {bot.user}"
    )

    try:

        synced = await bot.tree.sync()

        print(
            f"🔄 {len(synced)} slash commands "
            f"sincronitzades"
        )

    except Exception as error:

        print(
            f"❌ Error sincronitzant slash commands: "
            f"{error}"
        )


# ============================================================
# CARREGAR EXTENSIONS
# ============================================================

async def load_extensions():

    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    await bot.load_extension(
        "commands.fun"
    )

    await bot.load_extension(
        "commands.moderation"
    )

    await bot.load_extension(
        "commands.tickets"
    )

    await bot.load_extension(
        "commands.giveaways"
    )
    await bot.load_extension(
        "commands.roles"
    )
    await bot.load_extension(
        "commands.ip"
    )
    await bot.load_extension(
        "events.suggestions"
        )
    await bot.load_extension(
    "commands.postulacion"
    )
    await bot.load_extension(
    "commands.levels"
    )
    await bot.load_extension(
    "events.logs"
    ) 
    print("🔎 Intentant carregar AutoMod...")

    await bot.load_extension(
        "commands.automod"
    )
    await bot.load_extension(
            "commands.verify"
    )
    await bot.load_extension(
                "events.boost"
    )

    print("✅ AutoMod carregat des de bot.py")   


    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    await bot.load_extension(
        "events.welcome"
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    async with bot:

        await load_extensions()

        await bot.start(
            TOKEN
        )


# ============================================================
# EXECUTAR
# ============================================================

asyncio.run(main())