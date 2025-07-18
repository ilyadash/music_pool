# Python Music Poll Bot
======================

## Overview

A Python-based bot for Telegram that holds music polls - listen to music yougathered with freands and learn new genres! 

Bot utilizes AsyncTeleBot and pydub modules to provide an interactive experience for users. 

### Bot features

- let you adjust bot options via environment variables: bot token, music directory, volume settings
- converts files from various formats to MP3
- plays local files from server where bot is running
- let you contol music playing: change sound volume, pause, unpause
- let you vote to skip the currently played track

## Usage

'Server' here is just a machine where your bot is running and where track to listen are downloaded. 
Required OS: Windows or Linux.

### Installation

*   Download bot files from this repositiry to yoor server, using `git clone` command
*   Install required packages using `pip` in your terminal/powershell:

```bash
pip install -r requirements.txt
```

### Prepare environment
*   Create your own Telegram bot via @BotFather
*   Rename file `template.env` to `.env`
*   Fill `.env` file with required variables for bot (API token is nessesary)

### To run
To run the Python Music Poll Bot, navigate to the project root directory and execute:

```bash
python src/music_poll_bot.py
```

Now you can interact with the bot by sending commands or messages into chat with the running bot.