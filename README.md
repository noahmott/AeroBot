# AviatorBot

A Discord bot for pilots and aviation enthusiasts that provides real-time weather reports, airport information, and flight planning assistance.

## Features

- `/weather [airport_code]` - Get METAR and TAF reports
- `/airport [airport_code]` - Get detailed airport information including:
  - Runway details
  - Communication frequencies
  - Location and elevation
  - Google Maps link

## Setup

1. **Prerequisites**
   - Python 3.8+
   - Discord account and application
   - Bot token from Discord Developer Portal

2. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/aviatorbot
   cd aviatorbot

   # Install dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your Discord bot token and application ID
   ```

3. **Configuration**
   Edit `.env` file:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_APP_ID=your_application_id_here
   ```

4. **Running the Bot**
   ```bash
   python bot.py
   ```

## Usage Examples

### Weather Information
