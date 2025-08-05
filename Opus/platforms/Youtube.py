import asyncio
import os
import re
import json
from typing import Union, Tuple
import aiohttp
import random
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from Opus.utils.database import is_on_off
from Opus.utils.formatters import time_to_seconds

API_URL1 = "https://ashlynn-repo.vercel.app/cobolt"
API_URL2 = "https://narayan.sivendrastorm.workers.dev/arytmp3"

# Cache for yt-dlp metadata to avoid redundant calls
_metadata_cache = {}

def cookie_txt_file():
    cookie_dir = f"{os.getcwd()}/cookies"
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    return os.path.join(cookie_dir, random.choice(cookies_files)) if cookies_files else None

async def download_song(link: str, download_mode: str = "audio") -> str:
    video_id = link.split('v=')[-1].split('&')[0]
    download_folder = "downloads"
    file_extension = "mp3" if download_mode == "audio" else "mp4"
    file_path = os.path.join(download_folder, f"{video_id}.{file_extension}")

    if os.path.exists(file_path):
        return file_path

    os.makedirs(download_folder, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        # Try API 2 (direct link)
        try:
            song_url = f"{API_URL2}?direct&id={video_id}"
            async with session.get(song_url, timeout=20) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                    return file_path
        except Exception as e:
            print(f"[API 2 Error] {e}")

        # Fallback to API 1
        try:
            song_url = f"{API_URL1}?url=https://www.youtube.com/watch?v={video_id}&downloadMode={download_mode}"
            async with session.get(song_url, timeout=20) as response:
                if response.status != 200:
                    raise Exception(f"API 1 request failed with status {response.status}")
                data = await response.json()
                if data.get("status") != 200 or data.get("successful") != "success":
                    raise Exception(f"API 1 error: {data.get('message', 'Unknown error')}")
                download_url = data.get("data", {}).get("url")
                if not download_url:
                    raise Exception("API 1 missing download URL")
                async with session.get(download_url, timeout=20) as download_response:
                    if download_response.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await download_response.read())
                        return file_path
        except Exception as e:
            print(f"[API 1 Error] {e}")

    return None

async def check_file_size(link: str) -> float:
    video_id = link.split('v=')[-1].split('&')[0]
    if video_id in _metadata_cache:
        formats = _metadata_cache[video_id].get('formats', [])
    else:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookie_txt_file(), "-J", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[yt-dlp Error] {stderr.decode()}")
            return None
        _metadata_cache[video_id] = json.loads(stdout.decode())
        formats = _metadata_cache[video_id].get('formats', [])

    total_size = sum(f.get('filesize', 0) for f in formats if 'filesize' in f)
    return total_size / (1024 * 1024) if total_size else None  # Return size in MB

async def shell_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    return err.decode() if err else out.decode()

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be|music\.youtube\.com)"
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1, message_1.reply_to_message] if message_1.reply_to_message else [message_1]
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        return (message.text or message.caption)[entity.offset:entity.offset + entity.length]
            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None) -> Tuple[str, str, int, str, str]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=1).next()
        result = results["result"][0]
        title = result["title"]
        duration_min = result["duration"] or "0:00"
        duration_sec = int(time_to_seconds(duration_min)) if duration_min != "None" else 0
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=1).next()
        return results["result"][0]["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=1).next()
        return results["result"][0]["duration"] or "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=1).next()
        return results["result"][0]["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None) -> Tuple[int, str]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookie_txt_file(), "-g", "-f", "best[height<=?720][width<=?1280]", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, stderr.decode())

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Union[bool, str] = None) -> list:
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        cmd = f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
        playlist = await shell_cmd(cmd)
        return [x for x in playlist.split("\n") if x]

    async def track(self, link: str, videoid: Union[bool, str] = None) -> Tuple[dict, str]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=1).next()
        result = results["result"][0]
        track_details = {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"] or "0:00",
            "thumb": result["thumbnails"][0]["url"].split("?")[0]
        }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> Tuple[list, str]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        video_id = link.split('v=')[-1].split('&')[0]
        if video_id in _metadata_cache:
            r = _metadata_cache[video_id]
        else:
            ydl_opts = {"quiet": True, "cookiefile": cookie_txt_file()}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                r = ydl.extract_info(link, download=False)
            _metadata_cache[video_id] = r

        formats_available = [
            {
                "format": f["format"],
                "filesize": f.get("filesize"),
                "format_id": f["format_id"],
                "ext": f["ext"],
                "format_note": f.get("format_note"),
                "yturl": link
            } for f in r["formats"] if "format" in f and "dash" not in str(f["format"]).lower()
        ]
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None) -> Tuple[str, str, str, str]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = await VideosSearch(link, limit=10).next()
        result = results["result"][query_type]
        return result["title"], result["duration"] or "0:00", result["thumbnails"][0]["url"].split("?")[0], result["id"]

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Tuple[str, bool]:
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_running_loop()

        async def ytdl_download(ydl_opts: dict) -> str:
            video_id = link.split('v=')[-1].split('&')[0]
            fpath = f"downloads/{video_id}.%(ext)s" if not title else f"downloads/{title}.%(ext)s"
            ydl_opts["outtmpl"] = fpath
            ydl_opts["cookiefile"] = cookie_txt_file()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(xyz):
                    return xyz
                ydl.download([link])
            return xyz

        if songvideo or songaudio:
            download_mode = "video" if songvideo else "audio"
            downloaded_file = await download_song(link, download_mode)
            if downloaded_file:
                return downloaded_file, True

            # Fallback to yt-dlp
            ydl_opts = {
                "format": f"{format_id}+140" if songvideo else format_id,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4" if songvideo else None,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }] if songaudio else []
            }
            downloaded_file = await loop.run_in_executor(None, lambda: ytdl_download(ydl_opts))
            return downloaded_file, True

        elif video:
            if await is_on_off(1):
                downloaded_file = await download_song(link, "video")
                if downloaded_file:
                    return downloaded_file, True

            total_size_mb = await check_file_size(link)
            if not total_size_mb or total_size_mb > 250:
                print(f"File size {total_size_mb:.2f} MB exceeds 250MB limit or is unavailable.")
                return None, False

            ydl_opts = {
                "format": "best[height<=?720][width<=?1280]+bestaudio[ext=m4a]",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4"
            }
            downloaded_file = await loop.run_in_executor(None, lambda: ytdl_download(ydl_opts))
            return downloaded_file, True

        else:
            downloaded_file = await download_song(link, "audio")
            if downloaded_file:
                return downloaded_file, True

            ydl_opts = {
                "format": "bestaudio/best",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }
            downloaded_file = await loop.run_in_executor(None, lambda: ytdl_download(ydl_opts))
            return downloaded_file, True
