# Timekeeper - Event Notification Service

Timekeeper is a standalone service that monitors your TaskMaster database and sends Telegram notifications when events are about to begin.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements_timekeeper.txt
```

### 2. Configure Telegram Chat IDs
Create a `telegram_chats.txt` file in the root directory with your Telegram chat IDs (one per line):
```
123456789
987654321
```

To find your chat ID:
1. Start a chat with your bot
2. Send `/start` command
3. The bot will respond with your chat ID

### 3. Environment Configuration
Ensure `.env.production` contains your Telegram bot token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Usage

### Start the Service
```bash
python timekeeper.py
```

### Stop the Service
Press `Ctrl+C` to stop gracefully.

## How It Works

1. **Database Monitoring**: Checks the SQLite database every minute
2. **Event Detection**: Finds events starting in the current minute
3. **Notification Sending**: Sends rich notifications to all configured chat IDs
4. **Read-Only**: Never modifies the database, only reads events

## Message Format

```
📅 **Event Starting Now:**

*Meeting with Client*

📍 Location: Conference Room A
⏱️ Duration: 1h 30m  
🏁 Ends at: 15:30
🏷️ Type: Meeting
```

## Features

- **Lightweight**: Minimal dependencies and resource usage
- **Reliable**: Uses proven scheduling patterns
- **Safe**: Read-only database access
- **Independent**: Runs separately from the main Flask application
- **Rich Notifications**: Includes all relevant event details

## Troubleshooting

### No Notifications Received
1. Check that `telegram_chats.txt` exists and contains valid chat IDs
2. Verify the bot token in `.env.production`
3. Ensure events have `notifications_enabled = 1` in the database
4. Check the console logs for error messages

### Service Won't Start
1. Verify all dependencies are installed: `pip install -r requirements_timekeeper.txt`
2. Check that the database file exists: `taskmaster.db`
3. Verify environment file exists: `.env.production`

## Logs

The service logs to both console and `timekeeper.log` file. Check the log file for detailed information about notifications sent and any errors encountered.