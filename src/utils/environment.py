import os
from dotenv import load_dotenv

load_dotenv() # load local .env file with bot token

def get_bot_token() -> str:
    return os.environ.get('BOT_TOKEN','')

def get_music_directory() -> str:
    return os.environ.get('MUSIC_DIRECTORY','')

def get_music_playlist() -> list[str]:
    return os.listdir(get_music_directory())

def get_volume_increment() -> int:
    return int(os.environ.get('VOLUME_INCRIMENT', '10'))

def get_initial_volume() -> int:
    return int(os.environ.get('INITIAL_VOLUME', '50'))