#!/usr/bin/env python3
"""
Debug version to isolate the 'proxies' error
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def debug_step(step_name, func):
    """Execute a function and catch any errors"""
    try:
        logger.info(f"Starting: {step_name}")
        result = func()
        logger.info(f"Success: {step_name}")
        return result
    except Exception as e:
        logger.error(f"Error in {step_name}: {e}")
        traceback.print_exc()
        raise

def main():
    # Check environment variables
    logger.info("Checking environment variables...")
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    logger.info(f"DISCORD_BOT_TOKEN: {'SET' if discord_token else 'NOT SET'}")
    logger.info(f"OPENAI_API_KEY: {'SET' if openai_api_key else 'NOT SET'}")
    logger.info(f"DISCORD_CHANNEL_ID: {'SET' if channel_id else 'NOT SET'}")
    
    # Test imports one by one
    logger.info("Testing imports...")
    
    def import_discord():
        import discord
        return discord
    
    def import_openai():
        import openai
        return openai
    
    discord = debug_step("Import discord", import_discord)
    openai = debug_step("Import openai", import_openai)
    
    # Test Discord client creation
    def create_discord_client():
        intents = discord.Intents.default()
        intents.message_content = True
        return discord.Client(intents=intents)
    
    discord_client = debug_step("Create Discord client", create_discord_client)
    
    # Test OpenAI client creation
    def create_openai_client():
        return openai.OpenAI(api_key=openai_api_key)
    
    openai_client = debug_step("Create OpenAI client", create_openai_client)
    
    logger.info("All components created successfully!")
    logger.info("The error must be occurring during the async execution or Discord connection.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)