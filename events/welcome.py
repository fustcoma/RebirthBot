import aiohttp
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURACIÓ
# ============================================================

# Activar / desactivar el welcome
WELCOME_ENABLED = True

# Canal del welcome
WELCOME_CHANNEL_ID = 1540758633216872468

# Rol que es dona automàticament
WELCOME_ROLE_ID = 1540758763307274289


# ============================================================
# ESTAT DEL WELCOME
# ============================================================

# Guardem aquí l'última vegada que el bot va comprovar
# els membres del servidor.

WELCOME_STATE_FILE = (
    Path(__file__).parent.parent
    / "database"
    / "welcome_state.json"
)


# ============================================================
# IMATGE
# ============================================================

IMAGE_WIDTH = 700
IMAGE_HEIGHT = 260


# ============================================================
# FONS
# ============================================================

# None = utilitzar un color
#
# Exemple:
#
# BACKGROUND_IMAGE = "assets/welcome_background.png"

BACKGROUND_IMAGE = None

BACKGROUND_COLOR = (20, 20, 25)


# ============================================================
# AVATAR
# ============================================================

AVATAR_SIZE = 105

AVATAR_Y = 20

AVATAR_BORDER_WIDTH = 5

AVATAR_BORDER_COLOR = (
    255,
    255,
    255
)


# ============================================================
# TEXT PRINCIPAL
# ============================================================

JOIN_TEXT_SIZE = 28

JOIN_TEXT_COLOR = (
    255,
    255,
    255
)

JOIN_TEXT_Y = 140


# ============================================================
# MEMBRE #N
# ============================================================

MEMBER_TEXT_SIZE = 21

MEMBER_TEXT_COLOR = (
    190,
    190,
    190
)

MEMBER_TEXT_Y = 185


# ============================================================
# FONT
# ============================================================

# Exemple:
#
# FONT_PATH = "assets/font.ttf"

FONT_PATH = None


# ============================================================
# MISSATGE
# ============================================================

WELCOME_MESSAGE = (
    "Hola {member}, benvingut a **{server}**!"
)


# ============================================================
# ESTAT
# ============================================================

def load_welcome_state():

    # Si no existeix el fitxer, retornem un diccionari buit.

    if not WELCOME_STATE_FILE.exists():

        return {}

    try:

        with open(
            WELCOME_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"❌ Error carregant l'estat del welcome: "
            f"{error}"
        )

        return {}


def save_welcome_state(state):

    try:

        WELCOME_STATE_FILE.parent.mkdir(
            exist_ok=True
        )

        with open(
            WELCOME_STATE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                indent=4
            )

    except Exception as error:

        print(
            f"❌ Error guardant l'estat del welcome: "
            f"{error}"
        )


# ============================================================
# FONT
# ============================================================

def get_font(size):

    if FONT_PATH is not None:

        if os.path.exists(FONT_PATH):

            return ImageFont.truetype(
                FONT_PATH,
                size
            )

    windows_font = "C:/Windows/Fonts/arial.ttf"

    if os.path.exists(windows_font):

        return ImageFont.truetype(
            windows_font,
            size
        )

    return ImageFont.load_default()


# ============================================================
# CREAR IMATGE
# ============================================================

def create_welcome_image(
    avatar_bytes,
    username,
    member_number
):

    # --------------------------------------------------------
    # FONS
    # --------------------------------------------------------

    if (
        BACKGROUND_IMAGE is not None
        and os.path.exists(BACKGROUND_IMAGE)
    ):

        background = Image.open(
            BACKGROUND_IMAGE
        ).convert("RGB")

        background = background.resize(
            (
                IMAGE_WIDTH,
                IMAGE_HEIGHT
            )
        )

    else:

        background = Image.new(
            "RGB",
            (
                IMAGE_WIDTH,
                IMAGE_HEIGHT
            ),
            BACKGROUND_COLOR
        )


    draw = ImageDraw.Draw(
        background
    )


    # --------------------------------------------------------
    # AVATAR
    # --------------------------------------------------------

    avatar = Image.open(
        io.BytesIO(avatar_bytes)
    ).convert("RGBA")

    avatar = avatar.resize(
        (
            AVATAR_SIZE,
            AVATAR_SIZE
        ),
        Image.Resampling.LANCZOS
    )


    # Màscara circular

    mask = Image.new(
        "L",
        (
            AVATAR_SIZE,
            AVATAR_SIZE
        ),
        0
    )

    mask_draw = ImageDraw.Draw(
        mask
    )

    mask_draw.ellipse(
        (
            0,
            0,
            AVATAR_SIZE,
            AVATAR_SIZE
        ),
        fill=255
    )


    # Posició centrada

    avatar_x = (
        IMAGE_WIDTH -
        AVATAR_SIZE
    ) // 2

    avatar_y = AVATAR_Y


    # --------------------------------------------------------
    # BORDA DE L'AVATAR
    # --------------------------------------------------------

    draw.ellipse(
        (
            avatar_x - AVATAR_BORDER_WIDTH,
            avatar_y - AVATAR_BORDER_WIDTH,

            avatar_x +
            AVATAR_SIZE +
            AVATAR_BORDER_WIDTH,

            avatar_y +
            AVATAR_SIZE +
            AVATAR_BORDER_WIDTH
        ),
        fill=AVATAR_BORDER_COLOR
    )


    # --------------------------------------------------------
    # POSAR AVATAR
    # --------------------------------------------------------

    background.paste(
        avatar,
        (
            avatar_x,
            avatar_y
        ),
        mask
    )


    # --------------------------------------------------------
    # FONTS
    # --------------------------------------------------------

    join_font = get_font(
        JOIN_TEXT_SIZE
    )

    member_font = get_font(
        MEMBER_TEXT_SIZE
    )


    # --------------------------------------------------------
    # TEXT PRINCIPAL
    # --------------------------------------------------------

    join_text = (
        f"{username} s'ha unit al server"
    )

    bbox = draw.textbbox(
        (0, 0),
        join_text,
        font=join_font
    )

    text_width = (
        bbox[2] -
        bbox[0]
    )

    join_x = (
        IMAGE_WIDTH -
        text_width
    ) // 2

    draw.text(
        (
            join_x,
            JOIN_TEXT_Y
        ),
        join_text,
        font=join_font,
        fill=JOIN_TEXT_COLOR
    )


    # --------------------------------------------------------
    # MEMBRE
    # --------------------------------------------------------

    member_text = (
        f"Membre #{member_number}"
    )

    bbox = draw.textbbox(
        (0, 0),
        member_text,
        font=member_font
    )

    text_width = (
        bbox[2] -
        bbox[0]
    )

    member_x = (
        IMAGE_WIDTH -
        text_width
    ) // 2

    draw.text(
        (
            member_x,
            MEMBER_TEXT_Y
        ),
        member_text,
        font=member_font,
        fill=MEMBER_TEXT_COLOR
    )


    # --------------------------------------------------------
    # GUARDAR A MEMÒRIA
    # --------------------------------------------------------

    output = io.BytesIO()

    background.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return output


# ============================================================
# WELCOME COG
# ============================================================

class Welcome(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        # Estat persistent
        self.welcome_state = load_welcome_state()


    # ========================================================
    # ENVIAR WELCOME
    # ========================================================

    async def send_welcome(
        self,
        member
    ):

        # ----------------------------------------------------
        # SISTEMA ACTIVAT?
        # ----------------------------------------------------

        if not WELCOME_ENABLED:
            return False


        # ====================================================
        # DONAR ROL
        # ====================================================

        role = member.guild.get_role(
            WELCOME_ROLE_ID
        )

        if role is None:

            print(
                f"❌ No he trobat el rol "
                f"{WELCOME_ROLE_ID}"
            )

        else:

            try:

                # Només el donem si encara no el té.

                if role not in member.roles:

                    await member.add_roles(
                        role,
                        reason="Rol automàtic de benvinguda"
                    )

                    print(
                        f"🎭 Rol {role.name} donat a "
                        f"{member}"
                    )

            except discord.Forbidden:

                print(
                    f"❌ No puc donar el rol "
                    f"{role.name} a {member}."
                )

                print(
                    "Comprova que el rol del bot "
                    "estigui per sobre del rol."
                )

            except Exception as error:

                print(
                    f"❌ Error donant el rol: {error}"
                )


        # ====================================================
        # BUSCAR CANAL
        # ====================================================

        channel = member.guild.get_channel(
            WELCOME_CHANNEL_ID
        )

        if channel is None:

            print(
                f"❌ No he trobat el canal "
                f"{WELCOME_CHANNEL_ID}"
            )

            return False


        # ====================================================
        # AVATAR
        # ====================================================

        avatar_url = member.display_avatar.replace(
            size=256
        ).url


        # ====================================================
        # DESCARREGAR AVATAR
        # ====================================================

        try:

            async with aiohttp.ClientSession() as session:

                async with session.get(
                    avatar_url
                ) as response:

                    if response.status != 200:

                        print(
                            "❌ No he pogut descarregar "
                            "l'avatar."
                        )

                        return False

                    avatar_bytes = await response.read()

        except Exception as error:

            print(
                f"❌ Error descarregant l'avatar: "
                f"{error}"
            )

            return False


        # ====================================================
        # CREAR IMATGE
        # ====================================================

        try:

            welcome_image = create_welcome_image(
                avatar_bytes,
                member.display_name,
                member.guild.member_count
            )

        except Exception as error:

            print(
                f"❌ Error creant la welcome card: "
                f"{error}"
            )

            return False


        # ====================================================
        # MISSATGE
        # ====================================================

        message = WELCOME_MESSAGE.format(
            member=member.mention,
            server=member.guild.name
        )


        # ====================================================
        # ENVIAR
        # ====================================================

        try:

            file = discord.File(
                welcome_image,
                filename="welcome.png"
            )

            await channel.send(
                content=message,
                file=file
            )

            print(
                f"👋 Welcome enviat per {member}"
            )

            return True

        except discord.Forbidden:

            print(
                f"❌ No tinc permisos per enviar "
                f"missatges a {channel.name}"
            )

        except Exception as error:

            print(
                f"❌ Error enviant welcome: {error}"
            )

        return False


    # ========================================================
    # COMPROVAR MEMBRES PERDUTS
    # ========================================================

    async def check_missed_members(
        self,
        guild
    ):

        if not WELCOME_ENABLED:
            return


        # ----------------------------------------------------
        # Hora actual
        # ----------------------------------------------------

        now = datetime.now(
            timezone.utc
        )


        # ----------------------------------------------------
        # Buscar última comprovació
        # ----------------------------------------------------

        guild_key = str(
            guild.id
        )

        last_check_string = (
            self.welcome_state.get(
                guild_key
            )
        )


        # ----------------------------------------------------
        # PRIMERA VEGADA
        # ----------------------------------------------------

        # Si és la primera vegada que utilitzem aquest
        # sistema, NO donarem welcome a tothom.
        #
        # Simplement guardem el moment actual.
        #
        # A partir d'aquí, qualsevol membre que entri
        # mentre el bot estigui apagat serà detectat.

        if last_check_string is None:

            self.welcome_state[
                guild_key
            ] = now.isoformat()

            save_welcome_state(
                self.welcome_state
            )

            print(
                f"👋 Welcome: primera comprovació "
                f"de {guild.name}."
            )

            return


        # ----------------------------------------------------
        # Convertir la data
        # ----------------------------------------------------

        try:

            last_check = datetime.fromisoformat(
                last_check_string
            )

            if last_check.tzinfo is None:

                last_check = last_check.replace(
                    tzinfo=timezone.utc
                )

        except Exception:

            print(
                f"⚠️ Data de welcome incorrecta "
                f"per {guild.name}. "
                f"Reiniciant registre."
            )

            self.welcome_state[
                guild_key
            ] = now.isoformat()

            save_welcome_state(
                self.welcome_state
            )

            return


        # ----------------------------------------------------
        # BUSCAR MEMBRES QUE HAN ENTRAT MENTRE EL BOT
        # ESTAVA APAGAT
        # ----------------------------------------------------

        missed_members = []

        for member in guild.members:

            # Bots no reben welcome

            if member.bot:
                continue

            # Si Discord no té registrada la data
            # d'entrada, no podem comprovar-la.

            if member.joined_at is None:
                continue

            if member.joined_at > last_check:

                missed_members.append(
                    member
                )


        # ----------------------------------------------------
        # ENVIAR WELCOME
        # ----------------------------------------------------

        if missed_members:

            print(
                f"👋 He detectat "
                f"{len(missed_members)} membre(s) "
                f"que van entrar mentre el bot estava apagat."
            )

        for member in missed_members:

            print(
                f"🔎 Welcome perdut detectat: "
                f"{member}"
            )

            success = await self.send_welcome(
                member
            )

            if success:

                print(
                    f"✅ Welcome recuperat per "
                    f"{member}"
                )


        # ----------------------------------------------------
        # ACTUALITZAR ÚLTIMA COMPROVACIÓ
        # ----------------------------------------------------

        self.welcome_state[
            guild_key
        ] = now.isoformat()

        save_welcome_state(
            self.welcome_state
        )


    # ========================================================
    # ON READY
    # ========================================================

    @commands.Cog.listener()
    async def on_ready(
        self
    ):

        # Evitar executar la comprovació diverses vegades
        # si Discord reconnecta el bot.

        if getattr(
            self,
            "_ready_checked",
            False
        ):

            return

        self._ready_checked = True

        print(
            "👋 Welcome: comprovant membres..."
        )

        for guild in self.bot.guilds:

            try:

                await self.check_missed_members(
                    guild
                )

            except Exception as error:

                print(
                    f"❌ Error comprovant membres "
                    f"de {guild.name}: {error}"
                )


    # ========================================================
    # MEMBER JOIN
    # ========================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):

        # ----------------------------------------------------
        # SISTEMA ACTIVAT?
        # ----------------------------------------------------

        if not WELCOME_ENABLED:
            return


        # ----------------------------------------------------
        # IGNORAR BOTS
        # ----------------------------------------------------

        if member.bot:
            return


        # ----------------------------------------------------
        # ENVIAR WELCOME NORMAL
        # ----------------------------------------------------

        success = await self.send_welcome(
            member
        )

        if success:

            # Guardem que aquest membre ja ha rebut
            # el welcome.

            guild_key = str(
                member.guild.id
            )

            now = datetime.now(
                timezone.utc
            )

            self.welcome_state[
                guild_key
            ] = now.isoformat()

            save_welcome_state(
                self.welcome_state
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    # Evitar carregar el sistema de Welcome més d'una vegada

    if bot.get_cog("Welcome") is not None:

        print(
            "⚠️ Welcome ja estava carregat. "
            "No es tornarà a carregar."
        )

        return

    await bot.add_cog(
        Welcome(bot)
    )

    print(
        "👋 Sistema de Welcome carregat una sola vegada."
    )