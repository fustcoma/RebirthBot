import aiohttp
import io
import os

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


    # ========================================================
    # MEMBER JOIN
    # ========================================================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        # ----------------------------------------------------
        # SISTEMA ACTIVAT?
        # ----------------------------------------------------

        if not WELCOME_ENABLED:
            return


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

            return


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

                        return

                    avatar_bytes = await response.read()

        except Exception as error:

            print(
                f"❌ Error descarregant l'avatar: "
                f"{error}"
            )

            return


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

            return


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

        except discord.Forbidden:

            print(
                f"❌ No tinc permisos per enviar "
                f"missatges a {channel.name}"
            )

        except Exception as error:

            print(
                f"❌ Error enviant welcome: {error}"
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