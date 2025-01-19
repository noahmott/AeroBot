import os
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('aviator_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define the bot class
class AviatorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.load_extension('cogs.weather')
            print("Weather cog loaded")
            await self.load_extension('cogs.airport')
            print("Airport cog loaded")
            await self.tree.sync()
            print("Command tree synced")
        except Exception as e:
            print(f"Error: {e}")

# Initialize and run the bot
bot = AviatorBot()

if __name__ == '__main__':
    bot.run(TOKEN)
