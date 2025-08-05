#!/usr/bin/env python3
"""
Discord News Bot - Daily Article Summarizer
Clean version without potential conflicts
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

import discord
import httpx
import openai
from bs4 import BeautifulSoup

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
        
        # Initialize HTTP client for web fetching
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Discord News Bot)"}
        )
        
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
                # Include all messages except from this bot itself
                if message.id not in processed_ids and message.author.id != self.client.user.id:
                    messages.append(message)
                    logger.debug(f"Found message: {message.id} from {message.author} at {message.created_at}")
            
            logger.info(f"Fetched {len(messages)} new messages from #{channel.name}")
            
            # If no messages found, let's check if we can see ANY messages
            if len(messages) == 0:
                logger.info("No new messages found. Checking if bot can read channel history...")
                try:
                    recent_messages = []
                    async for msg in channel.history(limit=5):
                        bot_indicator = " [BOT]" if msg.author.bot else ""
                        recent_messages.append(f"{msg.author}{bot_indicator}: {msg.content[:50]}...")
                    
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

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text content."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.[^\s<>"{}|\\^`\[\]]+)*'
        urls = re.findall(url_pattern, text)
        logger.debug(f"Extracted {len(urls)} URLs from text: {urls}")
        return urls

    async def fetch_web_content(self, url: str) -> Optional[str]:
        """Fetch and extract text content from a web page."""
        try:
            logger.info(f"Fetching content from: {url}")
            response = await self.http_client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = ' '.join(line for line in lines if line)
            
            # Limit content size for OpenAI
            if len(text) > 8000:
                text = text[:8000] + "... [Content truncated]"
            
            logger.info(f"Successfully fetched {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None

    async def prepare_content_for_summary(self, messages: List[discord.Message]) -> str:
        """Prepare message content for OpenAI summarization by extracting and fetching URLs."""
        if not messages:
            logger.warning("prepare_content_for_summary called with no messages")
            return ""
        
        logger.info(f"Preparing content from {len(messages)} messages")
        content_parts = []
        
        for i, msg in enumerate(messages):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M UTC")
            author = msg.author.display_name
            
            logger.info(f"Message {i+1}: {timestamp} {author} - Content length: {len(msg.content)}, Embeds: {len(msg.embeds)}")
            if len(msg.content) > 0:
                logger.info(f"  Content preview: {msg.content[:100]}...")
            else:
                logger.info("  Content is empty")
            
            # Log embed info for debugging
            for j, embed in enumerate(msg.embeds):
                logger.info(f"  Embed {j+1}: URL={embed.url}, Title={embed.title[:50] if embed.title else None}")
            
            # Extract URLs from the message content
            urls = self.extract_urls(msg.content)
            
            # Also check embeds for URLs
            for embed in msg.embeds:
                if embed.url:
                    urls.append(embed.url)
                if embed.description:
                    urls.extend(self.extract_urls(embed.description))
                if embed.title:
                    urls.extend(self.extract_urls(embed.title))
            
            # Remove duplicates
            urls = list(set(urls))
            
            if urls:
                logger.info(f"Found {len(urls)} URLs in message {i+1}: {urls}")
                for url in urls:
                    web_content = await self.fetch_web_content(url)
                    if web_content:
                        # Extract article title from URL or content for better organization
                        article_title = "News Article"
                        if "wowhead.com" in url:
                            # Try to extract title from URL path
                            url_parts = url.split('/')
                            for part in url_parts:
                                if part and '-' in part and not part.startswith('news') and 'utm_source' not in part:
                                    article_title = part.replace('-', ' ').title()
                                    break
                        
                        content_parts.append(f"""─── {article_title} ───
SOURCE URL: {url}
TIMESTAMP: {timestamp}
AUTHOR: {author}

CONTENT:
{web_content}

""")
                    else:
                        content_parts.append(f"[{timestamp}] {author} shared: {url}\n\n[Could not fetch content]")
            elif msg.content.strip():
                # Fallback to original message content if no URLs
                content = msg.content[:500]  # Limit message length
                content_parts.append(f"[{timestamp}] {author}: {content}")
            else:
                logger.info(f"  Skipping message {i+1} - no content or URLs found in message or embeds")
        
        logger.info(f"Valid content parts: {len(content_parts)} out of {len(messages)} messages")
        combined_content = "\n\n".join(content_parts)
        
        # Limit total content size
        if len(combined_content) > 12000:  # Increased limit since we're now fetching article content
            combined_content = combined_content[:12000] + "\n\n[Content truncated due to length...]"
        
        logger.info(f"Final combined content length: {len(combined_content)}")
        return combined_content

    async def generate_summary(self, content: str) -> Optional[str]:
        """Generate AI summary using OpenAI."""
        if not content.strip():
            logger.warning("generate_summary called with empty content")
            return None
        
        logger.info(f"Generating summary for {len(content)} characters of content")
        logger.debug(f"Content preview: {content[:200]}...")
        
        prompt = f"""Please provide a concise summary of the following World of Warcraft news articles. Format for Discord readability:

FORMATTING REQUIREMENTS:
- Use **bold** for topic headers
- Use bullet points (•) for key details under each topic
- Include the source URL after each topic section
- Keep topics clearly separated with blank lines
- Maximum 400 words total
- Focus on actionable information for players

CONTENT TO SUMMARIZE:
{content}

Please organize by major topics and include the Wowhead source URL after each topic section. Format example:
**Topic Name**
• Key point 1
• Key point 2
📖 Read more: [URL]

Summary:"""

        try:
            logger.info("Making OpenAI API call...")
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes Discord channel activity, focusing on news and important discussions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            logger.info("OpenAI API call completed successfully")
            logger.debug(f"Response object: {response}")
            
            if not response.choices:
                logger.error("OpenAI response has no choices")
                return None
                
            if not response.choices[0].message:
                logger.error("OpenAI response choice has no message")
                return None
                
            summary = response.choices[0].message.content
            if not summary:
                logger.error("OpenAI response message content is empty")
                return None
                
            summary = summary.strip()
            logger.info(f"Successfully generated AI summary ({len(summary)} characters)")
            logger.debug(f"Summary preview: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    async def send_summary(self, channel: discord.TextChannel, summary: str, message_count: int, date_range: str) -> bool:
        """Send the summary to the Discord channel."""
        try:
            summary_message = f"""📰 **Daily WoW News Summary** ({date_range})
*Processed {message_count} articles*

{summary}

─────────────────────────────
*🤖 Generated by NewsBot • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*"""

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
            content = await self.prepare_content_for_summary(messages)
            logger.info(f"Prepared content for summary: {len(content)} characters")
            if len(content) > 0:
                logger.debug(f"Content sample: {content[:300]}...")
            else:
                logger.warning("Prepared content is empty!")
            
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
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.http_client.aclose()
            logger.info("HTTP client closed")
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")

async def main():
    """Main entry point."""
    try:
        bot = NewsBot()
        
        @bot.client.event
        async def on_ready():
            logger.info(f"Bot logged in as {bot.client.user}")
            try:
                await bot.run_daily_summary()
            finally:
                await bot.cleanup()
                await bot.client.close()
        
        await bot.client.start(bot.discord_token)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())