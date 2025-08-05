import os
import re
import random
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()


API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
BOT_USERNAME = getenv("BOT_USERNAME", "StormMusicPlayer_bot")

OWNER_ID = int(getenv("OWNER_ID", "7639428220"))
OWNER_USERNAME = getenv("OWNER_USERNAME", "ll_KEX_ll")
EVALOP = list(map(int, getenv("EVALOP", "7639428220").split()))

LOGGER_ID = int(getenv("LOGGER_ID", ""))
DEBUG_IGNORE_LOG = True
LOG_ERROR_ID = "-1002139499282"
SONG_DUMP_ID = int(getenv("SONG_DUMP_ID", "-1002139499282"))
ASSUSERNAME = getenv("ASSUSERNAME", "None")
STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/storm_techh")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/storm_core")
LOG_CHAT_LINK = "https://t.me/STORM_CORE"

BOT_NAME = getenv("BOT_NAME", "˹Opus")

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 777777))
DURATION_LIMIT = int(sum(
    int(x) * 60**i for i, x in enumerate(reversed(f"{DURATION_LIMIT_MIN}:00".split(":")))
))
RESTART_INTERVAL = int(getenv("RESTART_INTERVAL", 86400))
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", True))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 70))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 104857600))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 1073741824))

SERVER_PLAYLIST_LIMIT = int(getenv("SERVER_PLAYLIST_LIMIT", "3000"))
AUTO_SUGGESTION_MODE = getenv("AUTO_SUGGESTION_MODE", "False")
AUTO_SUGGESTION_TIME = int(getenv("AUTO_SUGGESTION_TIME", "60"))

START_IMG_URL = getenv("START_IMG_URL", "https://envs.sh/lSU.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://graph.org/file/9077cd2ba5818efef2d28.jpg")
PLAYLIST_IMG_URL = getenv("PLAYLIST_IMG_URL", "https://graph.org/file/eb1e2b58e17964083db73.jpg")
STATS_IMG_URL = getenv("STATS_IMG_URL", "https://envs.sh/Ol4.jpg")
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/7c4ib1.jpg"
TELEGRAM_AUDIO_URL = getenv("TELEGRAM_AUDIO_URL", "https://envs.sh/Olr.jpg")
TELEGRAM_VIDEO_URL = getenv("TELEGRAM_VIDEO_URL", "https://envs.sh/Olr.jpg")
STREAM_IMG_URL = getenv("STREAM_IMG_URL", "https://envs.sh/Olk.jpg")
APPLE_IMG_URL = "https://files.catbox.moe/cq87ww.jpg"
YOUTUBE_IMG_URL = getenv("YOUTUBE_IMG_URL", "https://files.catbox.moe/6xpaz5.jpg")
FAILED = "https://files.catbox.moe/6xpaz5.jpg"

SPOTIFY_ARTIST_IMG_URL = getenv("SPOTIFY_ARTIST_IMG_URL", "https://envs.sh/Olk.jpg")
SPOTIFY_ALBUM_IMG_URL = getenv("SPOTIFY_ALBUM_IMG_URL", "https://envs.sh/Olk.jpg")
SPOTIFY_PLAYLIST_IMG_URL = getenv("SPOTIFY_PLAYLIST_IMG_URL", "https://envs.sh/Olk.jpg")

API_URL = getenv("API_URL", "https://vortex.webs.vc")
MONGO_DB_URI = getenv("MONGO_DB_URI", None)
URL1 = getenv("URL1", None)
URL2 = getenv("URL2", None)
API_URL1 = getenv("API_URL1", None)
API_URL2 = getenv("API_URL2", None)
API_KEY = getenv("API_KEY", None)
COOKIE_URL = getenv("COOKIE_URL", None)

UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/KEXI01/Opus")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", "")
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")
REPO_PASS = int(getenv("REPO_PASS", "0"))
REPO_PASSWORD = getenv("REPO_PASSWORD", None)

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "2d3fd5ccdd3d43dda6f17864d8eb7281")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "48d311d8910a4531ae81205e1f754d27")

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

def time_to_seconds(time: str) -> int:
    return sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))

DURATION_LIMIT = time_to_seconds(f"{DURATION_LIMIT_MIN}:00")

BANNED_USERS = filters.user()
adminlist, lyrical, votemode, autoclean, confirmer = {}, {}, {}, [], {}


def validate_url(url, url_type):
    if url and not re.match(r"(?:http|https)://", url):
        raise SystemExit(f"[ERROR] - Your {url_type} url is wrong. Please ensure that it starts with https://")

validate_url(SUPPORT_CHANNEL, "SUPPORT_CHANNEL")
validate_url(SUPPORT_CHAT, "SUPPORT_CHAT")
