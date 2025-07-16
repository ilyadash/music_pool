import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import pygame as pg
import os
import random as rnd
from tinytag import TinyTag
import time
import sys

CURRENT_DIRECTORY: str = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, "utils"))

from convert import convert_to_mp3


class MusicPollBot(AsyncTeleBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Add poll methods
        # TODO: Add admin only methods
        pg.init()
        pg.mixer.init()
        self.state: str = ""  # in what regime is bot right now
        self.playing: bool = False
        self.music_directory = ""
        self.ok_to_convert_extensions: list[str] = [".m4a"]
        self.ok_to_play_extensions: list[str] = [".mp3", ".wav", ".ogg"]
        self.playlist: list[str] = []
        self.current_file: str = ""
        self.current_track_number: int = -1
        self.current_volume = pg.mixer.music.get_volume() * 100  # in %
        self.shuffled_playlist: bool = False
        self.track_tags = None
        self.volume_increment = 10
        self.start_playing: bool = False
        self.number_of_listeners: int = 0
        self.votes_to_skip: int = 0
        self.votes_threshold_relative: int = 0 # %
        self.votes_threshold_shift: int = 0
        self.message_reply_to = None
        self.statistics = {
            "tracks": {"played": 0, "skipped": 0},
            "polls": {"started": 0, "passed": 0},
        }

    def check_file_exists(self, full_path) -> bool:
        return os.path.exists(full_path) and os.path.isfile(full_path)

    def update_message_reply_to(self, message) -> None:
        if message is not None:
            self.message_reply_to = message
        
    async def my_reply_to(self, text:str = "") -> types.Message:
        if self.message_reply_to is not None:
            return await self.reply_to(self.message_reply_to, text)

    async def convert_to_mp3(self, dir, file, message_reply_to=None) -> bool:
        await convert_to_mp3(dir, file)
        if message_reply_to is not None:
            await self.reply_to(message_reply_to, f"Converted {file} to mp3")

    async def convert_all_to_mp3(
        self, dir: str = "", files: list[str] = [], message_reply_to=None
    ) -> None:
        files_to_convert: list[str] = []
        if message_reply_to is not None:
            await self.reply_to(
                message_reply_to,
                "Converting all files with unacceptable extensions to mp3",
            )

        if dir == "":
            dir = self.music_directory

        if len(files) == 0:
            files = self.playlist

        for file in files:
            name, extension = os.path.splitext(file)
            if extension in self.ok_to_convert_extensions:
                if not self.check_file_exists(dir + "\\" + name + ".mp3"):
                    files_to_convert.append(file)

        if message_reply_to is not None:
            if len(files_to_convert) == 0:
                await self.reply_to(message_reply_to, "All files are already in mp3!")
            else:
                await self.reply_to(
                    message_reply_to, "Wait before conversion is ended!"
                )

        if len(files_to_convert) > 0:
            conversion_tasks = [
                self.convert_to_mp3(dir, file_name, message_reply_to)
                for file_name in files_to_convert
            ]

            await asyncio.gather(*conversion_tasks, return_exceptions=False)

            if message_reply_to is not None:
                await self.reply_to(
                    message_reply_to,
                    f"Finished converting {len(files_to_convert)} files to mp3",
                )

    def shuffle_playlist(self) -> None:
        self.shuffled_playlist = True
        rnd.shuffle(self.playlist)

    def file_is_ok(self, file) -> bool:
        is_ok: bool = False
        if str(type(file)) == "<class 'str'>":
            name, extension = os.path.splitext(file)
            if extension in self.ok_to_play_extensions:
                is_ok = True
        return is_ok

    async def set_playlist(self, list_of_files: list[str] = []) -> None:
        if len(list_of_files) == 0:
            return
        for file in list_of_files:
            if not self.file_is_ok(file):
                list_of_files.remove(file)
        self.playlist = list_of_files

    async def play_all(self, message_reply_to=None) -> None:
        if message_reply_to is not None:
            await self.reply_to(
                message_reply_to, f"Files in queue: {len(self.playlist)}"
            )
            self.current_track_number = 0
            await self.play(message_reply_to=message_reply_to)

    async def continue_playing(self, message_reply_to=None) -> None:
        if self.start_playing:
            while True:
                if self.voted_to_skip():
                    self.clear_vote_to_skip()
                    await self.play_next(message_reply_to=message_reply_to)
                elif not pg.mixer.music.get_busy():
                    await self.play(message_reply_to=message_reply_to)

    def load_file(self, file: str = "", message_reply_to=None) -> bool:
        loaded_file = True
        if file == "":
            file = self.current_file
        try:
            pg.mixer.music.load(os.path.join(self.music_directory, file))
        except pg.error:
            if message_reply_to is not None:
                self.reply_to(
                    message_reply_to,
                    f"Could not load the music file. Ensure the file {self.current_file} exists and is a valid format.",
                )
            loaded_file = False
        return loaded_file

    async def play(self, file: str = "", message_reply_to=None) -> bool:
        self.playing = False
        if file == "":
            if self.file_is_ok(self.current_file):
                file = self.current_file
            else:
                file = self.playlist[self.current_track_number]
        if self.set_current_file(file):
            if self.load_file(file, message_reply_to):
                pg.mixer.music.play()
                self.playing = True
                if message_reply_to is not None:
                    await self.reply_to(
                        message_reply_to,
                        f"Now playing {self.current_track_number + 1}/{len(self.playlist)}\n"
                        + self.get_info_for_current_file(),
                    )
        elif message_reply_to is not None:
            await self.reply_to(
                message_reply_to,
                "Skipped playing of " + self.playlist[self.current_track_number],
            )
        return self.playing

    async def pause(self, message_reply_to=None) -> None:
        pg.mixer.music.pause()
        self.playing = False
        self.start_playing = False
        if message_reply_to is not None:
            await self.reply_to(message_reply_to, f"Paused: {self.current_file}")

    async def unpause(self, message_reply_to=None) -> None:
        pg.mixer.music.unpause()
        self.playing = True
        self.start_playing = True
        if message_reply_to is not None:
            await self.reply_to(message_reply_to, f"Unpaused: {self.current_file}")

    def stop(self, message_reply_to=None) -> None:
        pg.mixer.music.stop()
        self.playing = False
        self.start_playing = False
        if message_reply_to is not None:
            self.reply_to(message_reply_to, "Stopped playing music")

    async def play_next(self, message_reply_to=None) -> None:
        self.current_track_number += 1
        if self.set_current_file(self.playlist[self.current_track_number]):
            await self.play(self.current_file, message_reply_to)
        else:
            if message_reply_to is not None:
                await self.reply_to(
                    message_reply_to,
                    "Skipped playing of " + self.playlist[self.current_track_number],
                )

    def set_volume(self, volume) -> None:  
        # TODO: Fix setting of new volume. Why are numbers not round? Do them round.
        pg.mixer.music.set_volume(volume / 100.0)
        self.current_volume = pg.mixer.music.get_volume() * 100

    def up(self) -> None:
        new_volume = int(min(100, self.current_volume + self.volume_increment))
        self.set_volume(new_volume)

    def down(self) -> None:
        new_volume = int(max(0, self.current_volume - self.volume_increment))
        self.set_volume(new_volume)

    def set_current_file(self, file) -> bool:
        if self.file_is_ok(file):
            self.current_file = file
            self.current_track_number = self.playlist.index(file)
            self.track_tags = TinyTag.get(os.path.join(self.music_directory, file))
            return True
        return False

    def get_info_for_current_file(self) -> str:
        info: str = ""
        if self.track_tags is not None:
            info = f"File name: {self.current_file}\nTitle: {self.track_tags.title}\nArtist: {self.track_tags.artist}\nAlbum: {self.track_tags.album}\nDuration: {time.strftime('%H:%M:%S', time.gmtime(self.track_tags.duration))}\n"
        return info

    async def skip_track(self, message_reply_to=None):
        self.votes_to_skip += 1
        if message_reply_to is not None:
            await self.reply_to(
                message_reply_to, f"Accepted skip vote from user: @{message_reply_to.from_user.username}"
            )

    async def voted_to_skip(self):
        vote_result = ((self.votes_to_skip - self.votes_threshold_shift) / self.number_of_listeners) * 100 >= self.votes_threshold_relative
        if vote_result:
            await self.reply_to(
                self.message_reply_to, f"Skip has passed!\nVoted for skip: {self.votes_to_skip} / {self.number_of_listeners}\nNeeded to skip: {max(int(self.votes_threshold_relative/100*self.number_of_listeners) + self.votes_threshold_shift, 1)}"
            )        
        return vote_result
    def clear_vote_to_skip(self):
        self.votes_to_skip = 0

    def clear_statistics(self):
        self.statistics = {
            "tracks": {"played": 0, "skipped": 0},
            "polls": {"started": 0, "passed": 0},
        }
