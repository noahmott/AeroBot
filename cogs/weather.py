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

    async def get_openai_translation(self, report: str, report_type: str) -> str:
        """Uses OpenAI API to translate a METAR or TAF report into plain English."""
        prompt = f"""
        Convert the following {report_type} aviation weather report into a structured, easy-to-read summary.
        
        {report_type}: {report}

        Requirements:
        1. Format the response in these sections:
           - Time (always specify UTC)
           - Temperature (show both °C and °F)
           - Wind
           - Visibility
           - Sky Conditions
           - Other Conditions (if any)
        2. Convert all temperatures to include both Celsius and Fahrenheit
        3. Use bullet points (•) for each section
        4. Keep it concise and factual
        5. Do NOT include any introductions or explanations
        6. If any section has no data, skip it entirely

        Example format:
        • Time (UTC): 1200Z
        • Temperature: 20°C (68°F)
        • Wind: From 180° at 10 knots
        • Visibility: 10 statute miles
        • Sky Conditions: Few clouds at 3000ft
        """

        if not self.openai_api_key:
            logger.error("🚨 OpenAI API key is missing! Check environment variables.")
            return "Error: Missing OpenAI API key."

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an aviation weather expert who provides structured, consistent weather summaries. Always use bullet points and include both °C and °F temperatures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Add some variability while maintaining structure
                max_tokens=500,
                timeout=10
            )

            translated_text = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI API Response (truncated): {translated_text[:100]}...")

            # Ensure the response starts with a bullet point
            if not translated_text.startswith('•'):
                translated_text = '• ' + translated_text

            # Truncate if needed to fit Discord's character limit
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
                raw_metar = metar_data[0].get("rawOb", None) if metar_data else "No METAR available"
                raw_taf = taf_data[0].get("rawTAF", None) if taf_data else "No TAF available"

                # **Prioritize METAR for translation, fallback to TAF if METAR is unavailable**
                if raw_metar and raw_metar != "No METAR available":
                    translated_weather = await self.get_openai_translation(raw_metar, "METAR")
                    selected_report_type = "METAR"
                elif raw_taf and raw_taf != "No TAF available":
                    translated_weather = await self.get_openai_translation(raw_taf, "TAF")
                    selected_report_type = "TAF"
                else:
                    translated_weather = "No weather report available."
                    selected_report_type = "None"

                # Ensure truncation for the Discord embed field limits
                raw_metar = raw_metar[:1020] + "..." if len(raw_metar) > 1024 else raw_metar
                raw_taf = raw_taf[:1020] + "..." if len(raw_taf) > 1024 else raw_taf
                translated_weather = translated_weather[:1020] + "..." if len(translated_weather) > 1024 else translated_weather

                # Create embed response
                embed = discord.Embed(
                    title=f"Weather Information for {airport_code}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="📡 METAR (Raw Data)", value=f"```{raw_metar}```", inline=False)
                embed.add_field(name="🗒️ TAF (Raw Data)", value=f"```{raw_taf}```", inline=False)
                embed.add_field(name="🌍 Translation (UTC Times)", value=f"```{translated_weather}```", inline=False)

                await interaction.followup.send(embed=embed)

            except Exception as e:
                logger.error(f"❌ Error in weather command: {e}")
                await interaction.followup.send("An error occurred while fetching weather information.")

async def setup(bot):
    await bot.add_cog(Weather(bot))
