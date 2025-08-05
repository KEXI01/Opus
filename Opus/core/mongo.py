from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI
from Opus.logging import LOGGER

LOGGER(__name__).info("☁️ Iɴɪᴛɪᴀᴛɪɴɢ Mᴏɴɢᴏ Cᴏɴɴᴇᴄᴛɪᴏɴ...")

try:
    _mongo_async_ = AsyncIOMotorClient(MONGO_DB_URI)
    mongodb = _mongo_async_.Opus
    LOGGER(__name__).info("✅ Mᴏɴɢᴏ Lɪɴᴋᴇᴅ » Dᴀᴛᴀғʟᴏᴡ sᴛᴀʙʟɪsʜᴇᴅ.")
except Exception as e:
    LOGGER(__name__).error(f"❌ Cᴏɴɴᴇᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ » Mᴏɴɢᴏᴅʙ ᴇʀʀᴏʀ: {e}")
    exit()
