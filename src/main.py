import asyncio
import os
from music_poll_bot import MusicPollBot
import sys

CURRENT_DIRECTORY: str = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, "utils"))

import environment as env

bot = MusicPollBot(env.get_bot_token())

#TODO: Move all bot initialization that makes sense to __init__ method
#TODO: Add "authors" who have sent tracks - separate playlists to different directories named by "authors/participants"
#TODO: Fix code on what to do after playlist ends - congratualte, state winner?
#TODO: Add statistics - what will be interesting for people in the end?
#TODO: Add buttons instead of commands
#TODO: Fill help with all the commands
#TODO: Add .env file template
#TODO: Add so every author is heard equally (more or less)
#TODO: Add playing from yandex music
#TODO: Add statistics functions (how many track were skipped, were listened till the end and how long were listening to music)
#TODO: Add sending playing track file/playing this file to everyone in the chat (is the second even possible)
#TODO: Add emojis to bot messages
#TODO: Update readme.md file into repository

@bot.message_handler(commands=["start"])
async def send_welcome(message):
    bot.set_volume(50)
    bot.number_of_listeners = await bot.get_chat_member_count(message.chat.id)
    await bot.convert_all_to_mp3(
        env.get_music_directory(), env.get_music_playlist(), message
    )
    await bot.set_playlist(env.get_music_playlist())
    await bot.reply_to(
        message,
        ("Welcome! I can play music from your local directory.\n"
         "Use /play to start or /help for help.\n"
         f"Sound volume - {int(bot.current_volume)}%.\n"
         f"Found {bot.number_of_participants} participants, "
         f"{bot.number_of_listeners} listeners, "
         f"{bot.number_of_administrators} administrators."
         ),
    )


@bot.message_handler(commands=["help"])
async def send_help(message):
    await bot.reply_to(
        message,
        "/play - Start playing music\n/next - Go to the next track\n/up - Increase volume\n/down - Decrease volume",
    )


@bot.message_handler(commands=["play"])
async def play_music(message):
    bot.shuffle_playlist()
    await bot.play_all(message)


@bot.message_handler(commands=["pause"])
async def pause_music(message):
    await bot.pause(message)


@bot.message_handler(commands=["unpause"])
async def unpause_music(message):
    await bot.unpause(message)


@bot.message_handler(commands=["next"])
async def play_next_track(message):
    await bot.play_next(message)


@bot.message_handler(commands=["up"])
async def increase_volume(message):
    bot.up()
    await bot.reply_to(message, f"Volume increased to: {bot.current_volume}%")


@bot.message_handler(commands=["down"])
async def decrease_volume(message):
    bot.down()
    await bot.reply_to(message, f"Volume decreased to: {bot.current_volume}%")


@bot.message_handler(commands=["stop"])
async def stop_play(message):
    await bot.stop(message)


@bot.message_handler(commands=["skip"])
async def skip(message):
    await bot.skip_track(message)


# Run the bot using a loop (or use an event-driven method if you're in a non-blocking environment)
async def main():
    await asyncio.gather(bot.infinity_polling(), bot.continue_playing())


if __name__ == "__main__":
    asyncio.run(main())
