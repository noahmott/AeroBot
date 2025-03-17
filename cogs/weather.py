import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
import openai
import os
from datetime import datetime, timezone

logger = logging.getLogger('aviator_bot.weather')

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weather_api_url = "https://aviationweather.gov/api/data"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def get_openai_translation(self, metar: str, taf: str) -> str:
        """Uses OpenAI API to translate METAR and TAF into plain English."""
        prompt = f"""
        Translate the following METAR and TAF reports into layperson-friendly weather descriptions:

        METAR: {metar if metar else 'No METAR available'}
        TAF: {taf if taf else 'No TAF available'}

        Provide a structured and concise response describing the weather conditions.
        """

        if not self.openai_api_key:
            logger.error("🚨 OpenAI API key is missing! Check Heroku config vars.")
            return "Error: Missing OpenAI API key."

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",  # Use "gpt-3.5-turbo" for faster responses
                messages=[
                    {"role": "system", "content": "You are an aviation weather expert translating reports into plain language."},
                    {"role": "user", "content": prompt}
                ]
            )

            translated_text = response.choices[0].message.content
            logger.info(f"✅ OpenAI API Response: {translated_text[:100]}")  # Log first 100 chars

            # 🔥 Truncate to Discord's max field length (1024 characters)
            if len(translated_text) > 1024:
                translated_text = translated_text[:1020] + "..."  # Append "..." if truncated

            return translated_text

        except Exception as e:
            logger.error(f"❌ OpenAI API Error: {e}")
            return "Error: Unable to fetch translation."

    @app_commands.command(
        name="weather",
        description="Get METAR and TAF for an airport, with plain English translation"
    )
    async def weather(self, interaction: discord.Interaction, airport_code: str):
        airport_code = airport_code.upper()
        
        await interaction.response.defer()  # Defer response while processing

        async with aiohttp.ClientSession() as session:
            try:
                # Fetch METAR
                metar_url = f"{self.weather_api_url}/metar"
                metar_params = {'ids': airport_code, 'format': 'json'}

                async with session.get(metar_url, params=metar_params) as resp:
                    if resp.status != 200:
                        logger.error(f"METAR API error: {resp.status}")
                        metar_data = None
                    else:
                        metar_data = await resp.json()

                # Fetch TAF
                taf_url = "https://aviationweather.gov/api/data/taf"
                taf_params = {'ids': airport_code, 'format': 'json'}

                async with session.get(taf_url, params=taf_params) as resp:
                    if resp.status != 200:
                        logger.error(f"TAF API error: {resp.status}")
                        taf_data = None
                    else:
                        taf_data = await resp.json()

                # Extract raw reports
                raw_metar = metar_data[0].get("rawOb", "No METAR available") if metar_data else "No METAR available"
                raw_taf = taf_data[0].get("rawTAF", "No TAF available") if taf_data else "No TAF available"

                # Get OpenAI translation
                translated_weather = await self.get_openai_translation(raw_metar, raw_taf)

                # Create embed response
                embed = discord.Embed(
                    title=f"Weather Information for {airport_code}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="METAR", value=f"```{raw_metar[:1020] + '...' if len(raw_metar) > 1024 else raw_metar}```", inline=False)
                embed.add_field(name="TAF", value=f"```{raw_taf[:1020] + '...' if len(raw_taf) > 1024 else raw_taf}```", inline=False)
                embed.add_field(name="Plain English Translation", value=f"```{translated_weather}```", inline=False)

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"❌ Error in weather command: {e}")
                await interaction.followup.send("An error occurred while fetching weather information.")

async def setup(bot):
    await bot.add_cog(Weather(bot))
