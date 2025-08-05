import os
import re
import asyncio
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.enums import ChatAction
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
    Message,
)

from Opus import app, YouTube
from config import (
    BANNED_USERS,
    SONG_DOWNLOAD_DURATION,
    SONG_DOWNLOAD_DURATION_LIMIT,
    SONG_DUMP_ID,
    LOGGER_ID,
)
from Opus.utils.decorators.language import language, languageCB
from Opus.utils.errors import capture_err, capture_callback_err
from Opus.utils.formatters import convert_bytes, time_to_seconds
from Opus.utils.inline.song import song_markup
from Opus.utils.database import is_on_off, get_spam_data, add_spam_data, block_user
from Opus.utils.downloader import download_audio_concurrent, yt_dlp_download  # Import the new downloader functions

SONG_COMMAND = ["song", "music"]

class InlineKeyboardBuilder(list):
    def row(self, *buttons):
        self.append(list(buttons))

@app.on_message(filters.command(SONG_COMMAND) & filters.group & ~BANNED_USERS)
@capture_err
@language
async def song_command_group(client, message: Message, lang):
    await message.reply_text(
        lang["song_1"],
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(lang["SG_B_1"],
                                   url=f"https://t.me/{app.username}?start=song")]]
        ),
    )

@app.on_message(filters.command(SONG_COMMAND) & filters.private & ~BANNED_USERS)
@capture_err
@language
async def song_command_private(client, message: Message, lang):
    await message.delete()
    mystic = await message.reply_text(lang["play_1"])

    url = await YouTube.url(message)
    query = url or (message.text.split(None, 1)[1] if len(message.command) > 1 else None)
    if not query:
        return await mystic.edit_text(lang["song_2"])

    if url and not await YouTube.exists(url):
        return await mystic.edit_text(lang["song_5"])

    try:
        title, dur_min, dur_sec, thumb, vidid = await YouTube.details(query)
    except Exception:
        return await mystic.edit_text(lang["play_3"])

    if not dur_min:
        return await mystic.edit_text(lang["song_3"])
    if int(dur_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(lang["play_4"].format(SONG_DOWNLOAD_DURATION, dur_min))

    await mystic.delete()
    await message.reply_photo(
        thumb,
        caption=lang["song_4"].format(title),
        reply_markup=InlineKeyboardMarkup(song_markup(lang, vidid)),
    )

@app.on_callback_query(filters.regex(r"song_back") & ~BANNED_USERS)
@capture_callback_err
@languageCB
async def songs_back_helper(client, cq, lang):
    _ignored, req = cq.data.split(None, 1)
    stype, vidid = req.split("|")
    await cq.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(song_markup(lang, vidid))
    )

@app.on_callback_query(filters.regex(r"song_helper") & ~BANNED_USERS)
@capture_callback_err
@languageCB
async def song_helper_cb(client, cq, lang):
    _ignored, req = cq.data.split(None, 1)
    stype, vidid = req.split("|")

    try:
        await cq.answer(lang["song_6"], show_alert=True)
    except Exception:
        pass

    try:
        formats, _yturl = await YouTube.formats(vidid)
    except Exception:
        return await cq.edit_message_text(lang["song_7"])

    kb = InlineKeyboardBuilder()
    seen = set()

    if stype == "audio":
        for f in formats:
            if "audio" not in f["format"] or not f["filesize"]:
                continue
            label = f["format_note"].title()
            if label in seen:
                continue
            seen.add(label)
            kb.row(
                InlineKeyboardButton(
                    text=f"{label} • {convert_bytes(f['filesize'])}",
                    callback_data=f"song_download {stype}|{f['format_id']}|{vidid}",
                )
            )
    else:
        allowed = {160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266}
        for f in formats:
            # FIXED: Handle non-numeric format IDs with try-except
            try:
                format_id_int = int(f["format_id"])
                if not f["filesize"] or format_id_int not in allowed:
                    continue
            except ValueError:
                # Skip non-numeric format IDs (like '249-drc')
                continue
            
            res = f["format"].split("-")[1]
            kb.row(
                InlineKeyboardButton(
                    text=f"{res} • {convert_bytes(f['filesize'])}",
                    callback_data=f"song_download {stype}|{f['format_id']}|{vidid}",
                )
            )

    kb.row(
        InlineKeyboardButton(lang["BACK_BUTTON"], callback_data=f"song_back {stype}|{vidid}"),
        InlineKeyboardButton(lang["CLOSE_BUTTON"], callback_data="close"),
    )
    await cq.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex(r"song_download") & ~BANNED_USERS)
@capture_callback_err
@languageCB
async def song_download_cb(client, cq, lang):
    user_id = cq.from_user.id
    _ignored, req = cq.data.split(None, 1)
    stype, fmt_id, vidid = req.split("|")
    yturl = f"https://www.youtube.com/watch?v={vidid}"

    spam_count = await get_spam_data(user_id)
    if spam_count and spam_count >= 5:
        await block_user(user_id, 600)
        return await cq.answer("You Are Spamming Now! Blocked for 10 minutes For Using /song or /music command.", show_alert=True)
    await add_spam_data(user_id)

    try:
        await cq.answer("Downloading... Please wait...")
    except Exception:
        pass

    mystic = await cq.edit_message_text(lang["song_8"])
    file_path = None
    thumb = None
    try:
        info, _ = await YouTube.track(yturl)
        title = re.sub(r"\W+", " ", info["title"])
        thumb = await cq.message.download()
        duration_sec = time_to_seconds(info.get("duration_min")) if info.get("duration_min") else None

        if stype == "audio":
            file_path = await download_audio_concurrent(yturl)  # Use download_audio_concurrent for audio
            if not file_path or not os.path.exists(file_path):
                await mystic.edit_text(lang["song_10"])
                return
            await mystic.edit_text(lang["song_11"])
            await app.send_chat_action(cq.message.chat.id, ChatAction.UPLOAD_AUDIO)
            await cq.edit_message_media(
                InputMediaAudio(
                    media=file_path,
                    caption=title,
                    thumb=thumb,
                    title=title,
                    performer=info.get("uploader"),
                )
            )
            await app.send_audio(
                SONG_DUMP_ID,
                audio=file_path,
                caption="Powered by 🌌 Space Api",
                title=title,
                performer=info.get("uploader"),
                duration=duration_sec,
                thumb=thumb,
            )
        else:
            file_path = await yt_dlp_download(yturl, type="video", format_id=fmt_id)  # Use yt_dlp_download for video
            if not file_path or not os.path.exists(file_path):
                await mystic.edit_text(lang["song_10"])
                return
            w, h = cq.message.photo.width, cq.message.photo.height
            await mystic.edit_text(lang["song_11"])
            await app.send_chat_action(cq.message.chat.id, ChatAction.UPLOAD_VIDEO)
            await cq.edit_message_media(
                InputMediaVideo(
                    media=file_path,
                    duration=duration_sec,
                    width=w,
                    height=h,
                    thumb=thumb,
                    caption=title,
                    supports_streaming=True,
                )
            )
            await app.send_video(
                SONG_DUMP_ID,
                video=file_path,
                caption="Powered by 🌌 Space Api",
                duration=duration_sec,
                thumb=thumb,
                supports_streaming=True,
                width=w,
                height=h,
            )

        if await is_on_off("LOG_COMMAND"):
            await app.send_message(
                LOGGER_ID,
                f"#SONG\nUser: {cq.from_user.mention} (`{user_id}`)\nQuery: `{yturl}`\nType: `{stype}`",
            )

        async def cleanup(path):
            await asyncio.sleep(300)
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"[CLEANUP] Removed file: {path}")
                except Exception as e:
                    print(f"[CLEANUP] Failed: {e}")

        if file_path:
            asyncio.create_task(cleanup(file_path))

    except Exception as err:
        print(f"[SONG] download/upload error: {err}")
        await mystic.edit_text(lang["song_10"])
    finally:
        try:
            if thumb and os.path.exists(thumb):
                os.remove(thumb)
                print(f"[CLEANUP] Removed thumb: {thumb}")
        except Exception:
            pass
