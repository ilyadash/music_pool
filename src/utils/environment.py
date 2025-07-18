import os
from dotenv import load_dotenv

load_dotenv() # load local .env file with bot token

def get_bot_token() -> str:
    return os.environ.get('BOT_TOKEN','')

def get_main_music_directory() -> str:
    return os.environ.get('MUSIC_DIRECTORY','')

def get_raw_music_playlist(files_directory:str=None) -> list[str]:
    if files_directory is None:
        files_directory = get_main_music_directory()
    return os.listdir(files_directory)

def get_volume_increment() -> int:
    return int(os.environ.get('VOLUME_INCRIMENT', '10'))

def get_initial_volume() -> int:
    return int(os.environ.get('INITIAL_VOLUME', '50'))

def check_file_exists(full_path:str) -> bool:
    return os.path.exists(full_path) and os.path.isfile(full_path)

def get_vote_threshold_relative() -> int:
    return int(os.environ.get('VOTE_RELATIVE_THRESHOLD', '50'))

def get_vote_threshold_shift() -> int:
    return int(os.environ.get('VOTE_THRESHOLD_SHIFT', '0'))