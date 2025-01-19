import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime, timezone

logger = logging.getLogger('aviator_bot.notam')

class NOTAM(commands.Cog, name="notams"):
    """NOTAM commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="notams",
        description="Get NOTAMs for an airport"
    )
    async def get_notams(self, interaction: discord.Interaction, airport: str):
        """Get NOTAMs for a specific airport"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.faa.gov/notam/v1/notams"
                params = {
                    'icaoCode': airport.upper(),
                    'format': 'json'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        embed = discord.Embed(
                            title=f"NOTAMs for {airport.upper()}",
                            color=discord.Color.blue(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        if data:
                            for notam in data[:5]:  # Limit to 5 NOTAMs
                                embed.add_field(
                                    name=f"NOTAM {notam.get('id', 'Unknown')}",
                                    value=f"```{notam.get('message', 'No details available')}```",
                                    inline=False
                                )
                        else:
                            embed.add_field(
                                name="No NOTAMs",
                                value="No NOTAMs found for this airport",
                                inline=False
                            )
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Error fetching NOTAMs for {airport.upper()}")
                        
        except Exception as e:
            logger.error(f"Error in NOTAM command: {e}")
            await interaction.followup.send("An error occurred while fetching NOTAMs")

async def setup(bot):
    await bot.add_cog(NOTAM(bot))
