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

    async def get_openai_translation(self, weather_report: str, report_type: str) -> str:
        """Uses OpenAI API to translate a METAR or TAF report into plain English."""
        prompt = f"""
        Convert the following {report_type} aviation weather report into a concise, layperson-friendly weather summary.

        {report_type}: {weather_report}

        Do not include any greetings, introductions, or explanations—just provide the summary in plain English.
        """

        if not self.openai_api_key:
            logger.error("🚨 OpenAI API key is missing! Check Heroku config vars.")
            return "Error: Missing OpenAI API key."

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an aviation weather expert who explains METAR and TAF in simple terms without introductions."},
                    {"role": "user", "content": prompt}
                ],
                timeout=10
            )

            translated_text = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI API Response (truncated): {translated_text[:100]}...")

            # Ensure truncation to fit within Discord's 1024 character limit
            if len(translated_text) > 900:
                translated_text = translated_text[:900] + "..."

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

                # Extract raw METAR and TAF reports
                raw_metar = metar_data[0].get("rawOb", None) if metar_data else None
                raw_taf = taf_data[0].get("rawTAF", None) if taf_data else None

                # **Prioritize METAR, fallback to TAF if METAR is unavailable**
                if raw_metar:
                    translated_weather = await self.get_openai_translation(raw_metar, "METAR")
                    selected_report = raw_metar
                    report_type = "METAR"
                elif raw_taf:
                    translated_weather = await self.get_openai_translation(raw_taf, "TAF")
                    selected_report = raw_taf
                    report_type = "TAF"
                else:
                    translated_weather = "No weather report available."
                    selected_report = "No report available."
                    report_type = "None"

                # Ensure truncation for the selected report
                selected_report = selected_report[:1020] + "..." if len(selected_report) > 1024 else selected_report
                translated_weather = translated_weather[:1020] + "..." if len(translated_weather) > 1024 else translated_weather

                # Create embed response
                embed = discord.Embed(
                    title=f"Weather Information for {airport_code}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name=f"{report_type}", value=f"```{selected_report}```", inline=False)
                embed.add_field(name="Plain English Translation", value=f"```{translated_weather}```", inline=False)

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"❌ Error in weather command: {e}")
                await interaction.followup.send("An error occurred while fetching weather information.")

async def setup(bot):
    await bot.add_cog(Weather(bot))
