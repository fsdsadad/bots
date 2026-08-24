import asyncio
import random
import time
import os
import re
from typing import Set, List, Optional, Dict

from telethon import TelegramClient, events
from telethon.tl.types import Message, User
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPhoto
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from typing import List

# API Credentials (REQUIRED even for bot tokens)
API_ID = 22152659
API_HASH = "7300603715676773c05db7fd7aab55fc"

# Bot Tokens
BOT_TOKENS = [
    "8774218095:AAHE5UNCY9hSnJe1Pxv0EkWeJk0twpXCAq8",
    "8508888819:AAEoa7BOhcNNwenILid8IHVN0kCYqNtSSEs", 
    "8347453245:AAFfpyrov2l8ySZJAs3F0YlFHjr9wM_6fiI",
    "8522432970:AAFy6MfoCYUnDUHFFk5z9pS55IrJEyFNQsE",
    "7463506644:AAF5LzaFKjqHPS1wC1GVIgO9pgsSrX4e8T0",
]

MASTER_BOT_INDEX = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = BASE_DIR
FOSH_FILE = os.path.join(BASE_DIR, "fosh.txt")
TARGET_ID_FILE = os.path.join(BOT_DIR, "targetid.txt")
FWD_SOURCE_CHANNEL_FILE = os.path.join(BOT_DIR, "fwd_source_channel.txt")
FWD_SOURCE_MSG_ID_FILE = os.path.join(BOT_DIR, "fwd_source_msg_id.txt")
FWD_DELAY_MIN_FILE = os.path.join(BOT_DIR, "fwd_delay_min.txt")
FWD_DELAY_MAX_FILE = os.path.join(BOT_DIR, "fwd_delay_max.txt")
FWD_EXTRA_TEXT_FILE = os.path.join(BOT_DIR, "fwd_extra_text.txt")
FWD_EXTRA_POSITION_FILE = os.path.join(BOT_DIR, "fwd_extra_position.txt")
HELP_IMAGE_URL = "https://raw.githubusercontent.com/sadraonthehack/VDIEO/main/8d4db30dac973ecc09668b36ba19f11e.gif"

ADMIN_IDS: Set[int] = {7202211827}  
FOSHLIST: List[str] = []
SPAM_TARGET: Optional[int] = None
SPAM_TEXT: str = "ONLINE"
SPAM_SPEED: float = 1.0  
ON_OFF_ACTIVE: bool = False
ON_OFF_TASK: Optional[asyncio.Task] = None
ON_OFF_SEQUENCE: List[str] = ["چس", "مس", "کص","لش", "مست", "1", "2", "3", "4", "5", "6", "7", "8", "9", "00", "مدرک"]
ON_OFF_DELAY: float = 0
ENEMY_TARGET: Optional[int] = None
ENEMY_ACTIVE: bool = False
REPLY_TO_ENEMY: bool = True
ORIGINAL_NAME: str = ""
ORIGINAL_PHOTO: Optional[InputPhoto] = None

# Tag spam variables
TAG_TARGETS: List[int] = []
TAG_SPAM_ACTIVE: bool = False
TAG_SPAM_TASK: Optional[asyncio.Task] = None
TAG_SPAM_DELAY: float = 5.0
TAG_SPAM_CHAT_ID: Optional[int] = None
TAG_SYMBOL: str = "->"

# Multi-bot variables
clients: List[TelegramClient] = []
MASTER_CLIENT: Optional[TelegramClient] = None
ALL_BOTS_RUNNING: bool = False
FORWARD_SPAM_ACTIVE = False
FORWARD_SPAM_TASK = None

# Per-bot spam states
bot_spam_states: Dict[int, Dict] = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def spam_loop_all_bots(target, text, speed):
    """Send spam with ALL bots."""
    global SPAM_ACTIVE
    while SPAM_ACTIVE and target:
        for i, client in enumerate(clients):
            if not SPAM_ACTIVE:
                break
            try:
                await client.send_message(target, text)
                print(f"[SPAM] Bot {i} Sent to {target}")
            except FloodWaitError as e:
                print(f"[SPAM] Bot {i} Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"[SPAM] Bot {i} Error: {e}")
        await asyncio.sleep(speed)


async def on_off_loop_all_bots(chat_id):
    """Send on/off sequence with ALL bots."""
    global ON_OFF_ACTIVE, ON_OFF_SEQUENCE, ON_OFF_DELAY
    while ON_OFF_ACTIVE:
        for item in ON_OFF_SEQUENCE:
            if not ON_OFF_ACTIVE:
                break
            for i, client in enumerate(clients):
                if not ON_OFF_ACTIVE:
                    break
                try:
                    await client.send_message(chat_id, item)
                    print(f"[ON/OFF] Bot {i} Sent: {item}")
                except FloodWaitError as e:
                    print(f"[ON/OFF] Bot {i} Flood wait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"[ON/OFF] Bot {i} Error: {e}")
            await asyncio.sleep(ON_OFF_DELAY)
        await asyncio.sleep(0)


async def tag_spam_all_bots_loop(chat_id: int):
    """Send fosh messages with all tag mentions using ALL bots."""
    global TAG_SPAM_ACTIVE, TAG_TARGETS, TAG_SPAM_DELAY, FOSHLIST, TAG_SYMBOL, clients
    while TAG_SPAM_ACTIVE and clients and chat_id:
        if not FOSHLIST:
            print("[TAG SPAM] No fosh messages available.")
            await asyncio.sleep(5)
            continue
        if not TAG_TARGETS:
            print("[TAG SPAM] No targets set.")
            await asyncio.sleep(5)
            continue

        fosh_text = random.choice(FOSHLIST)

        mentions = "\n".join(
            f"<a href='tg://user?id={uid}'>{TAG_SYMBOL}</a>"
            for uid in TAG_TARGETS
        )

        full_message = f"{fosh_text}\n\n{mentions}"

        for i, client in enumerate(clients):
            if not TAG_SPAM_ACTIVE:
                break
            try:
                await client.send_message(chat_id, full_message, parse_mode='html')
                print(f"[TAG SPAM] Bot {i} sent with {len(TAG_TARGETS)} tag(s)")
            except FloodWaitError as e:
                print(f"[TAG SPAM] Bot {i} Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"[TAG SPAM] Bot {i} Error: {e}")

        await asyncio.sleep(TAG_SPAM_DELAY)


async def forward_spam_all_bots():
    """Forward spam with ALL bots."""
    global FORWARD_SPAM_ACTIVE
    print("[FWD SPAM] Started ")
    ensure_forward_files()
    while FORWARD_SPAM_ACTIVE:
        try:
            target_id = SPAM_TARGET
            if not target_id:
                target_id = int(read_forward_file(TARGET_ID_FILE, "1") or "1")

            source_channel = read_forward_file(FWD_SOURCE_CHANNEL_FILE)
            source_msg_id = int(read_forward_file(FWD_SOURCE_MSG_ID_FILE, "0"))
            delay_min = float(read_forward_file(FWD_DELAY_MIN_FILE, "3"))
            delay_max = float(read_forward_file(FWD_DELAY_MAX_FILE, "10"))
            extra_text = read_forward_file(FWD_EXTRA_TEXT_FILE)
            extra_pos = read_forward_file(FWD_EXTRA_POSITION_FILE, "after").lower()
        except Exception as e:
            print(f"[FWD SPAM] Config read error: {e}")
            await asyncio.sleep(5)
            continue

        if not target_id or target_id == 1:
            print("[FWD SPAM] No target set. Use setid <chatid> first.")
            FORWARD_SPAM_ACTIVE = False
            break

        if not source_channel or source_msg_id == 0:
            print("[FWD SPAM] No source set. Use setfwd <message_link>")
            FORWARD_SPAM_ACTIVE = False
            break

        try:
            source_message = await MASTER_CLIENT.get_messages(source_channel, ids=source_msg_id)
            if not source_message:
                print(f"[FWD SPAM] Message {source_msg_id} not found in {source_channel}")
                FORWARD_SPAM_ACTIVE = False
                break

            for i, client in enumerate(clients):
                if not FORWARD_SPAM_ACTIVE:
                    break
                try:
                    await client.forward_messages(target_id, source_message)
                    print(f"[FWD SPAM] Bot {i} forwarded to {target_id}")
                except FloodWaitError as e:
                    print(f"[FWD SPAM] Bot {i} Flood wait: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"[FWD SPAM] Bot {i} Error: {e}")

            if extra_text:
                if extra_pos == "before":
                    for i, client in enumerate(clients):
                        if not FORWARD_SPAM_ACTIVE:
                            break
                        try:
                            await client.send_message(target_id, f"{extra_text}\n\n")
                        except Exception as e:
                            print(f"[FWD SPAM] Bot {i} extra text error: {e}")
                else:
                    for i, client in enumerate(clients):
                        if not FORWARD_SPAM_ACTIVE:
                            break
                        try:
                            await client.send_message(target_id, f"\n\n{extra_text}")
                        except Exception as e:
                            print(f"[FWD SPAM] Bot {i} extra text error: {e}")

            delay = random.uniform(delay_min, delay_max)
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            print(f"[FWD SPAM] Flood wait: {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"[FWD SPAM] Error: {e}")
            await asyncio.sleep(5)


async def send_loading_animation(event):
    """Send a loading animation with progress bar effect."""
    loading_steps = [
        " [          ] 0%",
        " [█         ] 10%",
        " [██        ] 20%",
        " [███       ] 30%",
        " [████      ] 40%",
        " [█████     ] 50%",
        " [██████    ] 60%",
        " [███████   ] 70%",
        " [████████  ] 80%",
        " [█████████ ] 90%",
        " [██████████] 100%",
        " LOADING COMPLETE"
    ]
    loading_msg = await event.reply(" Loading...\n" + loading_steps[0])
    for i in range(1, len(loading_steps)):
        await asyncio.sleep(0.3)
        try:
            await loading_msg.edit(f" Loading...\n{loading_steps[i]}")
        except:
            break
    await asyncio.sleep(0.3)
    try:
        await loading_msg.delete()
    except:
        pass


def save_fosh_file():
    try:
        with open(FOSH_FILE, "w", encoding="utf-8") as f:
            for item in FOSHLIST:
                f.write(item.strip() + "\n")
    except Exception as e:
        print(f"[ERROR] Could not save {FOSH_FILE}: {e}")


def normalize_join_target(raw: str) -> Optional[str]:
    if not raw:
        return None

    target = raw.strip()
    if not target:
        return None

    if target.startswith("@"):
        return target[1:]

    target = target.replace("https://", "").replace("http://", "")
    target = target.replace("t.me/", "", 1).replace("telegram.me/", "", 1)
    target = target.split("?", 1)[0].split("#", 1)[0].strip("/")

    if not target:
        return None

    if target.lower().startswith("joinchat/"):
        return target[len("joinchat/"):]

    if target.startswith("+"):
        return target

    if target.lower().startswith("joinchat"):
        return target[len("joinchat"):]

    if "/" in target:
        first_part = target.split("/", 1)[0]
        if first_part.lower() in {"joinchat", "addlist", "s"}:
            return target.split("/", 1)[1]
        return first_part

    return target


def looks_like_invite_hash(target: str) -> bool:
    if not target:
        return False
    return target.lower().startswith("joinchat") or target.startswith("+")


def ensure_forward_files():
    os.makedirs(BOT_DIR, exist_ok=True)
    files_defaults = {
        TARGET_ID_FILE: "1",
        FWD_SOURCE_CHANNEL_FILE: "",
        FWD_SOURCE_MSG_ID_FILE: "0",
        FWD_DELAY_MIN_FILE: "3",
        FWD_DELAY_MAX_FILE: "10",
        FWD_EXTRA_TEXT_FILE: "",
        FWD_EXTRA_POSITION_FILE: "after",
    }
    for path, value in files_defaults.items():
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(value)
            except Exception as e:
                print(f"[ERROR] Could not create {path}: {e}")


def read_forward_file(path: str, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip() or default
    except Exception:
        return default


async def handle_all_messages(event):
    global ADMIN_IDS, FOSHLIST, SPAM_TARGET, SPAM_TEXT, SPAM_ACTIVE, SPAM_SPEED
    global ON_OFF_ACTIVE, ON_OFF_TASK, ENEMY_TARGET, ENEMY_ACTIVE, REPLY_TO_ENEMY, ORIGINAL_NAME, ORIGINAL_PHOTO, FORWARD_SPAM_ACTIVE, FORWARD_SPAM_TASK
    global TAG_TARGETS, TAG_SPAM_ACTIVE, TAG_SPAM_TASK, TAG_SPAM_DELAY, TAG_SPAM_CHAT_ID, TAG_SYMBOL
    global MASTER_CLIENT
    
    user_id = event.sender_id
    client_instance = event.client
    
    if ENEMY_ACTIVE and REPLY_TO_ENEMY and FOSHLIST:
        if user_id == ENEMY_TARGET:
            reply_text = random.choice(FOSHLIST)
            await asyncio.sleep(0.5)
            try:
                await event.reply(reply_text)
                print(f"[BOT] Enemy reply sent to {user_id}")
            except Exception as e:
                print(f"[ERROR] Enemy reply failed: {e}")
            return
    
    if not event.message or not event.message.text:
        return
    
    raw_text = event.message.text.strip() if event.message.text else ""
    text = raw_text.lower()

    if event.is_reply and raw_text:
        if user_id in ADMIN_IDS:
            if not text.startswith((
                "help", "راهنما", "help2", "on", "off", "spam", "spamoff", "setfosh ",
                "speed ", "id", "setid ", "setfwd ", "setfwd_delay ", "setfwd_text ",
                "setfwd_pos ", "fspam_on", "fspam_off", "showfwd", "join ",
                "addfosh", "listfosh", "removefosh ", "setenemy", "enemyoff", "setreply ",
                "copy ", "back", "ping", "status", "sudo su", "kiladmin",
                "bitch ", "time ", "start", "stop", "set "
            )):
                trailing_match = re.match(r"^(.*?)(?:\s+)?(\d+)\s*$", raw_text)
                if trailing_match:
                    message_text = trailing_match.group(1).strip()
                    count = int(trailing_match.group(2))
                    if message_text and count > 0:
                        reply_to_id = event.message.reply_to_msg_id or event.message.id
                        try:
                            for _ in range(count):
                                await client_instance.send_message(event.chat_id, message_text, reply_to=reply_to_id)
                                await asyncio.sleep(0.1)
                        except Exception as e:
                            print(f"[ERROR] Repeat reply failed: {e}")
                        return
    
    me = await client_instance.get_me()

    if user_id not in ADMIN_IDS:
        print(f"[BOT] Ignored non-admin message from {user_id}")
        return
    
    if event.is_private:
        location = "PRIVATE"
    elif event.is_group:
        location = "GROUP"
    elif event.is_channel:
        location = "CHANNEL"
    else:
        location = "UNKNOWN"
    
    print(f"[BOT] Admin {user_id} in {location}: {text[:50]}")
    
    # HELP COMMANDS
    if text == "help" or text == "راهنما":
        await send_loading_animation(event)
        help_text = """
> spam - Start spam 
> spamoff - Stop spam 
> setfosh <text> - 
> speed <1-60> - Set speed
> id - Get chat ID
> setid <chat_id> - Set target
> join <link> - Join link 
> ping - Check bot ping
> status - Show status
> help2
> Development by @DevilWillCryBitch
"""
        try:
            await client_instance.send_file(
                event.chat_id,
                HELP_IMAGE_URL,
                caption=help_text,
                reply_to=event.message.id,
            )
        except Exception as e:
            print(f"[ERROR] Help media send failed: {e}")
            try:
                await client_instance.send_message(event.chat_id, help_text, reply_to=event.message.id)
            except Exception as fallback_error:
                print(f"[ERROR] Help text fallback failed: {fallback_error}")
        return

    if text == "help2":
        await send_loading_animation(event)
        help_text = """
> sudo su <user id> - Add admin 
> kiladmin <user id> - Remove admin
> copy @user - Clone profile
> back - Restore original profile
> on - Start number fight 
> off - Stop number fight 
> setenemy - Mark user as enemy 
> enemyoff - Remove user from enemy list
> listfosh - Show the fosh list
> addfosh - Add fosh (reply to message)
> removefosh <index> - Remove fosh
> bitch <user id> - Set users to tag
> set <symbol> - Set tag symbol
> time <seconds> - Set delay (1-60s)
> start - spam with your chose id  
> stop - Stop (start)
> Development by @DevilWillCryBitch
"""
        try:
            await client_instance.send_file(
                event.chat_id,
                HELP_IMAGE_URL,
                caption=help_text,
                reply_to=event.message.id,
            )
        except Exception as e:
            print(f"[ERROR] Help2 media send failed: {e}")
            try:
                await client_instance.send_message(event.chat_id, help_text, reply_to=event.message.id)
            except Exception as fallback_error:
                print(f"[ERROR] Help2 text fallback failed: {fallback_error}")
        return

    # ON/OFF (ALL BOTS)
    if text == "on":
        if not ON_OFF_ACTIVE:
            ON_OFF_ACTIVE = True
            if ON_OFF_TASK and not ON_OFF_TASK.done():
                ON_OFF_TASK.cancel()
            ON_OFF_TASK = asyncio.create_task(on_off_loop_all_bots(event.chat_id))
            await event.reply(f"ON start {len(clients)} ")
        return

    if text == "off":
        if ON_OFF_ACTIVE:
            ON_OFF_ACTIVE = False
            if ON_OFF_TASK and not ON_OFF_TASK.done():
                ON_OFF_TASK.cancel()
            await event.reply("OFF stopped")
        return

    # SPEED
    if text.startswith("speed "):
        try:
            new_speed = float(text[6:].strip())
            if 1 <= new_speed <= 60:
                SPAM_SPEED = new_speed
                print(f" Spam speed changed to {SPAM_SPEED}s")
                await event.reply(f"Speed set to {SPAM_SPEED} seconds")
        except ValueError:
            pass
        return  

    # SPAM (ALL BOTS)
    if text == "spam":
        if not SPAM_TARGET:
            await event.reply("No target chat set. Use setid first.")
            return
        if SPAM_ACTIVE:
            await event.reply("Spam is already running. Use spamoff to stop.")
            return
        
        SPAM_ACTIVE = True
        await event.reply(
            f" {len(clients)} \n"
            f" {SPAM_TARGET}\n"
            f" {SPAM_TEXT}\n"
            f" {SPAM_SPEED} seconds"
        )
        
        if SPAM_TASK and not SPAM_TASK.done():
            SPAM_TASK.cancel()
        SPAM_TASK = asyncio.create_task(spam_loop_all_bots(SPAM_TARGET, SPAM_TEXT, SPAM_SPEED))
        return
    
    if text == "spamoff":
        if SPAM_ACTIVE:
            SPAM_ACTIVE = False
            if SPAM_TASK and not SPAM_TASK.done():
                SPAM_TASK.cancel()
            await event.reply("SPAM STOP")
        else:
            await event.reply("NOT ACTIVE")
        return
    
    # SETFOSH
    if text.startswith("setfosh "):
        SPAM_TEXT = text[8:].strip()
        await event.reply(f"Spam text set to: {SPAM_TEXT}")
        return
    
    # ID
    if text == "id":
        chat_id = event.chat_id
        chat_type = "Private" if event.is_private else "Group" if event.is_group else "Channel"
        await event.reply(f"ID {chat_id}\nType: {chat_type}")
        return
    
    # SETID
    if text.startswith("setid "):
        try:
            SPAM_TARGET = int(text[6:].strip())
            await event.reply(f"Target set to {SPAM_TARGET}")
            try:
                with open(TARGET_ID_FILE, "w", encoding="utf-8") as f:
                    f.write(str(SPAM_TARGET))
            except Exception as e:
                print(f"[ERROR] Could not save target ID file: {e}")
        except ValueError:
            await event.reply("Invalid chat ID. Must be a number.")
        return

    # SETFWD
    if text.startswith("setfwd "):
        link = text[7:].strip()
        if not link:
            await event.reply("Usage: setfwd <message_link>")
            return
        try:
            cleaned = link.replace("https://", "").replace("http://", "").replace("t.me/", "").replace("telegram.me/", "")
            parts = cleaned.split("/")
            if len(parts) >= 3 and parts[0].lower() == "c":
                channel = str(int("-100" + parts[1]))
                msg_id = int(parts[2])
            elif len(parts) >= 2:
                channel = parts[0]
                msg_id = int(parts[1])
            else:
                await event.reply("Invalid setfwd link. Use a t.me link with message ID.")
                return
            with open(FWD_SOURCE_CHANNEL_FILE, "w", encoding="utf-8") as f:
                f.write(channel)
            with open(FWD_SOURCE_MSG_ID_FILE, "w", encoding="utf-8") as f:
                f.write(str(msg_id))
            await event.reply(f"Source set\nChannel: {channel}\nMessage ID: {msg_id}")
        except Exception as e:
            await event.reply(f"Failed to parse link: {e}")
        return

    # SETFWD_DELAY
    if text.startswith("setfwd_delay "):
        try:
            parts = text.split()
            min_d = float(parts[1])
            max_d = float(parts[2]) if len(parts) > 2 else min_d + 1
            if min_d < 0.5:
                min_d = 0.5
            if max_d < min_d:
                max_d = min_d + 1
            with open(FWD_DELAY_MIN_FILE, "w", encoding="utf-8") as f:
                f.write(str(min_d))
            with open(FWD_DELAY_MAX_FILE, "w", encoding="utf-8") as f:
                f.write(str(max_d))
            await event.reply(f"Delay: {min_d}-{max_d} seconds")
        except Exception:
            await event.reply("Usage: setfwd_delay <min> <max>")
        return

    # SETFWD_TEXT
    if text.startswith("setfwd_text "):
        extra_text = text[12:].strip()
        with open(FWD_EXTRA_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write(extra_text)
        await event.reply("Extra text set")
        return

    # SETFWD_POS
    if text.startswith("setfwd_pos "):
        pos = text[11:].strip().lower()
        if pos not in ["before", "after"]:
            await event.reply("Usage: setfwd_pos before or setfwd_pos after")
            return
        with open(FWD_EXTRA_POSITION_FILE, "w", encoding="utf-8") as f:
            f.write(pos)
        await event.reply(f"Position: {pos}")
        return

    # FSPAM (ALL BOTS)
    if text == "fspam_on":
        if FORWARD_SPAM_ACTIVE:
            await event.reply("Forward spam is already running.")
            return
        FORWARD_SPAM_ACTIVE = True
        if FORWARD_SPAM_TASK and not FORWARD_SPAM_TASK.done():
            FORWARD_SPAM_TASK.cancel()
        FORWARD_SPAM_TASK = asyncio.create_task(forward_spam_all_bots())
        await event.reply(f"FWD SPAM RUNNING with ALL {len(clients)} bots")
        return

    if text == "fspam_off":
        if FORWARD_SPAM_ACTIVE:
            FORWARD_SPAM_ACTIVE = False
            if FORWARD_SPAM_TASK and not FORWARD_SPAM_TASK.done():
                FORWARD_SPAM_TASK.cancel()
            await event.reply("FWD SPAM STOPPED")
        else:
            await event.reply("Forward spam is not running.")
        return

    # SHOWFWD
    if text == "showfwd":
        source = read_forward_file(FWD_SOURCE_CHANNEL_FILE)
        msg_id = read_forward_file(FWD_SOURCE_MSG_ID_FILE, "0")
        min_delay = read_forward_file(FWD_DELAY_MIN_FILE, "3")
        max_delay = read_forward_file(FWD_DELAY_MAX_FILE, "10")
        target = SPAM_TARGET or int(read_forward_file(TARGET_ID_FILE, "1") or "1")
        status = "RUNNING" if FORWARD_SPAM_ACTIVE else "STOPPED"
        await event.reply(f"Forward Config - {status}\nTARGET: {target}\nSOURCE: {source}/{msg_id}\nDELAY: {min_delay}-{max_delay} seconds")
        return

    # JOIN (ALL BOTS)
    if text.startswith("join "):
        invite_input = raw_text[5:].strip()
        if not invite_input:
            await event.reply("Usage: join <invite_link> or join @channelname")
            return

        invite_input = invite_input.strip()
        target = normalize_join_target(invite_input)
        if not target:
            await event.reply("Invalid invite link.")
            return

        try:
            entity = None
            try:
                entity = await MASTER_CLIENT.get_entity(target if not target.startswith("@") else target[1:])
            except:
                pass

            if not entity:
                await event.reply("Could not find the channel/group.")
                return

            joined_count = 0
            for i, client in enumerate(clients):
                try:
                    await client(JoinChannelRequest(entity))
                    joined_count += 1
                    print(f"[JOIN] Bot {i} joined {invite_input}")
                    await asyncio.sleep(0.5)
                except UserAlreadyParticipantError:
                    joined_count += 1
                    print(f"[JOIN] Bot {i} already joined")
                except Exception as e:
                    print(f"[JOIN] Bot {i} error: {e}")

            await event.reply(f"{joined_count}/{len(clients)} bots joined successfully")
        except Exception as e:
            await event.reply(f"Failed to join: {e}")
        return

    # ADDFOSH
    if text == "addfosh":
        if not event.is_reply:
            await event.reply("Reply to a message and type addfosh")
            return

        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.text:
            await event.reply("The replied message has no text.")
            return

        FOSHLIST.append(replied_msg.text)
        save_fosh_file()
        await event.reply(
            f"Fosh added (Index #{len(FOSHLIST)-1})\n"
            f"Preview: {replied_msg.text[:50]}..."
        )
        return

    await _commands_handler(event, text, client_instance)

# Load fosh file
try:
    with open(FOSH_FILE, "r", encoding="utf-8") as f:
        FOSHLIST: List[str] = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    FOSHLIST: List[str] = [
        "بیا پایین",
        "کصخل",
        "برو گمشو"
    ]
    print("fosh.txt not found. Using default fosh list.")


async def _commands_handler(event, text, client):
    global ADMIN_IDS, FOSHLIST, ENEMY_TARGET, ENEMY_ACTIVE, REPLY_TO_ENEMY, ORIGINAL_NAME, ORIGINAL_PHOTO
    global TAG_TARGETS, TAG_SPAM_ACTIVE, TAG_SPAM_TASK, TAG_SPAM_DELAY, TAG_SPAM_CHAT_ID, TAG_SYMBOL
    user_id = event.sender_id

    # LISTFOSH
    if text == "listfosh":
        if not FOSHLIST:
            await event.reply("Foshlist is empty. Use addfosh to fill it.")
            return
        lines = []
        for i, item in enumerate(FOSHLIST):
            snippet = item.replace("\n", " ")[:60]
            lines.append(f"{i}: {snippet}...")
        msg = "FOSHLIST (index to use with removefosh):\n" + "\n".join(lines[:20])
        if len(lines) > 20:
            msg += f"\n... and {len(lines)-20} more."
        await event.reply(msg)
        return

    # REMOVEFOSH
    if text.startswith("removefosh "):
        try:
            idx = int(text[11:].strip())
            if idx < 0 or idx >= len(FOSHLIST):
                await event.reply("Index out of range.")
                return
            removed = FOSHLIST.pop(idx)
            save_fosh_file()
            await event.reply(f"Removed fosh {idx}:\n{removed[:50]}...")
        except ValueError:
            await event.reply("Invalid index. Must be a number.")
        return

    # SETENEMY
    if text == "setenemy":
        if not event.is_reply:
            await event.reply("Reply to a message to mark as enemy.")
            return

        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.sender_id:
            await event.reply("Could not identify the user.")
            return

        target_user = await client.get_entity(replied_msg.sender_id)
        ENEMY_TARGET = target_user.id
        ENEMY_ACTIVE = True
        await event.reply(
            f"Enemy set: @{target_user.username or target_user.first_name or 'Unknown'}\n"
            f"ID: {ENEMY_TARGET}"
        )
        return

    # ENEMYOFF
    if text == "enemyoff":
        if ENEMY_ACTIVE:
            ENEMY_ACTIVE = False
            await event.reply("Enemy mode deactivated.")
        else:
            await event.reply("Enemy mode is already off.")
        return

    # SETREPLY
    if text.startswith("setreply "):
        mode = text[9:].strip().lower()
        if mode not in ["on", "off"]:
            await event.reply("Usage: setreply on or setreply off")
            return
        REPLY_TO_ENEMY = mode == "on"
        await event.reply(f"Auto-reply set to: {REPLY_TO_ENEMY}")
        return
    
    # COPY
    if text.startswith("copy "):
        target_identifier = text[6:].strip()
        if target_identifier.startswith("@"):
            target_identifier = target_identifier[1:]
        
        await event.reply(f"Searching for user: {target_identifier}...")
        
        try:
            try:
                target_user = await client.get_entity(target_identifier)
            except:
                if target_identifier.isdigit():
                    try:
                        target_user = await client.get_entity(int(target_identifier))
                    except:
                        target_user = None
                else:
                    target_user = None
            
            if not target_user and event.is_reply:
                replied_msg = await event.get_reply_message()
                if replied_msg and replied_msg.sender_id:
                    target_user = await client.get_entity(replied_msg.sender_id)
            
            if not target_user:
                await event.reply("Could not find user.")
                return
            
            me = await client.get_me()
            if not ORIGINAL_NAME:
                ORIGINAL_NAME = me.first_name or ""
            
            if not ORIGINAL_PHOTO:
                try:
                    photos = await client.get_profile_photos(me, limit=1)
                    if photos:
                        ORIGINAL_PHOTO = photos[0]
                except:
                    pass
            
            await event.reply(f"Cloning {target_user.first_name or 'Unknown'}...")
            
            try:
                photos = await client.get_profile_photos(target_user, limit=1)
                if photos:
                    photo = photos[0]
                    photo_path = await client.download_media(photo, file="temp_profile.jpg")
                    if photo_path:
                        await client(UploadProfilePhotoRequest(
                            file=await client.upload_file(photo_path)
                        ))
                        await event.reply("Profile picture cloned successfully")
                        try:
                            os.remove(photo_path)
                        except:
                            pass
            except Exception as e:
                await event.reply(f"Failed to set profile picture: {str(e)[:100]}")
            
            new_first_name = target_user.first_name or ""
            new_last_name = target_user.last_name or ""
            
            try:
                await client(UpdateProfileRequest(
                    first_name=new_first_name,
                    last_name=new_last_name
                ))
                await event.reply(f"Name cloned: {new_first_name} {new_last_name}".strip())
            except Exception as e:
                await event.reply(f"Failed to set name: {str(e)[:100]}")
            
            await event.reply(f"CLONE COMPLETE\nID: {target_user.id}")
            
        except Exception as e:
            await event.reply(f"Clone failed: {str(e)[:200]}")
        return
    
    # BACK
    if text == "back":
        try:
            photos = await client.get_profile_photos(await client.get_me(), limit=1)
            if photos:
                await client(DeletePhotosRequest(id=[photos[0]]))
            
            if ORIGINAL_PHOTO:
                try:
                    photo_path = await client.download_media(ORIGINAL_PHOTO, file="orig_profile.jpg")
                    if photo_path:
                        await client(UploadProfilePhotoRequest(
                            file=await client.upload_file(photo_path)
                        ))
                        try:
                            os.remove(photo_path)
                        except:
                            pass
                except:
                    pass
            
            if ORIGINAL_NAME:
                await client(UpdateProfileRequest(
                    first_name=ORIGINAL_NAME,
                    last_name=""
                ))
            
            await event.reply("back")
        except Exception as e:
            await event.reply(f"faild{str(e)[:100]}")
        return

    # BITCH (set tag targets)
    if text.startswith("bitch"):
        try:
            parts = text.split()
            if len(parts) < 2:
                await event.reply("Provide at least one User ID.\nUsage: bitch user_id1 user_id2 ...")
                return
            
            user_ids = []
            invalid_ids = []
            
            for part in parts[1:]:
                try:
                    user_id = int(part.strip())
                    user_ids.append(user_id)
                except ValueError:
                    invalid_ids.append(part)
            
            if invalid_ids:
                await event.reply(f"Invalid user IDs: {', '.join(invalid_ids)}")
                return
            
            if not user_ids:
                await event.reply("No valid User IDs provided.")
                return
            
            TAG_TARGETS = user_ids
            await event.reply(f"{len(TAG_TARGETS)} \nIDs: {'`, `'.join(map(str, TAG_TARGETS))}")
            
        except Exception as e:
            await event.reply(f"Error: {str(e)}")
        return

    # TIME (set tag delay)
    if text.startswith("time "):
        try:
            delay = float(text[5:].strip())
            if 1 <= delay <= 60:
                TAG_SPAM_DELAY = delay
                await event.reply(f"{TAG_SPAM_DELAY} seconds.")
            else:
                await event.reply("Delay must be between 1 and 60 seconds.")
        except ValueError:
            await event.reply("Invalid number. Use time <seconds> (1-60).")
        return

    # START (tag spam with ALL bots)
    if text == "start":
        if TAG_SPAM_ACTIVE:
            await event.reply("Tag spam is already running. Use stop first")
            return
        if not FOSHLIST:
            await event.reply("No fosh messages available. Use addfosh first")
            return
        if not TAG_TARGETS:
            await event.reply("No tag targets set. Use bitch <ids> first")
            return
        
        TAG_SPAM_CHAT_ID = event.chat_id
        TAG_SPAM_ACTIVE = True
        if TAG_SPAM_TASK and not TAG_SPAM_TASK.done():
            TAG_SPAM_TASK.cancel()
        TAG_SPAM_TASK = asyncio.create_task(tag_spam_all_bots_loop(TAG_SPAM_CHAT_ID))
        await event.reply(
            f"Tag spam started with ALL {len(clients)} bots\n"
            f"Targets: {len(TAG_TARGETS)} user(s)\n"
            f"Delay: {TAG_SPAM_DELAY}s\n"
            f"Fosh count: {len(FOSHLIST)}\n"
            f"Symbol: {TAG_SYMBOL}"
        )
        return

    # STOP (tag spam)
    if text == "stop":
        if not TAG_SPAM_ACTIVE:
            await event.reply("Tag spam is not running.")
            return
        TAG_SPAM_ACTIVE = False
        if TAG_SPAM_TASK and not TAG_SPAM_TASK.done():
            TAG_SPAM_TASK.cancel()
        await event.reply("ok ")
        return

    # SET (symbol)
    if text.startswith("set"):
        symbol = text[10:].strip()
        if not symbol:
            await event.reply("Please provide a symbol.\nUsage: set <symbol>")
            return
        TAG_SYMBOL = symbol
        await event.reply(f"Tag symbol set to: {TAG_SYMBOL}")
        return

    # PING
    if text == "bot":
        await event.reply("O N L I N E")
        return
    
    # STATUS
    if text == "status":
        status_msg = f"""
BOT STATUS

Admins: {len(ADMIN_IDS)} users
Bots online: {len(clients)}/{len(BOT_TOKENS)}
Spam target: {SPAM_TARGET or 'Not set'}
Spam text: {SPAM_TEXT[:50]}...
Spam speed: {SPAM_SPEED} seconds
Spam active: {SPAM_ACTIVE}
Enemy target: {ENEMY_TARGET or 'None'}
Enemy active: {ENEMY_ACTIVE}
Fosh count: {len(FOSHLIST)}
Tag targets: {len(TAG_TARGETS)} user(s)
Tag delay: {TAG_SPAM_DELAY}s
Tag symbol: {TAG_SYMBOL}
"""
        await event.reply(status_msg)
        return
    
    # SUDO SU (add admin)
    if text.startswith("sudo su"):
        try:
            parts = text.split()
            if len(parts) < 3:
                await event.reply("Usage: sudo su <user_id>")
                return
            try:
                new_admin = int(parts[2].strip())
            except ValueError:
                await event.reply("Invalid user ID. Must be a number.")
                return

            if new_admin == user_id:
                await event.reply("You already have root permission.")
                return
            if new_admin in ADMIN_IDS:
                await event.reply("User is already an admin.")
                return
            ADMIN_IDS.add(new_admin)
            await event.reply(f"User {new_admin} now has root permission")
            print(f"[BOT] New admin added: {new_admin}")
        except Exception as e:
            await event.reply(f"Failed to add admin: {str(e)[:100]}")
        return

    # KILADMIN (remove admin)
    if text.startswith("kiladmin"):
        try:
            parts = text.split(maxsplit=1)  
            if len(parts) < 2:
                await event.reply("Usage: kiladmin <user_id>")
                return
            rem_admin = int(parts[1].strip())
            
            if rem_admin not in ADMIN_IDS:
                await event.reply("User doesn't have root permission.")
                return
            if len(ADMIN_IDS) <= 1:
                await event.reply("Cannot remove the last root user.")
                return
            ADMIN_IDS.remove(rem_admin)
            await event.reply(f"User {rem_admin} no longer has root permission")
            print(f"[BOT] Admin removed: {rem_admin}")
        except (ValueError, IndexError):
            await event.reply("Invalid user ID.")
        return


async def run_bot(index, token):
    """Run a single bot instance."""
    global clients, MASTER_CLIENT
    
    client = TelegramClient(f"bot_session_{index}", API_ID, API_HASH)
    await client.start(bot_token=token)
    clients.append(client)
    
    if index == MASTER_BOT_INDEX:
        MASTER_CLIENT = client
    
    me = await client.get_me()
    
    print(f"[BOT {index}] Logged in as: {me.first_name} (@{me.username})")
    print(f"[BOT {index}] User ID: {me.id}")
    
    client.add_event_handler(handle_all_messages, events.NewMessage(incoming=True))
    
    await client.run_until_disconnected()


async def main():
    global ALL_BOTS_RUNNING
    
    print("=" * 60)
    print("[BOT] Starting Multi-Bot System...")
    print(f"[BOT] Admins: {ADMIN_IDS}")
    print(f"[BOT] Total Bots: {len(BOT_TOKENS)}")
    print(f"[BOT] Master Bot Index: {MASTER_BOT_INDEX}")
    print("[BOT] ALL commands run on ALL bots")
    print("=" * 60)
    
    ensure_forward_files()
    
    bot_tasks = []
    for i, token in enumerate(BOT_TOKENS):
        if not token or token.startswith("YOUR_BOT_TOKEN"):
            print(f"[BOT] Skipping bot {i+1} - Invalid token")
            continue
        task = asyncio.create_task(run_bot(i, token))
        bot_tasks.append(task)
        await asyncio.sleep(0.5)
    
    if not bot_tasks:
        print("[BOT] No valid bot tokens found")
        return
    
    print("[BOT] ALL BOTS STARTED")
    print("=" * 60)
    
    await asyncio.gather(*bot_tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[BOT] Shutting down...")
    except Exception as e:
        print(f"[ERROR] Bot crashed: {e}")
