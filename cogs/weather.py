import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime, timezone

logger = logging.getLogger('aviator_bot.weather')

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weather_api_url = "https://aviationweather.gov/api/data"
        
    @app_commands.command(
        name="weather",
        description="Get METAR and TAF for an airport"
    )
    async def weather(
        self,
        interaction: discord.Interaction,
        airport_code: str
    ):
        airport_code = airport_code.upper()
        
        # Defer reply since API call might take time
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get METAR
                metar_params = {
                    'ids': airport_code,
                    'format': 'json'
                }
                
                metar_url = f"{self.weather_api_url}/metar"
                logger.info(f"Trying METAR URL: {metar_url} with params: {metar_params}")
                
                async with session.get(metar_url, params=metar_params) as resp:
                    logger.info(f"METAR Status: {resp.status}")
                    if resp.status != 200:
                        logger.error(f"METAR API returned status {resp.status}")
                        await interaction.followup.send(f"Error fetching METAR for {airport_code}")
                        return
                    
                    try:
                        metar_data = await resp.json()
                        logger.info(f"METAR response: {metar_data}")
                        if not metar_data or len(metar_data) == 0:
                            await interaction.followup.send(f"No METAR data found for {airport_code}")
                            return
                    except Exception as e:
                        logger.error(f"Failed to parse METAR JSON: {str(e)}")
                        await interaction.followup.send("Error parsing METAR data")
                        return

                # Get TAF with new endpoint
                taf_params = {
                    'ids': airport_code,
                    'format': 'json'
                }
                
                taf_url = "https://aviationweather.gov/api/data/taf"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                async with session.get(taf_url, params=taf_params, headers=headers) as resp:
                    logger.info(f"TAF Status Code: {resp.status}")
                    if resp.status != 200:
                        logger.error(f"TAF API returned status {resp.status}")
                        taf_data = None
                    else:
                        try:
                            taf_data = await resp.json()
                            logger.info(f"TAF data received: {taf_data}")
                        except Exception as e:
                            logger.error(f"Failed to parse TAF JSON: {str(e)}")
                            taf_data = None
                
            # Create embed response
            embed = discord.Embed(
                title=f"Weather Information for {airport_code}",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if metar_data and len(metar_data) > 0:
                embed.add_field(
                    name="METAR",
                    value=f"```{metar_data[0].get('rawOb', 'No METAR available')}```",
                    inline=False
                )
            
            if taf_data and len(taf_data) > 0:
                embed.add_field(
                    name="TAF",
                    value=f"```{taf_data[0].get('rawTAF', 'No TAF available')}```",
                    inline=False
                )
            elif taf_data is None:
                embed.add_field(
                    name="TAF",
                    value="```TAF data unavailable```",
                    inline=False
                )
                
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in weather command: {e}")
            await interaction.followup.send(
                "An error occurred while fetching weather information."
            )

async def setup(bot):
    await bot.add_cog(Weather(bot)) 