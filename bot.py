#!/usr/bin/env python3
"""
Discord News Bot - Daily Article Summarizer
Clean version without potential conflicts
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

import discord
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class NewsBot:
    def __init__(self):
        # Environment variables
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.channel_id = int(os.getenv('DISCORD_CHANNEL_ID', '0'))
        self.state_file = 'state.json'
        
        # Validate environment variables
        if not self.discord_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not self.channel_id:
            raise ValueError("DISCORD_CHANNEL_ID environment variable is required")
        
        # Initialize Discord client with comprehensive intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.guilds = True
        self.client = discord.Client(intents=intents)
        
        # Initialize OpenAI client - simplified
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        logger.info("NewsBot initialized successfully")

    def load_state(self) -> Dict:
        """Load processing state from JSON file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                logger.info(f"Loaded state: last_processed_date={state.get('last_processed_date')}")
                return state
        except FileNotFoundError:
            logger.info("No state file found, starting fresh")
            return {'last_processed_date': None, 'processed_message_ids': []}
        except json.JSONDecodeError as e:
            logger.error(f"Error reading state file: {e}")
            return {'last_processed_date': None, 'processed_message_ids': []}

    def save_state(self, state: Dict) -> None:
        """Save processing state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"State saved: last_processed_date={state.get('last_processed_date')}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def get_cutoff_time(self, state: Dict) -> datetime:
        """Determine cutoff time for message processing."""
        if state.get('last_processed_date'):
            try:
                return datetime.fromisoformat(state['last_processed_date'])
            except ValueError:
                logger.warning("Invalid date in state, using 24h ago")
        
        # Default to 24 hours ago
        return datetime.now(timezone.utc) - timedelta(hours=24)

    async def fetch_new_messages(self, channel: discord.TextChannel, cutoff_time: datetime, processed_ids: Set[int]) -> List[discord.Message]:
        """Fetch messages newer than cutoff time that haven't been processed."""
        messages = []
        
        try:
            logger.info(f"Searching for messages after {cutoff_time} in #{channel.name}")
            
            async for message in channel.history(after=cutoff_time, oldest_first=True):
                if message.id not in processed_ids and not message.author.bot:
                    messages.append(message)
                    logger.debug(f"Found message: {message.id} from {message.author} at {message.created_at}")
            
            logger.info(f"Fetched {len(messages)} new messages from #{channel.name}")
            
            # If no messages found, let's check if we can see ANY messages
            if len(messages) == 0:
                logger.info("No new messages found. Checking if bot can read channel history...")
                try:
                    recent_messages = []
                    async for msg in channel.history(limit=5):
                        recent_messages.append(f"{msg.author}: {msg.content[:50]}...")
                    
                    if recent_messages:
                        logger.info(f"Bot CAN read channel. Found {len(recent_messages)} recent messages:")
                        for msg in recent_messages:
                            logger.info(f"  - {msg}")
                        logger.info("This suggests no NEW messages since cutoff time")
                    else:
                        logger.warning("Bot cannot read ANY messages from channel - permission issue!")
                        
                except discord.Forbidden:
                    logger.error(f"PERMISSION DENIED: Bot cannot read message history in #{channel.name}")
                    
            return messages
        
        except discord.Forbidden:
            logger.error(f"PERMISSION DENIED: No permission to read messages in #{channel.name}")
            logger.error("Please check bot permissions: View Channel, Read Message History, Send Messages")
            return []
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def prepare_content_for_summary(self, messages: List[discord.Message]) -> str:
        """Prepare message content for OpenAI summarization."""
        if not messages:
            return ""
        
        content_parts = []
        for msg in messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M UTC")
            author = msg.author.display_name
            content = msg.content[:500]  # Limit message length
            
            if content.strip():
                content_parts.append(f"[{timestamp}] {author}: {content}")
        
        combined_content = "\n\n".join(content_parts)
        
        # Limit total content size
        if len(combined_content) > 8000:
            combined_content = combined_content[:8000] + "\n\n[Content truncated due to length...]"
        
        return combined_content

    async def generate_summary(self, content: str) -> Optional[str]:
        """Generate AI summary using OpenAI."""
        if not content.strip():
            return None
        
        prompt = f"""Please provide a concise summary of the following Discord messages. Focus on:
- Key news items, articles, or important discussions
- Main topics and themes
- Notable links or resources shared
- Keep it under 300 words

Messages:
{content}

Summary:"""

        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes Discord channel activity, focusing on news and important discussions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Successfully generated AI summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return None

    async def send_summary(self, channel: discord.TextChannel, summary: str, message_count: int, date_range: str) -> bool:
        """Send the summary to the Discord channel."""
        try:
            summary_message = f"""📰 **Daily News Summary** ({date_range})
*Processed {message_count} messages*

{summary}

---
*Generated by NewsBot • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"""

            await channel.send(summary_message)
            logger.info("Summary sent successfully")
            return True
            
        except discord.Forbidden:
            logger.error("No permission to send messages to channel")
            return False
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
            return False

    async def run_daily_summary(self) -> None:
        """Main function to run the daily summary process."""
        try:
            # Load state
            state = self.load_state()
            cutoff_time = self.get_cutoff_time(state)
            processed_ids = set(state.get('processed_message_ids', []))
            
            logger.info(f"Processing messages since: {cutoff_time}")
            
            # Get channel
            await self.client.wait_until_ready()
            channel = self.client.get_channel(self.channel_id)
            
            if not channel:
                logger.error(f"Could not find channel with ID: {self.channel_id}")
                return
            
            logger.info(f"Connected to channel: #{channel.name}")
            
            # Fetch new messages
            messages = await self.fetch_new_messages(channel, cutoff_time, processed_ids)
            
            if not messages:
                logger.info("No new messages to process")
                return
            
            # Prepare content and generate summary
            content = self.prepare_content_for_summary(messages)
            summary = await self.generate_summary(content)
            
            if not summary:
                logger.warning("Could not generate summary")
                return
            
            # Send summary
            date_range = f"{cutoff_time.strftime('%m/%d')} - {datetime.now(timezone.utc).strftime('%m/%d')}"
            success = await self.send_summary(channel, summary, len(messages), date_range)
            
            if success:
                # Update state
                new_processed_ids = processed_ids.union({msg.id for msg in messages})
                # Keep only recent IDs to prevent unbounded growth
                recent_ids = [id for id in new_processed_ids if id > (max(new_processed_ids) - 10000)]
                
                state = {
                    'last_processed_date': datetime.now(timezone.utc).isoformat(),
                    'processed_message_ids': recent_ids
                }
                self.save_state(state)
                logger.info("Daily summary completed successfully")
            
        except Exception as e:
            logger.error(f"Error in run_daily_summary: {e}")
            raise

async def main():
    """Main entry point."""
    try:
        bot = NewsBot()
        
        @bot.client.event
        async def on_ready():
            logger.info(f"Bot logged in as {bot.client.user}")
            await bot.run_daily_summary()
            await bot.client.close()
        
        await bot.client.start(bot.discord_token)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())