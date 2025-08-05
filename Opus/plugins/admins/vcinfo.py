from pyrogram import filters
from pyrogram.types import Message

from config import BANNED_USERS
from Opus import app
from Opus.core.call import Space
from Opus.utils.database import group_assistant
from Opus.utils.admin_filters import admin_filter


@app.on_message(filters.command("volume") & filters.group & admin_filter & ~BANNED_USERS)
async def set_volume(client, message: Message):
    chat_id = message.chat.id

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text("⚠️ ᴜꜱᴀɢᴇ: <code>/volume 1-200</code>")
    
    try:
        volume_level = int(args[1])
    except ValueError:
        return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ. ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ <code>/volume 1-200</code>")
    
    if volume_level == 0:
        return await message.reply_text("🔇 ᴜꜱᴇ <code>/mute</code> ᴛᴏ ᴍᴜᴛᴇ ᴛʜᴇ ꜱᴛʀᴇᴀᴍ.")
    
    if not 1 <= volume_level <= 200:
        return await message.reply_text("⚠️ ᴠᴏʟᴜᴍᴇ ᴍᴜꜱᴛ ʙᴇ ʙᴇᴛᴡᴇᴇɴ 1 ᴀɴᴅ 200.")
    
    if chat_id >= 0:
        return await message.reply_text("❌ ᴠᴏʟᴜᴍᴇ ᴄᴏɴᴛʀᴏʟ ɪꜱ ɴᴏᴛ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ɪɴ ʙᴀꜱɪᴄ ɢʀᴏᴜᴘꜱ.")
    
    try:
        await Space.change_volume(chat_id, volume_level)
        await message.reply_text(
            f"<b>🔊 ꜱᴛʀᴇᴀᴍ ᴠᴏʟᴜᴍᴇ ꜱᴇᴛ ᴛᴏ {volume_level}</b>.\n\nʀᴇQᴜᴇꜱᴛᴇᴅ ʙʏ: {message.from_user.mention} 🥀"
        )
    except Exception as e:
        await message.reply_text(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴀɴɢᴇ ᴠᴏʟᴜᴍᴇ.\n{e}")