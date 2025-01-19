import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime, timezone
import csv
from io import StringIO

logger = logging.getLogger('aviator_bot.airport')

class Airport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.airports_url = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"
        self.frequencies_url = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airport-frequencies.csv"
        self.runways_url = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/runways.csv"
        
    @app_commands.command(
        name="airport",
        description="Get information about an airport"
    )
    async def airport(
        self,
        interaction: discord.Interaction,
        airport_code: str
    ):
        airport_code = airport_code.upper()
        
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch airport data
                async with session.get(self.airports_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(
                            "Error fetching airport data"
                        )
                        return
                    
                    airports_csv = await resp.text()
                    
                # Find airport in CSV data
                airport_data = None
                csv_reader = csv.DictReader(StringIO(airports_csv))
                
                for row in csv_reader:
                    if row['ident'] == airport_code:
                        airport_data = row
                        break
                
                if not airport_data:
                    await interaction.followup.send(
                        f"Airport {airport_code} not found"
                    )
                    return
                
                # Create embed response
                embed = discord.Embed(
                    title=f"{airport_data['name']} ({airport_code})",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Add basic information
                embed.add_field(
                    name="Location",
                    value=f"{airport_data['municipality']}, {airport_data['iso_country']}",
                    inline=True
                )
                
                embed.add_field(
                    name="Elevation",
                    value=f"{airport_data['elevation_ft']} ft",
                    inline=True
                )
                
                embed.add_field(
                    name="Coordinates",
                    value=f"Lat: {airport_data['latitude_deg']}\nLong: {airport_data['longitude_deg']}",
                    inline=True
                )
                
                # Add Google Maps link
                maps_url = f"https://www.google.com/maps?q={airport_data['latitude_deg']},{airport_data['longitude_deg']}"
                embed.add_field(
                    name="Maps",
                    value=f"[View on Google Maps]({maps_url})",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in airport command: {e}")
            await interaction.followup.send(
                "An error occurred while fetching airport information."
            )

async def setup(bot):
    await bot.add_cog(Airport(bot)) 