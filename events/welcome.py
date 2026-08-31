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
# CONFIGURACIÓN
# ============================================================

# Activar / desactivar el welcome
WELCOME_ENABLED = True

# Canal del welcome
WELCOME_CHANNEL_ID = 1540758633216872468

# Rol que se asigna automáticamente
WELCOME_ROLE_ID = 1540758763307274289


# ============================================================
# ESTADO DEL WELCOME
# ============================================================

# Guardamos aquí la última vez que el bot comprobó
# los miembros del servidor.

WELCOME_STATE_FILE = (
    Path(__file__).parent.parent
    / "database"
    / "welcome_state.json"
)


# ============================================================
# IMAGEN
# ============================================================

IMAGE_WIDTH = 700
IMAGE_HEIGHT = 260


# ============================================================
# FONDO
# ============================================================

# None = utilizar un color
#
# Ejemplo:
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
# TEXTO PRINCIPAL
# ============================================================

JOIN_TEXT_SIZE = 28

JOIN_TEXT_COLOR = (
    255,
    255,
    255
)

JOIN_TEXT_Y = 140


# ============================================================
# MIEMBRO #N
# ============================================================

MEMBER_TEXT_SIZE = 21

MEMBER_TEXT_COLOR = (
    190,
    190,
    190
)

MEMBER_TEXT_Y = 185


# ============================================================
# FUENTE
# ============================================================

# Ejemplo:
#
# FONT_PATH = "assets/font.ttf"

FONT_PATH = None


# ============================================================
# MENSAJE
# ============================================================

WELCOME_MESSAGE = (
    "¡Hola {member}, bienvenido/a a **{server}**!"
)


# ============================================================
# ESTADO
# ============================================================

def load_welcome_state():

    # Si no existe el archivo, devolvemos un diccionario vacío.

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
            f"❌ Error cargando el estado del welcome: "
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
            f"❌ Error guardando el estado del welcome: "
            f"{error}"
        )


# ============================================================
# FUENTE
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
# CREAR IMAGEN
# ============================================================

def create_welcome_image(
    avatar_bytes,
    username,
    member_number
):

    # --------------------------------------------------------
    # FONDO
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


    # Máscara circular

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


    # Posición centrada

    avatar_x = (
        IMAGE_WIDTH -
        AVATAR_SIZE
    ) // 2

    avatar_y = AVATAR_Y


    # --------------------------------------------------------
    # BORDE DEL AVATAR
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
    # COLOCAR AVATAR
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
    # FUENTES
    # --------------------------------------------------------

    join_font = get_font(
        JOIN_TEXT_SIZE
    )

    member_font = get_font(
        MEMBER_TEXT_SIZE
    )


    # --------------------------------------------------------
    # TEXTO PRINCIPAL
    # --------------------------------------------------------

    join_text = (
        f"{username} se ha unido al servidor"
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
    # MIEMBRO
    # --------------------------------------------------------

    member_text = (
        f"Miembro #{member_number}"
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
    # GUARDAR EN MEMORIA
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

        # Estado persistente
        self.welcome_state = load_welcome_state()


    # ========================================================
    # ENVIAR WELCOME
    # ========================================================

    async def send_welcome(
        self,
        member
    ):

        # ----------------------------------------------------
        # ¿SISTEMA ACTIVADO?
        # ----------------------------------------------------

        if not WELCOME_ENABLED:
            return False


        # ====================================================
        # ASIGNAR ROL
        # ====================================================

        role = member.guild.get_role(
            WELCOME_ROLE_ID
        )

        if role is None:

            print(
                f"❌ No he encontrado el rol "
                f"{WELCOME_ROLE_ID}"
            )

        else:

            try:

                # Solo se lo damos si aún no lo tiene.

                if role not in member.roles:

                    await member.add_roles(
                        role,
                        reason="Rol automático de bienvenida"
                    )

                    print(
                        f"🎭 Rol {role.name} asignado a "
                        f"{member}"
                    )

            except discord.Forbidden:

                print(
                    f"❌ No puedo asignar el rol "
                    f"{role.name} a {member}."
                )

                print(
                    "Comprueba que el rol del bot "
                    "esté por encima del rol."
                )

            except Exception as error:

                print(
                    f"❌ Error asignando el rol: {error}"
                )


        # ====================================================
        # BUSCAR CANAL
        # ====================================================

        channel = member.guild.get_channel(
            WELCOME_CHANNEL_ID
        )

        if channel is None:

            print(
                f"❌ No he encontrado el canal "
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
        # DESCARGAR AVATAR
        # ====================================================

        try:

            async with aiohttp.ClientSession() as session:

                async with session.get(
                    avatar_url
                ) as response:

                    if response.status != 200:

                        print(
                            "❌ No he podido descargar "
                            "el avatar."
                        )

                        return False

                    avatar_bytes = await response.read()

        except Exception as error:

            print(
                f"❌ Error descargando el avatar: "
                f"{error}"
            )

            return False


        # ====================================================
        # CREAR IMAGEN
        # ====================================================

        try:

            welcome_image = create_welcome_image(
                avatar_bytes,
                member.display_name,
                member.guild.member_count
            )

        except Exception as error:

            print(
                f"❌ Error creando la tarjeta de welcome: "
                f"{error}"
            )

            return False


        # ====================================================
        # MENSAJE
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
                f"👋 Welcome enviado para {member}"
            )

            return True

        except discord.Forbidden:

            print(
                f"❌ No tengo permisos para enviar "
                f"mensajes en {channel.name}"
            )

        except Exception as error:

            print(
                f"❌ Error enviando welcome: {error}"
            )

        return False


    # ========================================================
    # COMPROBAR MIEMBROS PERDIDOS
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
        # Buscar última comprobación
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
        # PRIMERA VEZ
        # ----------------------------------------------------

        # Si es la primera vez que utilizamos este
        # sistema, NO daremos welcome a todos.
        #
        # Simplemente guardamos el momento actual.
        #
        # A partir de aquí, cualquier miembro que entre
        # mientras el bot esté apagado será detectado.

        if last_check_string is None:

            self.welcome_state[
                guild_key
            ] = now.isoformat()

            save_welcome_state(
                self.welcome_state
            )

            print(
                f"👋 Welcome: primera comprobación "
                f"de {guild.name}."
            )

            return


        # ----------------------------------------------------
        # Convertir la fecha
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
                f"⚠️ Fecha de welcome incorrecta "
                f"para {guild.name}. "
                f"Reiniciando registro."
            )

            self.welcome_state[
                guild_key
            ] = now.isoformat()

            save_welcome_state(
                self.welcome_state
            )

            return


        # ----------------------------------------------------
        # BUSCAR MIEMBROS QUE HAN ENTRADO MIENTRAS EL BOT
        # ESTABA APAGADO
        # ----------------------------------------------------

        missed_members = []

        for member in guild.members:

            # Los bots no reciben welcome

            if member.bot:
                continue

            # Si Discord no tiene registrada la fecha
            # de entrada, no podemos comprobarla.

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
                f"👋 He detectado "
                f"{len(missed_members)} miembro(s) "
                f"que entraron mientras el bot estaba apagado."
            )

        for member in missed_members:

            print(
                f"🔎 Welcome perdido detectado: "
                f"{member}"
            )

            success = await self.send_welcome(
                member
            )

            if success:

                print(
                    f"✅ Welcome recuperado para "
                    f"{member}"
                )


        # ----------------------------------------------------
        # ACTUALIZAR ÚLTIMA COMPROBACIÓN
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

        # Evitar ejecutar la comprobación varias veces
        # si Discord reconecta el bot.

        if getattr(
            self,
            "_ready_checked",
            False
        ):

            return

        self._ready_checked = True

        print(
            "👋 Welcome: comprobando miembros..."
        )

        for guild in self.bot.guilds:

            try:

                await self.check_missed_members(
                    guild
                )

            except Exception as error:

                print(
                    f"❌ Error comprobando miembros "
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
        # ¿SISTEMA ACTIVADO?
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

            # Guardamos que este miembro ya ha recibido
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

    # Evitar cargar el sistema de Welcome más de una vez

    if bot.get_cog("Welcome") is not None:

        print(
            "⚠️ Welcome ya estaba cargado. "
            "No se volverá a cargar."
        )

        return

    await bot.add_cog(
        Welcome(bot)
    )

    print(
        "👋 Sistema de Welcome cargado una sola vez."
    )