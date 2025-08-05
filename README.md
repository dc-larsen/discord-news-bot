# Discord News Bot

A Discord bot that automatically summarizes daily news articles and discussions using OpenAI's GPT, running on GitHub Actions.

<img width="1246" height="1154" alt="image" src="https://github.com/user-attachments/assets/f702f078-a332-4629-8c82-2cbe113746d6" />


## Features

- 📰 Automatically processes Discord channel messages daily
- 🤖 Generates AI-powered summaries using OpenAI GPT-3.5-turbo
- 📅 Tracks processed messages to avoid duplicates
- ⚡ Runs on GitHub Actions with zero external infrastructure
- 💰 Cost-optimized with token limits and efficient prompting
- 🔒 Secure handling of Discord and OpenAI API keys

## Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token (you'll need this for `DISCORD_BOT_TOKEN`)
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent

### 2. Set Bot Permissions

In the "OAuth2" > "URL Generator" section:
1. Select "bot" scope
2. Select these bot permissions:
   - **Read Message History** (required to fetch past messages)
   - **Send Messages** (required to post summaries)
3. Use the generated URL to invite the bot to your Discord server

### 3. Get Channel ID

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on your target channel and select "Copy ID"
3. Save this ID for the `DISCORD_CHANNEL_ID` secret

### 4. Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `OPENAI_API_KEY`: Your OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- `DISCORD_CHANNEL_ID`: The Discord channel ID to monitor

### 5. Customize Schedule (Optional)

Edit `.github/workflows/daily-summary.yml` to change when the bot runs:

```yaml
schedule:
  # Run daily at 9:00 AM UTC
  - cron: '0 9 * * *'
```

## Local Development

### Prerequisites

- Python 3.12+
- Discord bot token
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd discord-news-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
export DISCORD_CHANNEL_ID="your_channel_id"
```

4. Run the bot:
```bash
python bot.py
```

## How It Works

1. **Message Fetching**: The bot reads messages from the specified Discord channel since the last run (or past 24 hours for first run)

2. **Deduplication**: Uses `state.json` to track processed message IDs, preventing duplicate summaries

3. **Content Preparation**: Combines message content with timestamps and author names, respecting token limits

4. **AI Summarization**: Sends content to OpenAI GPT-3.5-turbo with a focused prompt for news summarization

5. **Summary Posting**: Posts the generated summary back to the Discord channel with formatting

6. **State Management**: Updates `state.json` with the latest processed date and message IDs

## Configuration

### Environment Variables

- `DISCORD_BOT_TOKEN`: Discord bot authentication token (required)
- `OPENAI_API_KEY`: OpenAI API key for GPT access (required)  
- `DISCORD_CHANNEL_ID`: Target Discord channel ID (required)

### State Management

The bot maintains state in `state.json`:
- `last_processed_date`: ISO timestamp of last successful run
- `processed_message_ids`: List of recent message IDs to prevent duplicates

## Cost Optimization

- **Single API Call**: Combines all content into one OpenAI request
- **Token Limits**: Enforces `max_tokens=400` for responses
- **Content Truncation**: Limits input content to ~8000 characters
- **Efficient Model**: Uses GPT-3.5-turbo (cheaper than GPT-4)

## Troubleshooting

### Bot Not Responding
- Verify bot has correct permissions in Discord
- Check GitHub Actions logs for error messages
- Ensure all secrets are set correctly

### Missing Messages
- Confirm bot has "Read Message History" permission
- Check if `state.json` is being updated properly
- Verify channel ID is correct

### API Errors
- Verify OpenAI API key is valid and has credits
- Check Discord bot token hasn't expired
- Review GitHub Actions logs for specific error messages

### Local Testing
```bash
# Test with debug logging
python bot.py 2>&1 | tee bot.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details
