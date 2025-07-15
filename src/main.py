import asyncio
import os
from music_poll_bot import MusicPollBot
import sys

CURRENT_DIRECTORY: str = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, 'utils'))

import environment as env

bot = MusicPollBot(env.get_bot_token())

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    """Send a message when the command /start is issued."""
    await bot.reply_to(message, "Welcome! I can play music from your local directory. Use /play to start or /help for help.")

@bot.message_handler(commands=['help'])
async def send_help(message):
    """Send a message with available commands."""
    await bot.reply_to(message, "/play - Start playing music\n/next - Go to the next track\n/up - Increase volume\n/down - Decrease volume")

@bot.message_handler(commands=['play'])
async def play_music(message):
    """Play music from the local directory."""
    bot.shuffle_playlist()
    await bot.play_all(message)

@bot.message_handler(commands=['pause'])
async def pause_music(message):
    await bot.pause(message)
    
@bot.message_handler(commands=['unpause'])
async def unpause_music(message):
    await bot.unpause(message)    

@bot.message_handler(commands=['next'])
async def play_next_track(message):
    """Play the next track in the directory."""
    await bot.play_next(message)        

@bot.message_handler(commands=['up'])
async def increase_volume(message):
    """Increase the volume."""
    bot.up()
    await bot.reply_to(message, f"Volume increased to: {bot.current_volume}%")

@bot.message_handler(commands=['down'])
async def decrease_volume(message):
    """Decrease the volume."""
    bot.down()
    await bot.reply_to(message, f"Volume decreased to: {bot.current_volume}%")

@bot.message_handler(commands=['stop'])
async def stop_play(message):
    await bot.stop(message)
    
@bot.message_handler(commands=['sound'])
async def sound(message):
    await bot.sound(message)

# Run the bot using a loop (or use an event-driven method if you're in a non-blocking environment)
async def main():
    await asyncio.gather(bot.infinity_polling(), bot.continue_playing())

if __name__ == '__main__':
    bot.music_directory = env.get_music_directory()
    bot.convert_all_to_mp3(env.get_music_directory(), env.get_music_playlist())
    bot.set_playlist(env.get_music_playlist())
    bot.set_volume(50)
    bot.volume_increment = env.get_volume_increment()
    asyncio.run(main())