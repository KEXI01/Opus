import asyncio
import aiohttp
import aiofiles
import os
import re
from typing import Optional, Dict
from yt_dlp import YoutubeDL
from config import API_URL

cookies_file = "Opus/assets/cookies.txt"
download_folder = "downloads"
os.makedirs(download_folder, exist_ok=True)


def extract_video_id(link: str) -> str:
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return link.split("/")[-1].split("?")[0]


def safe_filename(name: str) -> str:
    return re.sub(r"[\\/*?\"<>|]", "_", name).strip()[:100]


def file_exists(video_id: str) -> Optional[str]:
    for ext in ["mp3", "mp4"]:
        path = f"{download_folder}/{video_id}.{ext}"
        if os.path.exists(path):
            print(f"[CACHED] Using existing file: {path}")
            return path
    return None


async def api_download_song(link: str) -> Optional[str]:
    video_id = extract_video_id(link)
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"{API_URL}?url=https://youtube.com/watch?v={video_id}&format=mp3&audioBitrate=320"
            async with session.get(api_url) as response:
                if response.status != 200:
                    print(f"[API ERROR] Status {response.status}")
                    return None

                data = await response.json()
                if data.get("status") != 200 or data.get("successful") != "success":
                    print(f"[API ERROR] Invalid response status: {data.get('status')}")
                    return None

                audio_url = data["data"]["download"]["url"]
                filename = safe_filename(data["data"]["download"]["filename"]).replace(".webm", ".mp3")
                path = f"{download_folder}/{filename}"

                async with session.get(audio_url) as file_response:
                    if file_response.status != 200:
                        print(f"[API Download Error] File download failed with status {file_response.status}")
                        return None
                    content = await file_response.read()
                    async with aiofiles.open(path, "wb") as f:
                        await f.write(content)

                return path
    except Exception as e:
        print(f"[API Download Error] {e}")
        return None


def _download_ytdlp(link: str, opts: Dict) -> Optional[str]:
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=False)
            vid = info.get("id")
            ext = opts["postprocessors"][0]["preferredcodec"] if "postprocessors" in opts else "mp4"
            filename = f"{download_folder}/{vid}.{ext}"
            if os.path.exists(filename):
                return filename
            ydl.download([link])
            return filename
    except Exception as e:
        print(f"[yt-dlp Error] {e}")
        return None


async def yt_dlp_download(link: str, type: str, format_id: str = None, title: str = None) -> Optional[str]:
    loop = asyncio.get_running_loop()

    def is_restricted() -> bool:
        return os.path.exists(cookies_file)

    common_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "geo_bypass_country": "IN",
        "concurrent_fragment_downloads": 5,
    }

    if type == "audio":
        opts = {
            **common_opts,
            "format": "bestaudio/best",
            "cookiefile": cookies_file if is_restricted() else None,
            "outtmpl": f"{download_folder}/%(id)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        return await loop.run_in_executor(None, _download_ytdlp, link, opts)

    elif type == "video":
        opts = {
            **common_opts,
            "format": "bestvideo[height<=720]+bestaudio/best",
            "cookiefile": cookies_file if is_restricted() else None,
            "outtmpl": f"{download_folder}/%(id)s.mp4",
            "merge_output_format": "mp4",
            "prefer_ffmpeg": True,
        }
        return await loop.run_in_executor(None, _download_ytdlp, link, opts)

    return None


async def download_audio_concurrent(link: str) -> Optional[str]:
    video_id = extract_video_id(link)

    existing = file_exists(video_id)
    if existing:
        return existing

    # Try API first
    api_result = await api_download_song(link)
    if api_result:
        print(f"[SUCCESS] Downloaded via API: {api_result}")
        return api_result

    # Fallback to yt-dlp
    yt_result = await yt_dlp_download(link, type="audio")
    if yt_result:
        print(f"[SUCCESS] Downloaded via yt-dlp: {yt_result}")
        return yt_result

    print(f"[ERROR] Failed to download audio from {link}")
    return None
