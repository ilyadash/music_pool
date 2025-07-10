import telebot as tb
import pygame as pg
import os
import random as rnd

VOLUME_INCRIMENT = 10
SONG_END = pg.USEREVENT + 1

# Initialize pygame mixer for playing music
pg.init()
pg.mixer.init()

def get_bot_token() -> str:
    return os.environ.get('BOT_TOKEN','')

class MusicPollBot (tb.TeleBot): # add code for wrapper class - to hold my additional data and methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_started = False # flag that bot is "turned on"
        self.state = '' # in what regime is bot right now
        self.playing = False
        self.music_directory = ''
        self.playlist = []
        self.current_file = ''
        self.current_track_number = 0
        self.current_volume = pg.mixer.music.get_volume() * 100
        self.shuffled_playlist = False
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
    def shuffle_playlist(self) -> None:
        self.shuffled_playlist = True
        rnd.shuffle(self.playlist)
    def file_is_ok(self, file) -> bool:
        is_ok = False
        if str(type(file)) == "<class 'str'>":
            if file.endswith(".mp3"): 
                is_ok = True
        return is_ok
    def play_all(self) -> None:
        self.current_track_number = 0
        if self.file_is_ok(self.playlist[self.current_track_number]):
            self.current_file = self.playlist[self.current_track_number]
            self.play()
            pg.mixer.music.queue(os.path.join(self.music_directory, self.playlist[min(self.current_track_number+1, len(self.playlist))]))
            self.current_track_number += 1
        while True:
            for event in pg.event.get():
                if event.type == SONG_END:
                    if self.file_is_ok(self.playlist[self.current_track_number]):
                        self.current_track_number += 1
                        self.current_file = self.playlist[self.current_track_number]
                        self.play()
                        pg.mixer.music.queue(os.path.join(self.music_directory, self.playlist[min(self.current_track_number+1, len(self.playlist))]))
    def play(self, file:str='') -> bool:
        self.playing = False
        if file == '':
            file = self.current_file
        if self.file_is_ok(file):
            self.current_track_number = self.playlist.index(file)
            self.playing = True 
            self.current_file = file  
            pg.mixer.music.load(os.path.join(self.music_directory, file))
            pg.mixer.music.play()
        return self.playing
    def pause(self) -> None:
        pg.mixer.music.pause()
        self.playing = False
    def stop(self) -> None:
        pg.mixer.music.stop()
        self.playing = False
    def next(self) -> None:
        self.current_track_number += 1
        self.current_file = self.playlist[self.current_track_number]
        self.play(self.current_file)
    def up(self) -> None:
        new_volume = min(100, self.current_volume + VOLUME_INCRIMENT)
        pg.mixer.music.set_volume(new_volume / 100.0)
        self.current_volume = pg.mixer.music.get_volume() * 100
    def down(self) -> None:
        new_volume = max(0, self.current_volume - VOLUME_INCRIMENT)
        pg.mixer.music.set_volume(new_volume / 100.0)
        self.current_volume = pg.mixer.music.get_volume() * 100
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
        
