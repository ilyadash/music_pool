import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import pygame as pg
import os
import random as rnd
from tinytag import TinyTag
import time
import itertools
import copy
from utils import environment as env
from utils.convert import convert_to_mp3
from telebot.apihelper import ApiTelegramException


class MusicPollBot(AsyncTeleBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Add admin only methods
        pg.init()
        pg.mixer.init()
        self.state: str = ""  # in what regime is bot right now
        self.playing: bool = False
        self.music_main_directory: str = env.get_main_music_directory()
        self.music_folders: list[str]  = env.get_music_folders(self.music_main_directory)
        self.cycler_of_participants = itertools.cycle(self.music_folders)
        self.ok_to_convert_extensions: list[str] = [".m4a"]
        self.ok_to_play_extensions: list[str] = [".mp3", ".wav", ".ogg"]
        self.playlist: dict[str:list[tuple(str), int]] = dict.fromkeys(self.music_folders, [(), -1])
        self.all_files_number = 0
        self.current_folder: str = self.music_folders[0]
        self.current_file: str = ""
        self.current_track_number: int = -1
        self.current_volume = pg.mixer.music.get_volume() * 100  # in %
        self.shuffled_playlist: bool = False
        self.track_tags = None
        self.volume_increment = env.get_volume_increment()
        self.start_playing: bool = False
        self.number_of_participants: int = len(self.music_folders)
        self.number_of_listeners: int = 0
        self.number_of_administrators: int = 0
        self.votes_to_skip: int = 0
        self.votes_threshold_relative: int = env.get_vote_threshold_relative() # in %
        self.votes_threshold_shift: int = env.get_vote_threshold_shift() # in votes
        self.message_reply_to: types.Message = None
        self.last_playing_message = None
        self.statistics = {
            "tracks": {"played": 0, "skipped": 0},
            "polls": {"started": 0, "passed": 0},
            "time_listening": 0
        }

    def check_file_exists(self, full_path) -> bool:
        return os.path.exists(full_path) and os.path.isfile(full_path)
    
    def check_mp3_of_file_exists(self, full_path) -> bool:
        path, extension = os.path.splitext(full_path)
        return self.check_file_exists(path+".mp3")

    def update_playlist(self, new_playlist=None) -> None:
        if new_playlist is not None: # TODO: Fix referencing of keys to the same values
            self.playlist = new_playlist
        else:
            initial_playlist_data = [tuple([]), -1]
            for participant in self.playlist.keys():
                self.playlist[participant][0] = copy.deepcopy([])
                self.playlist[participant][1] = -1
            for participant in self.playlist.keys():
                buffer_playlist = []
                full_dir_path = os.path.join(self.music_main_directory, participant)
                for file_name in env.get_raw_music_playlist(full_dir_path):
                    full_file_path = os.path.join(full_dir_path, file_name)
                    if self.check_file_exists(full_file_path) and file_name not in self.playlist[participant][0]:
                        if self.file_is_ok_to_play(file_name):
                            buffer_playlist.append(file_name)
                        elif self.file_is_ok_to_convert(file_name):
                            name, extension = os.path.splitext(file_name)
                            if self.check_mp3_of_file_exists(full_file_path):
                                buffer_playlist.append(name+".mp3")
                self.playlist[participant][0] = tuple(copy.deepcopy(buffer_playlist))
        return
    
    def update_message_reply_to(self, message:types.Message) -> None:
        if message is not None:
            self.message_reply_to = message

    def get_current_participant(self) -> str:
        return self.current_folder
    
    def get_next_participant(self) -> str:
        return next(self.cycler_of_participants)
    
    def set_current_participant(self, participant:str = "") -> None:
        self.current_folder = participant
        return 
    
    def get_current_playlist(self):
        return self.playlist[self.get_current_participant()][0]

    def get_current_track_number(self) -> int:
        return self.playlist[self.get_current_participant()][1]
    
    def set_current_track_number(self, number: int):
        self.playlist[self.get_current_participant()][1] = number

    def get_current_track(self) -> int:
        return self.get_current_playlist()[self.get_current_track_number()]

    def get_current_music_dir(self) -> str:
        return os.path.join(self.music_main_directory, self.current_folder)
    
    def get_number_of_all_files(self) -> int:
        return sum([len(self.playlist[folder][0]) for folder in self.playlist])

    async def reply_message_with_retry(self, text, max_retries=3, initial_delay=5):
        for attempt in range(max_retries):
            try:
                msg_sent = await self.reply_to(self.message_reply_to, text)
                print(f"Message sent successfully on attempt {attempt + 1}")
                return msg_sent
            except ApiTelegramException as e:
                if "Too Many Requests" in str(e): # Example for rate limiting
                    print(f"Rate limit hit. Retrying in {initial_delay} seconds...")
                    await asyncio.sleep(initial_delay)
                    initial_delay *= 2 # Exponential backoff
                else:
                    print(f"Telegram API error: {e}. Retrying in {initial_delay} seconds...")
                    await asyncio.sleep(initial_delay)
                    initial_delay *= 2
            except Exception as e: # Catch other potential network errors
                print(f"An unexpected error occurred: {e}. Retrying in {initial_delay} seconds...")
                await asyncio.sleep(initial_delay)
                initial_delay *= 2
        print(f"Failed to send message after {max_retries} attempts.")

    async def my_reply_to(self, text:str = ""):
        if self.message_reply_to is not None:
            return await self.reply_message_with_retry(text)

    async def convert_to_mp3(self, dir:str = "", file:str = "", message_reply_to:types.Message=None):
        if dir == "":
            dir = self.get_current_music_dir()
        if file == "":  
            file = self.current_file
        await asyncio.sleep(1)
        await convert_to_mp3(dir, file)
        self.update_message_reply_to(message_reply_to)
        await self.my_reply_to(f"Converted file\n{file}\nto mp3")

    async def convert_all_to_mp3(
        self, message_reply_to:types.Message=None
    ) -> None:
        #TODO: Fix function to work for several subfolders/participants
        files_to_convert: list[str] = []
        if message_reply_to is not None:
            self.update_message_reply_to(message_reply_to)
            await self.reply_to(
                message_reply_to,
                "Converting all files with unacceptable extensions to mp3",
            )

        conversion_tasks = []

        for dir in self.music_folders:
            files = env.get_files_list_in_dir(os.path.join(self.music_main_directory, dir))
            files_to_convert = []
            for file in files:
                name, extension = os.path.splitext(file)
                if extension in self.ok_to_convert_extensions:
                    if not self.check_file_exists(os.path.join(self.music_main_directory, dir, name + ".mp3")):
                        files_to_convert.append(file)

            if message_reply_to is not None:
                self.update_message_reply_to(message_reply_to)
                if len(files_to_convert) == 0:
                    await self.my_reply_to(f"All files in folder {dir} are already in mp3!")
            
            for file_name in files_to_convert:
                conversion_tasks.append(self.convert_to_mp3(os.path.join(self.music_main_directory, dir), file_name)) # removed message to reply to to avoid flooding of Telegram API. Too many messages reporting about each converted file.

        if len(conversion_tasks) > 0:
            await self.reply_to(
                message_reply_to, f"{len(conversion_tasks)} files will be converted into mp3. Wait until conversion is ended!"
            )
            await asyncio.gather(*conversion_tasks, return_exceptions=False)

            if message_reply_to is not None:
                self.update_message_reply_to(message_reply_to)
                await self.reply_to(
                    message_reply_to,
                    f"Finished converting {len(conversion_tasks)} files to mp3",
                )

    def file_is_ok_to_play(self, file) -> bool:
        if str(type(file)) == "<class 'str'>":
            name, extension = os.path.splitext(file)
            if extension in self.ok_to_play_extensions:
                return True
        return False
    
    def file_is_ok_to_convert(self, file) -> bool:
        is_ok: bool = False
        if str(type(file)) == "<class 'str'>":
            name, extension = os.path.splitext(file)
            if extension in self.ok_to_convert_extensions:
                is_ok = True
        return is_ok

    #Start "anew" - play all files possible
    async def play_all(self, message_reply_to:types.Message=None, shuffle:bool=False) -> None:
        self.set_current_participant(self.music_folders[0]) 
        self.set_current_track_number(0)
        if self.set_current_file(self.get_current_track()):
            if message_reply_to is not None:
                self.update_message_reply_to(message_reply_to)
                await self.reply_to(
                    message_reply_to, f"Files in queue: {self.get_number_of_all_files()}"
                )
            await self.play(message_reply_to=message_reply_to)

    #Always playing loop for music stop only if specifaclly asked:
    async def continue_playing(self, message_reply_to:types.Message=None) -> bool:
        while True:
            if self.start_playing:
                skip = await self.voted_to_skip()
                if skip:
                    self.clear_vote_to_skip()
                    await self.play_next(message_reply_to=message_reply_to)
                elif not pg.mixer.music.get_busy():
                    await self.play_next(message_reply_to=message_reply_to)
            await asyncio.sleep(0.1) # Sleep shortly to yield control to event loop (prevent CPU lockup)
    
    async def load_file(self, message_reply_to:types.Message=None) -> bool:
        try:
            pg.mixer.music.load(os.path.join(self.music_main_directory, self.current_folder, self.current_file))
        except pg.error:
            if message_reply_to is not None:
                self.update_message_reply_to(message_reply_to)
                await self.reply_to(
                    message_reply_to,
                    ("Could not load the music file. Ensure the file"
                     f"{self.current_file} exists and is a valid format.")
                )
            return False
        return  True

    async def play(self, message_reply_to:types.Message=None) -> bool:
        self.playing = False
        loaded_file = await self.load_file(message_reply_to)
        if loaded_file:
            pg.mixer.music.play()
            self.playing = True
            self.start_playing = True
            self.update_message_reply_to(message_reply_to)
            self.statistics["tracks"]["played"] += 1
            if self.message_reply_to is not None:
                self.last_playing_message = await self.reply_to(
                    self.message_reply_to,
                    f"Now playing {self.current_track_number + 1}/{len(self.playlist[self.get_current_participant][0])}\n"
                    + self.get_info_for_current_file(),
                )
        return self.playing

    async def pause(self, message_reply_to:types.Message=None) -> None:
        pg.mixer.music.pause()
        self.playing = False
        self.start_playing = False
        if message_reply_to is not None:
            self.update_message_reply_to(message_reply_to)
            await self.reply_to(message_reply_to, f"Paused: {self.current_file}")

    async def unpause(self, message_reply_to:types.Message=None) -> None:
        pg.mixer.music.unpause()
        self.playing = True
        self.start_playing = True
        if message_reply_to is not None:
            self.update_message_reply_to(message_reply_to)
            await self.reply_to(message_reply_to, f"Unpaused: {self.current_file}")

    async def stop(self, message_reply_to:types.Message=None) -> None:
        pg.mixer.music.stop()
        self.playing = False
        self.start_playing = False
        if message_reply_to is not None:
            self.update_message_reply_to(message_reply_to)
            await self.reply_to(message_reply_to, "Stopped playing music")

    async def play_next(self, message_reply_to:types.Message=None) -> None:
        self.set_current_track_number(self.get_current_track_number() + 1)
        self.set_current_participant(self.get_next_participant())
        if self.set_current_file(self.get_current_track()):
            await self.play(message_reply_to=message_reply_to)
        else:
            if message_reply_to is not None:
                self.update_message_reply_to(message_reply_to)
                await self.reply_to(
                    message_reply_to,
                    "Skipped playing of " + self.playlist[self.current_track_number],
                )

    def set_volume(self, volume) -> None:  
        # TODO: Fix setting of new volume. Why are numbers not round? Do them round. (do not know how)
        pg.mixer.music.set_volume(volume / 100.0)
        self.current_volume = pg.mixer.music.get_volume() * 100

    def up(self) -> None:
        new_volume = int(min(100, self.current_volume + self.volume_increment))
        self.set_volume(new_volume)

    def down(self) -> None:
        new_volume = int(max(0, self.current_volume - self.volume_increment))
        self.set_volume(new_volume)

    def set_current_file(self, file) -> bool:
        if self.file_is_ok_to_play(file):
            self.current_file = file
            self.current_track_number = self.get_current_track_number()
            self.track_tags = TinyTag.get(os.path.join(self.music_main_directory, self.current_folder, file))
            return True
        return False

    def get_info_for_current_file(self) -> str:
        info: str = ""
        if self.track_tags is not None:
            info = (f"Participant: {self.get_current_participant()}\n"
                    f"File name: {self.current_file}\n"
                    f"Title: {self.track_tags.title}\n"
                    f"Artist: {self.track_tags.artist}\n"
                    f"Album: {self.track_tags.album}\n"
                    f"Duration: {time.strftime('%H:%M:%S', time.gmtime(self.track_tags.duration))}\n")
        return info

    async def skip_track(self, message_reply_to:types.Message=None):
        self.votes_to_skip += 1
        if self.votes_to_skip == 1:
            self.statistics["polls"]["started"] += 1
        if message_reply_to is not None:
            await self.reply_to(
                message_reply_to, f"Accepted skip vote from user: @{message_reply_to.from_user.username}"
            )

    async def voted_to_skip(self): # TODO: Fix long pause after 'skip' command results
        vote_result = ((self.votes_to_skip - self.votes_threshold_shift) / self.number_of_listeners) * 100 >= self.votes_threshold_relative
        if vote_result:
            self.statistics["polls"]["passed"] += 1
            self.statistics["tracks"]["skipped"] += 1
            await self.reply_to(
                self.last_playing_message, f"Skip has passed!\nVoted for skip: {self.votes_to_skip} / {self.number_of_listeners}\nNeeded to skip: {max(int(self.votes_threshold_relative/100*self.number_of_listeners) + self.votes_threshold_shift, 1)}"
            )
        return vote_result

    def clear_vote_to_skip(self):
        self.votes_to_skip = 0

    def clear_statistics(self):
        self.statistics = {
            "tracks": {"played": 0, "skipped": 0},
            "polls": {"started": 0, "passed": 0},
        }
