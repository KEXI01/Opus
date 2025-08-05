import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import TelegramServerError
from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import AudioQuality, ChatUpdate, MediaStream, StreamEnded, Update, VideoQuality

import config
from strings import get_string
from Opus import LOGGER, YouTube, app
from Opus.misc import db
from Opus.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from Opus.utils.exceptions import AssistantErr
from Opus.utils.formatters import check_duration, seconds_to_min, speed_converter
from Opus.utils.inline.play import stream_markup
from Opus.utils.stream.autoclear import auto_clean
from Opus.utils.thumbnails import get_thumb
from Opus.utils.errors import capture_internal_err, send_large_error

autoend = {}
counter = {}

def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    """Create MediaStream compatible with pytgcalls v2.2.5"""
    if video:
        return MediaStream(
            path,
            audio_parameters=AudioQuality.MEDIUM,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=ffmpeg_params,
        )
    else:
        return MediaStream(
            path,
            audio_parameters=AudioQuality.STUDIO,
            ffmpeg_parameters=ffmpeg_params,
        )

async def _clear_(chat_id: int) -> None:
    popped = db.pop(chat_id, None)
    if popped:
        await auto_clean(popped)
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)
    await set_loop(chat_id, 0)

class Call:
    def __init__(self):
        self.userbot1 = Client(
            "RecXAss1", config.API_ID, config.API_HASH, session_string=config.STRING1
        ) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = Client(
            "RecXAss2", config.API_ID, config.API_HASH, session_string=config.STRING2
        ) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = Client(
            "RecXAss3", config.API_ID, config.API_HASH, session_string=config.STRING3
        ) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = Client(
            "RecXAss4", config.API_ID, config.API_HASH, session_string=config.STRING4
        ) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = Client(
            "RecXAss5", config.API_ID, config.API_HASH, session_string=config.STRING5
        ) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.pause(chat_id)  # Fixed method name
        except (IndexError, ValueError):
            raise AssistantErr("No assistant available")

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.resume(chat_id)  # Fixed method name
        except (IndexError, ValueError):
            raise AssistantErr("No assistant available")

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.mute(chat_id)  # Fixed method name
        except (IndexError, ValueError):
            raise AssistantErr("No assistant available")

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.unmute(chat_id)  # Fixed method name
        except (IndexError, ValueError):
            raise AssistantErr("No assistant available")

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
        except (IndexError, ValueError):
            await _clear_(chat_id)
            self.active_calls.discard(chat_id)
            return
            
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except NoActiveGroupCall:
            pass
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
        except (IndexError, ValueError):
            await _clear_(chat_id)
            self.active_calls.discard(chat_id)
            return
            
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except (IndexError, KeyError):
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except NoActiveGroupCall:
            pass
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        try:
            assistant = await group_assistant(self, chat_id)
            participants = await assistant.get_participants(chat_id)
            return [p.user_id for p in participants if not p.muted_by_admin]
        except:
            return []

    @capture_internal_err
    async def change_volume(self, chat_id: int, volume: int) -> None:
        try:
            assistant = await group_assistant(self, chat_id)
            volume = max(1, min(200, volume))
            await assistant.change_volume_call(chat_id, volume)
        except AttributeError:
            try:
                await assistant.set_call_property(chat_id, volume=volume)
            except:
                raise AssistantErr("Volume change not supported")
        except (IndexError, ValueError):
            raise AssistantErr("No assistant available")

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        # Convert and validate speed
        try:
            speed = float(speed)
        except (ValueError, TypeError):
            raise AssistantErr("Invalid speed value provided")
        
        if speed <= 0 or speed > 3.0:
            raise AssistantErr("Speed must be between 0.1 and 3.0")

        assistant = await group_assistant(self, chat_id)
        
        # Use original file if speed is 1.0
        if str(speed) == "1.0":
            out = file_path
        else:
            base = os.path.basename(file_path)
            # Clean filename and add proper extension
            clean_base = "".join(c for c in base if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not clean_base.endswith(('.mp3', '.mp4', '.wav', '.m4a')):
                clean_base += '.mp3'  # Default extension
                
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, clean_base)
            
            if not os.path.isfile(out):
                # Use your proven speed multipliers
                if str(speed) == "0.5":
                    vs = 2.0
                elif str(speed) == "0.75":
                    vs = 1.35
                elif str(speed) == "1.5":
                    vs = 0.68
                elif str(speed) == "2.0":
                    vs = 0.5
                else:
                    vs = 1.0 / float(speed)
                
                # Build FFmpeg command with proper format specification
                if playing[0]["streamtype"] == "video":
                    cmd = [
                        "ffmpeg", "-i", file_path,
                        "-filter:v", f"setpts={vs}*PTS",
                        "-filter:a", f"atempo={speed}",
                        "-c:v", "libx264", "-c:a", "aac",
                        "-preset", "ultrafast",
                        "-y", out
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-i", file_path,
                        "-filter:a", f"atempo={speed}",
                        "-c:a", "libmp3lame",
                        "-b:a", "128k",
                        "-y", out
                    ]
                
                try:
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    if proc.returncode != 0:
                        # If first attempt fails, try simpler approach
                        LOGGER(__name__).warning(f"First attempt failed, trying simpler approach")
                        
                        if playing[0]["streamtype"] == "video":
                            simple_cmd = [
                                "ffmpeg", "-i", file_path,
                                "-filter:v", f"setpts={vs}*PTS",
                                "-filter:a", f"atempo={speed}",
                                "-y", out
                            ]
                        else:
                            simple_cmd = [
                                "ffmpeg", "-i", file_path,
                                "-filter:a", f"atempo={speed}",
                                "-y", out
                            ]
                        
                        proc = await asyncio.create_subprocess_exec(
                            *simple_cmd,
                            stdin=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        
                        if proc.returncode != 0:
                            LOGGER(__name__).error(f"Both FFmpeg attempts failed: {stderr.decode()}")
                            # Use original file instead of failing
                            out = file_path
                            
                except Exception as e:
                    LOGGER(__name__).error(f"FFmpeg execution failed: {e}")
                    out = file_path

        # Get duration
        try:
            dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
            dur = int(float(dur))
        except (ValueError, TypeError):
            # Use original duration from database
            dur = int(playing[0].get("seconds", 180))

        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        
        # Create stream
        if playing[0]["streamtype"] == "video":
            stream = MediaStream(
                out,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.SD_480p,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        else:
            stream = MediaStream(
                out,
                audio_parameters=AudioQuality.STUDIO,
                ffmpeg_parameters=f"-ss {played} -to {duration}",
            )

        # Play stream
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.play(chat_id, stream)
        else:
            raise AssistantErr("Stream file mismatch during speedup")

        # Update database exactly like your v1.2.9
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    @capture_internal_err
    async def stream_call(self, link: str) -> None:
        try:
            assistant = await group_assistant(self, config.LOGGER_ID)
            stream = MediaStream(
                link,
                audio_parameters=AudioQuality.STUDIO,
            )
            await assistant.play(config.LOGGER_ID, stream)
        except ChatAdminRequired:
            LOGGER(__name__).warning(
                f"❌ Cannot start stream in LOGGER_ID ({config.LOGGER_ID}) — bot is not admin!"
            )
            try:
                await app.send_message(
                    config.OWNER_ID,
                    "❌ <b>Failed to stream in LOGGER_ID</b>\n\nReason: Bot is not admin in LOGGER chat.\n\n"
                    "Please promote the bot or update LOGGER_ID."
                )
            except Exception as e:
                LOGGER(__name__).warning(f"Failed to notify owner: {e}")
        except (IndexError, ValueError):
            LOGGER(__name__).warning("No assistant available for stream_call")
        except Exception as e:
            LOGGER(__name__).exception(f"❌ stream_call failed: {e}")

    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        
        if link.startswith(('http://', 'https://')) and 'index_' not in str(link):
            if video:
                stream = MediaStream(
                    link,
                    audio_parameters=AudioQuality.MEDIUM,
                    video_parameters=VideoQuality.HD_720p,
                )
            else:
                stream = MediaStream(
                    link,
                    audio_parameters=AudioQuality.STUDIO,
                )
        else:
            stream = dynamic_media_stream(path=link, video=bool(video))

        try:
            await assistant.play(chat_id, stream)
        except (NoActiveGroupCall, ChatAdminRequired):
            raise AssistantErr(_["call_8"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        except Exception as e:
            raise AssistantErr(
                f"ᴜɴᴀʙʟᴇ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴄᴀʟʟ.\nRᴇᴀsᴏɴ: {e}"
            )
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
                if users == 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except:
                pass

    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                if chat_id in self.active_calls:
                    try:
                        await client.leave_call(chat_id)
                    except NoActiveGroupCall:
                        pass
                    except Exception:
                        pass
                    finally:
                        self.active_calls.discard(chat_id)
                return
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except:
                return
        else:
            try:
                queued = check[0]["file"]
            except (KeyError, IndexError):
                LOGGER(__name__).warning(f"Corrupted queue entry in {chat_id}")
                return await self.play(client, chat_id)

            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0

            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0

            video = True if str(streamtype) == "video" else False

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                stream = dynamic_media_stream(path=link, video=video)
                try:
                    await client.play(chat_id, stream)
                except Exception:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], disable_web_page_preview=True
                    )

                stream = dynamic_media_stream(path=file_path, video=video)
                try:
                    await client.play(chat_id, stream)
                except:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

            elif "index_" in queued:
                try:
                    if videoid.startswith(('http://', 'https://')):
                        if video:
                            stream = MediaStream(
                                videoid,
                                audio_parameters=AudioQuality.MEDIUM,
                                video_parameters=VideoQuality.HD_720p,
                            )
                        else:
                            stream = MediaStream(
                                videoid,
                                audio_parameters=AudioQuality.STUDIO,
                            )
                    else:
                        stream = dynamic_media_stream(path=videoid, video=video)
                    
                    await client.play(chat_id, stream)
                except Exception as e:
                    LOGGER(__name__).error(f"Index streaming failed: {e}")
                    return await app.send_message(original_chat_id, text=_["call_6"])

                button = stream_markup(_, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                stream = dynamic_media_stream(path=queued, video=video)
                try:
                    await client.play(chat_id, stream)
                except:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=(
                            config.TELEGRAM_AUDIO_URL
                            if str(streamtype) == "audio"
                            else config.TELEGRAM_VIDEO_URL
                        ),
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                else:
                    img = await get_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    try:
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{app.username}?start=info_{videoid}",
                                title[:23],
                                check[0]["dur"],
                                user,
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                        )
                    except FloodWait as e:
                        LOGGER(__name__).warning(f"FloodWait: Sleeping for {e.value}")
                        await asyncio.sleep(e.value)
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{app.username}?start=info_{videoid}",
                                title[:23],
                                check[0]["dur"],
                                user,
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                        )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    async def start(self) -> None:
        LOGGER(__name__).info("Starting PyTgCalls Clients...")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        if config.STRING1 and self.one:
            try:
                pings.append(await self.one.ping)
            except:
                pass
        if config.STRING2 and self.two:
            try:
                pings.append(await self.two.ping)
            except:
                pass
        if config.STRING3 and self.three:
            try:
                pings.append(await self.three.ping)
            except:
                pass
        if config.STRING4 and self.four:
            try:
                pings.append(await self.four.ping)
            except:
                pass
        if config.STRING5 and self.five:
            try:
                pings.append(await self.five.ping)
            except:
                pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        assistants = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))
        
        if not assistants:
            LOGGER(__name__).warning("No assistants available for decorators")
            return

        CRITICAL_FLAGS = (
            ChatUpdate.Status.KICKED |
            ChatUpdate.Status.LEFT_GROUP |
            ChatUpdate.Status.CLOSED_VOICE_CHAT |
            ChatUpdate.Status.DISCARDED_CALL |
            ChatUpdate.Status.BUSY_CALL
        )

        async def unified_update_handler(client, update: Update) -> None:
            try:
                if isinstance(update, ChatUpdate):
                    if update.status & ChatUpdate.Status.LEFT_CALL or update.status & CRITICAL_FLAGS:
                        await self.stop_stream(update.chat_id)
                        return

                elif isinstance(update, StreamEnded):
                    # Handle both audio and video stream ends
                    if update.stream_type in (StreamEnded.Type.AUDIO, StreamEnded.Type.VIDEO):
                        # Check if there are more items in queue
                        check = db.get(update.chat_id)
                        if not check or len(check) == 0:
                            # No more items in queue, leave the call
                            await self.stop_stream(update.chat_id)
                            return
                        else:
                            # Continue playing next item
                            await self.play(client, update.chat_id)

            except Exception as e:
                import sys, traceback
                from datetime import datetime

                exc_type, exc_obj, exc_tb = sys.exc_info()
                full_trace = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))
                caption = (
                    f"🚨 <b>Stream Update Error</b>\n"
                    f"📍 <b>Update Type:</b> <code>{type(update).__name__}</code>\n"
                    f"📍 <b>Error Type:</b> <code>{exc_type.__name__}</code>"
                )
                filename = f"update_error_{getattr(update, 'chat_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                await send_large_error(full_trace, caption, filename)

        for assistant in assistants:
            assistant.on_update()(unified_update_handler)

Space = Call()
