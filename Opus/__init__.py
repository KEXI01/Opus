from Opus.core.bot import Space
from Opus.core.dir import dirr
from Opus.core.git import git
from Opus.core.userbot import Userbot
from Opus.misc import dbb, heroku
from Opus.logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Space()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
