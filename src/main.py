import asyncio
import os
from music_poll_bot import MusicPollBot
import sys

CURRENT_DIRECTORY: str = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, "utils"))

import environment as env

bot = MusicPollBot(env.get_bot_token())


@bot.message_handler(commands=["start"]) # TODO: Fix long pause after 'start' command
async def send_welcome(message):
    bot.music_directory = env.get_music_directory()
    bot.set_volume(50)
    bot.volume_increment = env.get_volume_increment()
    bot.votes_threshold_relative = env.get_vote_threshold_relative()
    bot.votes_threshold_shift = env.get_vote_threshold_shift()
    bot.number_of_listeners = await bot.get_chat_member_count(message.chat.id)
    await bot.convert_all_to_mp3(
        env.get_music_directory(), env.get_music_playlist(), message
    )
    await bot.set_playlist(env.get_music_playlist())
    await bot.reply_to(
        message,
        f"Welcome! I can play music from your local directory.\nUse /play to start or /help for help.\nSound volume - {int(bot.current_volume)}%.\nFound {bot.number_of_listeners} listeners.",
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
