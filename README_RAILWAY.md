# Railway Deployment Guide

This guide will help you deploy the Bac-Bo Bot to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. A Telegram Bot Token (get it from @BotFather on Telegram)
3. A Telegram Channel ID (where the bot will send messages)

## Deployment Steps

### 1. Prepare Your Repository

Make sure you have these files in your repository:
- `bac_bo_bot_demo.py` - Main bot file (works in both GUI and headless mode)
- `requirements.txt` - Python dependencies
- `railway.json` - Railway configuration
- `Procfile` - Process file for Railway
- `runtime.txt` - Python version specification

### 2. Create a New Project on Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or upload your code)
4. Select your repository

### 3. Configure Environment Variables

In your Railway project, go to **Variables** tab and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
BOT_LANGUAGE=en
```

**Important:**
- `TELEGRAM_BOT_TOKEN`: Get this from @BotFather on Telegram
- `TELEGRAM_CHANNEL_ID`: Your Telegram channel ID (e.g., `@yourchannel` or numeric ID)
- `BOT_LANGUAGE`: Set to `en` for English or `pt` for Portuguese (default: `en`)

### 4. Deploy

1. Railway will automatically detect the Python project
2. It will install dependencies from `requirements.txt`
3. The bot will start automatically using `bac_bo_bot_demo.py` (detects headless mode automatically)

### 5. Monitor Your Deployment

- Check the **Deployments** tab to see build logs
- Check the **Logs** tab to see runtime logs
- The bot will start sending messages to your Telegram channel

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Your Telegram bot token | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `TELEGRAM_CHANNEL_ID` | Yes | Your Telegram channel ID | `@yourchannel` or `-1001234567890` |
| `BOT_LANGUAGE` | No | Bot language (`en` or `pt`) | `en` |

## Getting Your Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create a bot
4. Copy the token provided (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Getting Your Telegram Channel ID

### Method 1: Using @userinfobot
1. Add `@userinfobot` to your channel
2. It will show the channel ID

### Method 2: Using @getidsbot
1. Forward a message from your channel to `@getidsbot`
2. It will show the channel ID

### Method 3: Using Telegram Web
1. Open your channel in Telegram Web
2. Look at the URL: `https://web.telegram.org/k/#-1001234567890`
3. The number after `#` is your channel ID (include the `-` sign)

## Troubleshooting

### Bot not sending messages
- Check that `TELEGRAM_BOT_TOKEN` is correct
- Check that `TELEGRAM_CHANNEL_ID` is correct
- Make sure your bot is added to the channel as an administrator
- Check Railway logs for error messages

### Bot stops after first message
- Check Railway logs for errors
- Verify all environment variables are set correctly
- Make sure the bot has permission to send messages to the channel

### Build fails
- Check that `requirements.txt` is correct
- Verify Python version in `runtime.txt` is supported
- Check build logs in Railway dashboard

## Stopping the Bot

To stop the bot:
1. Go to Railway dashboard
2. Click on your service
3. Click "Settings"
4. Click "Delete" or pause the deployment

The bot will send a stop message before shutting down.

## Notes

- The bot runs continuously once deployed
- It will automatically restart if it crashes
- All data is simulated (random) for demo purposes
- The bot sends messages every 12 seconds after the initial setup sequence

