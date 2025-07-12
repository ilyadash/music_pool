import telebot as tb
import pygame as pg
import os
import random as rnd
from tinytag import TinyTag
import time

SONG_END = pg.USEREVENT + 1

# Initialize pygame mixer for playing music
pg.init()
pg.mixer.init()

class MusicPollBot (tb.TeleBot): # add code for wrapper class - to hold my additional data and methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_started: bool = False # flag that bot is "turned on"
        self.state: str = '' # in what regime is bot right now
        self.playing: bool = False
        self.music_directory = ''
        self.ok_extensions: list[str] = ['.mp3', '.wav', '.ogg']
        self.playlist: list[str] = []
        self.current_file: str = ''
        self.current_track_number: int = -1
        self.current_volume = pg.mixer.music.get_volume() * 100 # in %
        self.shuffled_playlist: bool = False
        self.track_tags = None
        self.volume_increment = 10
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
        is_ok: bool = False
        if str(type(file)) == "<class 'str'>":
            name, extension = os.path.splitext(file)
            if extension in self.ok_extensions: 
                is_ok = True
        return is_ok
    def play_all(self, message_reply_to=None) -> None:
        self.current_track_number = 0
        if self.set_current_file(self.playlist[self.current_track_number]):
            if message_reply_to != None:
                self.reply_to(message_reply_to, f"Files in queue: {len(self.playlist)}")
            self.play(self.current_file, message_reply_to=message_reply_to)
            pg.mixer.music.queue(os.path.join(self.music_directory, self.playlist[min(self.current_track_number+1, len(self.playlist))]))
            self.current_track_number += 1
            self.continue_playing(message_reply_to)
    def continue_playing(self, message_reply_to=None): #TODO: Fix indefinite playing + ignoring commands while waiting for the end
        while True:
            for event in pg.event.get():
                if event.type == SONG_END:
                    if self.set_current_file(self.playlist[self.current_track_number+1]):
                        self.play(self.current_file, message_reply_to=message_reply_to)
                        pg.mixer.music.queue(os.path.join(self.music_directory, self.playlist[min(self.current_track_number+1, len(self.playlist))]))
    def load_file(self, file:str='', message_reply_to=None) -> bool:
        loaded_file = True
        if file == '':
            file = self.current_file
        try:
            pg.mixer.music.load(os.path.join(self.music_directory, file))
        except pg.error:
            if message_reply_to != None:
                self.reply_to(message_reply_to, f"Could not load the music file. Ensure the file {self.current_file} exists and is a valid format.")
            loaded_file = False
        return loaded_file
    def play(self, file:str='', message_reply_to=None) -> bool:
        self.playing = False
        if file == '':
            file = self.current_file
        if self.set_current_file(file):   
            if self.load_file(file, message_reply_to):
                pg.mixer.music.play()
                self.playing = True
            if message_reply_to != None:
                self.reply_to(message_reply_to, f"Now playing\n"+self.get_info_for_current_file())
        return self.playing
    def pause(self, message_reply_to=None) -> None:
        pg.mixer.music.pause()
        self.playing = False
        if message_reply_to != None:
            self.reply_to(message_reply_to, f"Paused: {self.current_file}")
    def stop(self, message_reply_to=None) -> None:
        pg.mixer.music.stop()
        self.playing = False
        if message_reply_to != None:
            self.reply_to(message_reply_to, f"Stopped playing music")
    def play_next(self, message_reply_to=None) -> None:
        self.current_track_number += 1
        if self.set_current_file(self.playlist[self.current_track_number]):
            self.play(self.current_file, message_reply_to)
        else:
            if message_reply_to != None:
                self.reply_to(message_reply_to, f"Skipped playing of "+self.playlist[self.current_track_number])
            self.play_next(message_reply_to)
        self.continue_playing(message_reply_to)
    def set_volume(self, volume) -> None: # TODO: Fix setting of new volume. Why are numbers not round? Do them round.
        pg.mixer.music.set_volume(volume / 100.0)
        self.current_volume = pg.mixer.music.get_volume() * 100
    def up(self) -> None:
        new_volume = int(min(100, self.current_volume + self.volume_increment))
        self.set_volume(new_volume)
    def down(self) -> None:
        new_volume = int(max(0, self.current_volume - self.volume_increment))
        self.set_volume(new_volume)
    def set_has_started(self, in_state: bool) -> None:
        self.has_started = in_state  
    def set_current_file(self, file) -> bool:
        if self.file_is_ok(file):
            self.current_file = file
            self.current_track_number = self.playlist.index(file)    
            self.track_tags = TinyTag.get(os.path.join(self.music_directory, file)) 
            return True
        return False
    def get_info_for_current_file(self) -> str:
        info: str = ''
        if self.track_tags != None:
            info = f"File name: {self.current_file}\nTitle: {self.track_tags.title}\nArtist: {self.track_tags.artist}\nAlbum: {self.track_tags.album}\nDuration: {time.strftime('%H:%M:%S', time.gmtime(self.track_tags.duration))}\n"
        return info
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
        
