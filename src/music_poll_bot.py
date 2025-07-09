import telebot as tb
import os

MUSIC_DIRECTORY = 'D:\Music'

def get_bot_token() -> str:
    return os.environ.get('BOT_TOKEN','')

class MusicPollBot (tb.TeleBot): # add code for wrapper class - to hold my additional data and methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_started = False # flag that bot is "turned on"
        self.state = '' # in what regime is bot right now
        self.music_directory = ''
        self.play_list = []
        self.statistics = {
            "tracks": {
                "played": 0,
                "skipped": 0
            },
            "polls": {
                "started": 0,
                "passed": 0
            }
        }
    def set_has_started(self, in_state: bool) -> None:
        self.has_started = in_state    
    def clear_statistics(self):
        self.statistics = {
            "tracks": {
                "played": 0,
                "skipped": 0
            },
            "polls": {
                "started": 0,
                "passed": 0
            }
        }
        
