from telebot import TeleBot
import os
from telebot import types
from music_poll_bot import MusicPollBot
import sys

CURRENT_DIRECTORY: str = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, 'utils'))

import environment as env

bot = MusicPollBot(env.get_bot_token())
bot.music_directory = env.get_music_directory()
bot.playlist = env.get_music_playlist()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Send a message when the command /start is issued."""
    bot.reply_to(message, "Welcome! I can play music from your local directory. Use /play to start.")

@bot.message_handler(commands=['help'])
def send_help(message):
    """Send a message with available commands."""
    bot.reply_to(message, "/play - Start playing music\n/next - Go to the next track\n/up - Increase volume\n/down - Decrease volume")

@bot.message_handler(commands=['play'])
def play_music(message):
    """Play music from the local directory."""
    bot.shuffle_playlist()
    bot.play_all()
    bot.reply_to(message, f"Now playing: {bot.current_file}")
    #break

@bot.message_handler(commands=['pause'])
def pause_music(message):
    bot.pause()
    bot.reply_to(message, f"Paused: {bot.current_file}")

@bot.message_handler(commands=['next'])
def play_next_track(message):
    """Play the next track in the directory."""
    bot.next()        
    bot.reply_to(message, f"Now playing\n"+bot.get_info_for_current_file())

@bot.message_handler(commands=['up'])
def increase_volume(message):
    """Increase the volume."""
    bot.up()
    bot.reply_to(message, f"Volume increased to: {bot.current_volume}%")

@bot.message_handler(commands=['down'])
def decrease_volume(message):
    """Decrease the volume."""
    bot.down()
    bot.reply_to(message, f"Volume decreased to: {bot.current_volume}%")

# Run the bot using a loop (or use an event-driven method if you're in a non-blocking environment)
def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    remove_keyboard = types.ReplyKeyboardRemove()
    main()