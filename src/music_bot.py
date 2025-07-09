from telebot import TeleBot
import pygame
import os
from telebot import types
from telebot.util import quick_markup
from dotenv import load_dotenv

API_TOKEN = ''
MUSIC_DIRECTORY = 'D:\Music'

load_dotenv() # load local .env file with bot token

def get_bot_token() -> str:
    return os.environ.get('BOT_TOKEN','')

# Initialize the bot
API_TOKEN = get_bot_token()
bot = TeleBot(API_TOKEN)

# Initialize pygame mixer for playing music
pygame.init()
pygame.mixer.init()

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
    current_dir = os.getcwd()
    song_dir = MUSIC_DIRECTORY  # Update this path as per your system
    for file in os.listdir(song_dir):
        if file.endswith(".mp3"):
            pygame.mixer.music.load(os.path.join(song_dir, file))
            pygame.mixer.music.play()
            bot.reply_to(message, f"Now playing: {file}")
            break

@bot.message_handler(commands=['next'])
def play_next_track(message):
    """Play the next track in the directory."""
    current_dir = os.getcwd()
    song_dir = MUSIC_DIRECTORY  # Update this path as per your system
    for file in os.listdir(song_dir):
        if file.endswith(".mp3"):
            pygame.mixer.music.load(os.path.join(song_dir, file))
            pygame.mixer.music.play()
            bot.reply_to(message, f"Now playing: {file}")
            break

@bot.message_handler(commands=['up'])
def increase_volume(message):
    """Increase the volume."""
    current_volume = pygame.mixer.get_volume() * 100
    new_volume = min(100, current_volume + 10)
    pygame.mixer.music.set_volume(new_volume / 100.0)
    bot.reply_to(message, f"Volume increased to: {new_volume}%")

@bot.message_handler(commands=['down'])
def decrease_volume(message):
    """Decrease the volume."""
    current_volume = pygame.mixer.get_volume() * 100
    new_volume = max(0, current_volume - 10)
    pygame.mixer.music.set_volume(new_volume / 100.0)
    bot.reply_to(message, f"Volume decreased to: {new_volume}%")

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