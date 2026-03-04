# Woolton Delivery Office Weather Telegram Bot

Telegram bot for Woolton Delivery Office staff. It provides a daily weather briefing for the L25 delivery area and supports self-subscription via Telegram commands.

## Features

- Daily weather briefing at **07:00** via GitHub Actions
- Forecast source: Open-Meteo UK Met Office 2km model
- Commands:
  - `/start` → subscribe
  - `/stop` → unsubscribe
  - `/weather` → instant forecast
- Subscriber storage in local `subscribers.json` (no external DB)

## Project Structure

- `weather_bot.py` – main bot logic and command handling
- `weather_api.py` – fetches and structures weather data
- `message_formatter.py` – formats Telegram output and advice
- `subscribers.json` – local subscriber list
- `requirements.txt` – Python dependencies
- `.github/workflows/weather.yml` – scheduled automation

## Security / Secrets

Do **not** commit the Telegram token.

Set repository secret:

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `TELEGRAM_BOT_TOKEN`
4. Value: your BotFather token

The bot reads token from environment variable:

- `TELEGRAM_BOT_TOKEN`

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="<your_token>"   # Windows PowerShell: $env:TELEGRAM_BOT_TOKEN="<your_token>"
```

### Run one-shot daily mode

```bash
python weather_bot.py
```

### Run continuous Telegram polling mode (for live command handling)

```bash
export RUN_MODE=bot
python weather_bot.py
```

## GitHub Actions Schedule

Workflow file: `.github/workflows/weather.yml`

- Cron: `0 7 * * *`
- Timezone environment set to `Europe/London`
- Each run:
  1. installs dependencies
  2. processes pending Telegram commands
  3. sends the daily weather briefing to all subscribers

## User Onboarding

1. User opens `@Wooltonbot`
2. Sends `/start`
3. Their Telegram ID is added to `subscribers.json`
4. They receive daily weather at scheduled time

To unsubscribe, user sends `/stop`.
