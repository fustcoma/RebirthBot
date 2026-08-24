
import re
import time
from collections import defaultdict, deque
from datetime import timedelta

import discord
from discord.ext import commands

from database.database import connect
from events.logs import send_log


# ============================================================
# CONFIGURACIÓ
# ============================================================


# ============================================================
# PARAULES PROHIBIDES
# ============================================================

BANNED_WORDS = {
    "nigga",
    "niggers",
    "nigger",
}


DELETE_BANNED_MESSAGES = True
WARN_BANNED_WORDS = True


# ============================================================
# ANTI-LINKS
# ============================================================

ANTI_LINKS_ENABLED = True
DELETE_LINK_MESSAGES = True
WARN_LINKS = True


# Dominis permesos

ALLOWED_LINK_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "twitch.tv",
}


# ============================================================
# ANTI-SPAM
# ============================================================

ANTI_SPAM_ENABLED = True

# Quants missatges iguals detectem
SPAM_MESSAGE_COUNT = 3

# En quants segons
SPAM_TIME_WINDOW = 6


# ============================================================
# ANTI-FLOOD
# ============================================================

ANTI_FLOOD_ENABLED = True

# Nombre màxim de missatges
FLOOD_MESSAGE_COUNT = 6

# En aquesta quantitat de segons
FLOOD_TIME_WINDOW = 5


# ============================================================
# COOLDOWN D'INCIDENT
# ============================================================

# Temps durant el qual no crearem un altre incident
# per al mateix usuari.
INCIDENT_COOLDOWN = 8


# ============================================================
# WARN AUTOMÀTIC
# ============================================================

WARN_TIMEOUT_AT = 5
WARN_TIMEOUT_MINUTES = 10

WARN_KICK_AT = 6


# ============================================================
# MISSATGE PÚBLIC
# ============================================================

SEND_PUBLIC_WARN_MESSAGE = True

PUBLIC_WARN_DELETE_AFTER = 8


# ============================================================
# LOGS
# ============================================================

AUTOMOD_LOGS_ENABLED = True


# ============================================================
# COG
# ============================================================

class AutoMod(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        # ----------------------------------------------------
        # Historial de missatges per usuari
        # ----------------------------------------------------

        self.user_messages = defaultdict(
            lambda: deque(maxlen=30)
        )

        # ----------------------------------------------------
        # Últim incident de cada usuari
        # ----------------------------------------------------

        self.last_incident = {}

        # ----------------------------------------------------
        # Evita processar simultàniament el mateix usuari
        # ----------------------------------------------------

        self.processing_users = set()

        print(
            "🛡️ AutoMod carregat correctament."
        )


    # ========================================================
    # JERARQUIA
    # ========================================================

    def can_moderate(
        self,
        message: discord.Message
    ):

        if message.guild is None:
            return False

        member = message.author
        bot_member = message.guild.me

        if bot_member is None:
            return False

        # Propietari
        if member.id == message.guild.owner_id:
            return False

        # Mateix bot
        if member.id == bot_member.id:
            return False

        # Jerarquia
        if member.top_role >= bot_member.top_role:
            return False

        return True


    # ========================================================
    # PARAULES PROHIBIDES
    # ========================================================

    def find_banned_word(
        self,
        content: str
    ):

        content_lower = content.lower()

        for word in BANNED_WORDS:

            word = word.lower().strip()

            if not word:
                continue

            # Paraules molt curtes
            if len(word) <= 3:

                if word in content_lower:
                    return word

                continue

            pattern = rf"\b{re.escape(word)}\b"

            if re.search(
                pattern,
                content_lower
            ):
                return word

        return None


    # ========================================================
    # DETECTAR LINKS
    # ========================================================

    def find_link(
        self,
        content: str
    ):

        normalized = content.lower()

        # Intentos senzills d'amagar dominis

        normalized = normalized.replace(
            "[.]",
            "."
        )

        normalized = normalized.replace(
            "(.)",
            "."
        )

        normalized = normalized.replace(
            " dot ",
            "."
        )

        # URL

        pattern = (
            r"(https?://[^\s]+"
            r"|www\.[^\s]+"
            r"|discord\.gg/[^\s]+"
            r"|discord\.com/invite/[^\s]+"
            r"|discordapp\.com/invite/[^\s]+)"
        )

        match = re.search(
            pattern,
            normalized
        )

        if not match:
            return None

        url = match.group(0)

        url = url.rstrip(
            ".,!?;:)]}>\"'"
        )

        domain = self.extract_domain(
            url
        )

        if domain is None:
            return url

        # Whitelist

        for allowed_domain in ALLOWED_LINK_DOMAINS:

            allowed_domain = (
                allowed_domain
                .lower()
                .strip()
            )

            if (
                domain == allowed_domain
                or domain.endswith(
                    "." + allowed_domain
                )
            ):
                return None

        return url


    # ========================================================
    # EXTREURE DOMINI
    # ========================================================

    def extract_domain(
        self,
        url: str
    ):

        url = url.lower()

        if url.startswith(
            "discord.gg/"
        ):
            return "discord.gg"

        if url.startswith(
            "discord.com/invite/"
        ):
            return "discord.com"

        if url.startswith(
            "discordapp.com/invite/"
        ):
            return "discordapp.com"

        url = re.sub(
            r"^https?://",
            "",
            url
        )

        url = re.sub(
            r"^www\.",
            "",
            url
        )

        domain = url.split(
            "/"
        )[0]

        domain = domain.split(
            ":"
        )[0]

        return domain


    # ========================================================
    # AFEGIR MISSATGE A L'HISTORIAL
    # ========================================================

    def register_message(
        self,
        message: discord.Message
    ):

        now = time.monotonic()

        key = (
            message.guild.id,
            message.author.id
        )

        self.user_messages[key].append(
            (
                now,
                message.id,
                message.channel.id,
                message.content
            )
        )

        # Netejar missatges antics

        history = self.user_messages[key]

        while history:

            if now - history[0][0] <= max(
                SPAM_TIME_WINDOW,
                FLOOD_TIME_WINDOW
            ):
                break

            history.popleft()


    # ========================================================
    # DETECTAR SPAM
    # ========================================================

    def detect_spam(
        self,
        message: discord.Message
    ):

        key = (
            message.guild.id,
            message.author.id
        )

        history = self.user_messages[key]

        content = message.content.strip().lower()

        if not content:
            return False, []


        now = time.monotonic()

        recent = [
            item
            for item in history
            if now - item[0] <= SPAM_TIME_WINDOW
        ]


        same_messages = [
            item
            for item in recent
            if item[3].strip().lower() == content
        ]


        if len(same_messages) >= SPAM_MESSAGE_COUNT:

            ids = [
                item[1]
                for item in same_messages
            ]

            if message.id not in ids:
                ids.append(
                    message.id
                )

            return True, ids

        return False, []


    # ========================================================
    # DETECTAR FLOOD
    # ========================================================

    def detect_flood(
        self,
        message: discord.Message
    ):

        key = (
            message.guild.id,
            message.author.id
        )

        history = self.user_messages[key]

        now = time.monotonic()

        recent = [
            item
            for item in history
            if now - item[0] <= FLOOD_TIME_WINDOW
        ]

        if len(recent) >= FLOOD_MESSAGE_COUNT:

            ids = [
                item[1]
                for item in recent
            ]

            if message.id not in ids:
                ids.append(
                    message.id
                )

            return True, ids

        return False, []


    # ========================================================
    # COOLDOWN D'INCIDENT
    # ========================================================

    def incident_on_cooldown(
        self,
        guild_id,
        user_id
    ):

        key = (
            guild_id,
            user_id
        )

        now = time.monotonic()

        last = self.last_incident.get(
            key,
            0
        )

        if now - last < INCIDENT_COOLDOWN:
            return True

        self.last_incident[key] = now

        return False


    # ========================================================
    # AFEGIR WARN
    # ========================================================

    async def add_warning(
        self,
        guild: discord.Guild,
        member: discord.Member,
        reason: str
    ):

        connection = connect()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO warnings
                (
                    guild_id,
                    user_id,
                    moderator_id,
                    reason
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    guild.id,
                    member.id,
                    self.bot.user.id,
                    reason
                )
            )

            connection.commit()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM warnings
                WHERE guild_id = ?
                AND user_id = ?
                """,
                (
                    guild.id,
                    member.id
                )
            )

            warning_count = (
                cursor.fetchone()[0]
            )

        finally:

            connection.close()

        return warning_count


    # ========================================================
    # ACCIONS AUTOMÀTIQUES
    # ========================================================

    async def automatic_action(
        self,
        member: discord.Member,
        warning_count: int,
        reason: str
    ):

        timeout_done = False
        kick_done = False


        # ----------------------------------------------------
        # TIMEOUT
        # ----------------------------------------------------

        if warning_count == WARN_TIMEOUT_AT:

            try:

                await member.timeout(
                    timedelta(
                        minutes=WARN_TIMEOUT_MINUTES
                    ),
                    reason=(
                        f"AutoMod: {reason} "
                        f"({warning_count} warns)"
                    )
                )

                timeout_done = True

                print(
                    f"⏱️ AutoMod: {member} "
                    f"ha rebut timeout."
                )

            except discord.Forbidden:

                print(
                    f"❌ No puc fer timeout "
                    f"a {member}."
                )

            except Exception as error:

                print(
                    f"❌ Error fent timeout: "
                    f"{error}"
                )


        # ----------------------------------------------------
        # KICK
        # ----------------------------------------------------

        if warning_count == WARN_KICK_AT:

            try:

                await member.kick(
                    reason=(
                        f"AutoMod: {reason} "
                        f"({warning_count} warns)"
                    )
                )

                kick_done = True

                print(
                    f"👢 AutoMod: {member} "
                    f"ha estat expulsat."
                )

            except discord.Forbidden:

                print(
                    f"❌ No puc expulsar "
                    f"{member}."
                )

            except Exception as error:

                print(
                    f"❌ Error expulsant: "
                    f"{error}"
                )


        return (
            timeout_done,
            kick_done
        )


    # ========================================================
    # ESBORRAR MISSATGES DE L'INCIDENT
    # ========================================================

    async def delete_messages(
        self,
        channel: discord.TextChannel,
        message_ids
    ):

        if not message_ids:
            return 0

        deleted = 0

        try:

            # Intentem obtenir els missatges
            # abans de fer la purga.

            messages = []

            for message_id in set(message_ids):

                try:

                    message = await channel.fetch_message(
                        message_id
                    )

                    messages.append(
                        message
                    )

                except (
                    discord.NotFound,
                    discord.Forbidden
                ):
                    continue

            if not messages:
                return 0

            # purge() agrupa les eliminacions
            # i redueix molt les peticions.

            deleted_messages = await channel.purge(
                limit=len(messages),
                check=lambda m: m.id in {
                    msg.id
                    for msg in messages
                },
                bulk=True
            )

            deleted = len(
                deleted_messages
            )

        except discord.NotFound:

            pass

        except discord.Forbidden:

            print(
                "❌ AutoMod no té permisos "
                "per eliminar missatges."
            )

        except discord.HTTPException as error:

            print(
                f"❌ Error eliminant missatges: "
                f"{error}"
            )

        return deleted


    # ========================================================
    # MISSATGE PÚBLIC DE WARN
    # ========================================================

    async def send_public_warning(
        self,
        message: discord.Message,
        reason: str,
        warning_count: int
    ):

        if not SEND_PUBLIC_WARN_MESSAGE:
            return

        if reason == "spam":

            text = (
                f"⚠️ {message.author.mention}, "
                f"has rebut un **warn** per spam."
            )

        elif reason == "flood":

            text = (
                f"⚠️ {message.author.mention}, "
                f"has rebut un **warn** per flood."
            )

        elif reason == "link":

            text = (
                f"⚠️ {message.author.mention}, "
                f"has rebut un **warn** per enviar "
                f"un link no permès."
            )

        elif reason == "banned_word":

            text = (
                f"⚠️ {message.author.mention}, "
                f"has rebut un **warn** per utilitzar "
                f"una paraula prohibida."
            )

        else:

            text = (
                f"⚠️ {message.author.mention}, "
                f"has rebut un **warn**."
            )

        if warning_count >= WARN_TIMEOUT_AT:

            if warning_count == WARN_TIMEOUT_AT:

                text += (
                    f"\n⏱️ Has arribat als "
                    f"**{WARN_TIMEOUT_AT} warns** "
                    f"i has rebut un timeout de "
                    f"**{WARN_TIMEOUT_MINUTES} minuts**."
                )

        try:

            warning_message = await message.channel.send(
                text
            )

            if PUBLIC_WARN_DELETE_AFTER > 0:

                await warning_message.delete(
                    delay=PUBLIC_WARN_DELETE_AFTER
                )

        except discord.HTTPException as error:

            print(
                f"❌ Error enviant warn públic: "
                f"{error}"
            )


    # ========================================================
    # LOG AUTOMOD
    # ========================================================

    async def automod_log(
        self,
        title,
        description,
        color,
        fields=None
    ):

        if not AUTOMOD_LOGS_ENABLED:
            return

        try:

            await send_log(
                self.bot,
                title,
                description,
                color,
                fields
            )

        except Exception as error:

            print(
                f"❌ Error enviant log: "
                f"{error}"
            )


    # ========================================================
    # PROCESSAR INCIDENT
    # ========================================================

    async def process_incident(
        self,
        message: discord.Message,
        reason: str,
        message_ids=None
    ):

        guild = message.guild
        member = message.author

        if guild is None:
            return

        key = (
            guild.id,
            member.id
        )

        # Evitar dues tasques simultànies

        if key in self.processing_users:
            return

        # Un únic incident

        if self.incident_on_cooldown(
            guild.id,
            member.id
        ):
            print(
                f"ℹ️ AutoMod: incident duplicat "
                f"ignorat per {member}."
            )
            return

        self.processing_users.add(
            key
        )

        try:

            # ------------------------------------------------
            # ELIMINAR MISSATGES
            # ------------------------------------------------

            if message_ids:

                deleted = await self.delete_messages(
                    message.channel,
                    message_ids
                )

                print(
                    f"🗑️ AutoMod ha eliminat "
                    f"{deleted} missatges."
                )


            # ------------------------------------------------
            # WARN
            # ------------------------------------------------

            if reason == "spam":

                warn_reason = (
                    "AutoMod: spam"
                )

            elif reason == "flood":

                warn_reason = (
                    "AutoMod: flood"
                )

            elif reason == "link":

                warn_reason = (
                    "AutoMod: link no permès"
                )

            elif reason == "banned_word":

                warn_reason = (
                    "AutoMod: paraula prohibida"
                )

            else:

                warn_reason = (
                    "AutoMod: infracció"
                )


            warning_count = await self.add_warning(
                guild,
                member,
                warn_reason
            )


            print(
                f"⚠️ AutoMod warn: "
                f"{member} -> "
                f"{warning_count}"
            )


            # ------------------------------------------------
            # ACCIONS AUTOMÀTIQUES
            # ------------------------------------------------

            (
                timeout_done,
                kick_done
            ) = await self.automatic_action(
                member,
                warning_count,
                warn_reason
            )


            # ------------------------------------------------
            # MISSATGE PÚBLIC
            # ------------------------------------------------

            await self.send_public_warning(
                message,
                reason,
                warning_count
            )


            # ------------------------------------------------
            # LOG
            # ------------------------------------------------

            reason_names = {

                "spam":
                    "Spam",

                "flood":
                    "Flood",

                "link":
                    "Link no permès",

                "banned_word":
                    "Paraula prohibida"
            }

            reason_name = reason_names.get(
                reason,
                "Infracció"
            )


            log_fields = [

                (
                    "👤 Usuari",
                    f"{member} (`{member.id}`)",
                    False
                ),

                (
                    "💬 Canal",
                    message.channel.mention,
                    True
                ),

                (
                    "🚨 Motiu",
                    reason_name,
                    True
                ),

                (
                    "📊 Warns",
                    str(warning_count),
                    True
                )
            ]


            if message_ids:

                log_fields.append(
                    (
                        "🗑️ Missatges eliminats",
                        str(len(message_ids)),
                        True
                    )
                )


            if timeout_done:

                log_fields.append(
                    (
                        "⏱️ Timeout",
                        f"{WARN_TIMEOUT_MINUTES} minuts",
                        False
                    )
                )


            if kick_done:

                log_fields.append(
                    (
                        "👢 Kick",
                        "Sí",
                        False
                    )
                )


            await self.automod_log(
                f"🛡️ AutoMod — {reason_name}",
                (
                    f"{member.mention} "
                    f"ha infringit les normes."
                ),
                discord.Color.red(),
                log_fields
            )

        finally:

            self.processing_users.discard(
                key
            )


    # ========================================================
    # ON MESSAGE
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

        # ----------------------------------------------------
        # IGNORAR DMs
        # ----------------------------------------------------

        if message.guild is None:
            return


        # ----------------------------------------------------
        # IGNORAR BOTS
        # ----------------------------------------------------

        if message.author.bot:
            return


        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print(
            f"🛡️ AutoMod: "
            f"{message.author} -> "
            f"{message.content}"
        )


        # ----------------------------------------------------
        # JERARQUIA
        # ----------------------------------------------------

        if not self.can_moderate(
            message
        ):
            return


        # ----------------------------------------------------
        # REGISTRAR MISSATGE
        # ----------------------------------------------------

        self.register_message(
            message
        )


        # ====================================================
        # PARAULES PROHIBIDES
        # ====================================================

        banned_word = self.find_banned_word(
            message.content
        )

        if banned_word is not None:

            print(
                f"🚨 Paraula prohibida: "
                f"{banned_word}"
            )

            if DELETE_BANNED_MESSAGES:

                try:

                    await message.delete()

                    print(
                        "🗑️ Missatge eliminat."
                    )

                except discord.NotFound:

                    pass

                except discord.Forbidden:

                    print(
                        "❌ No puc eliminar "
                        "el missatge."
                    )

            if WARN_BANNED_WORDS:

                await self.process_incident(
                    message,
                    "banned_word"
                )

            return


        # ====================================================
        # ANTI-LINKS
        # ====================================================

        if ANTI_LINKS_ENABLED:

            link = self.find_link(
                message.content
            )

            if link is not None:

                print(
                    f"🔗 Link detectat: "
                    f"{link}"
                )

                message_ids = [
                    message.id
                ]

                if DELETE_LINK_MESSAGES:

                    try:

                        await message.delete()

                        print(
                            "🗑️ Link eliminat."
                        )

                    except discord.NotFound:

                        pass

                    except discord.Forbidden:

                        print(
                            "❌ No puc eliminar "
                            "el link."
                        )


                if WARN_LINKS:

                    await self.process_incident(
                        message,
                        "link",
                        message_ids
                    )

                return


        # ====================================================
        # ANTI-SPAM
        # ====================================================

        if ANTI_SPAM_ENABLED:

            spam_detected, spam_ids = (
                self.detect_spam(
                    message
                )
            )

            if spam_detected:

                print(
                    f"🚨 Spam detectat: "
                    f"{message.author}"
                )

                await self.process_incident(
                    message,
                    "spam",
                    spam_ids
                )

                return


        # ====================================================
        # ANTI-FLOOD
        # ====================================================

        if ANTI_FLOOD_ENABLED:

            flood_detected, flood_ids = (
                self.detect_flood(
                    message
                )
            )

            if flood_detected:

                print(
                    f"🚨 Flood detectat: "
                    f"{message.author}"
                )

                await self.process_incident(
                    message,
                    "flood",
                    flood_ids
                )

                return


    # ========================================================
    # ON MESSAGE EDIT
    # ========================================================

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message
    ):

        # ----------------------------------------------------
        # DMs
        # ----------------------------------------------------

        if after.guild is None:
            return


        # ----------------------------------------------------
        # Bots
        # ----------------------------------------------------

        if after.author.bot:
            return


        # ----------------------------------------------------
        # Només si el contingut ha canviat
        # ----------------------------------------------------

        if before.content == after.content:
            return


        # ----------------------------------------------------
        # Jerarquia
        # ----------------------------------------------------

        if not self.can_moderate(
            after
        ):
            return


        print(
            f"✏️ AutoMod: "
            f"{after.author} ha editat "
            f"un missatge."
        )


        # ====================================================
        # PARAULA PROHIBIDA
        # ====================================================

        banned_word = self.find_banned_word(
            after.content
        )

        if banned_word is not None:

            print(
                f"🚨 Paraula prohibida "
                f"detectada en edició: "
                f"{banned_word}"
            )

            try:

                await after.delete()

                print(
                    "🗑️ Missatge editat eliminat."
                )

            except discord.NotFound:

                pass

            except discord.Forbidden:

                print(
                    "❌ No puc eliminar "
                    "el missatge editat."
                )

            await self.process_incident(
                after,
                "banned_word"
            )

            return


        # ====================================================
        # LINK
        # ====================================================

        if ANTI_LINKS_ENABLED:

            link = self.find_link(
                after.content
            )

            if link is not None:

                print(
                    f"🔗 Link detectat "
                    f"en edició: {link}"
                )

                try:

                    await after.delete()

                    print(
                        "🗑️ Link editat eliminat."
                    )

                except discord.NotFound:

                    pass

                except discord.Forbidden:

                    print(
                        "❌ No puc eliminar "
                        "el link editat."
                    )

                await self.process_incident(
                    after,
                    "link",
                    [after.id]
                )

                return


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        AutoMod(bot)
    )

