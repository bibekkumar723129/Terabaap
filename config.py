import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # required
API_ID = int(os.getenv("API_ID", 2040))
API_HASH = os.getenv("API_HASH", "b18441a1ff607e10a989891a4eaaf88f")

# the iTeraPlay API key (you can place key here or put in .env)
ITERAPLAY_KEY = os.getenv("ITERAPLAY_KEY", "iTeraPlay2025")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024 * 1024))  # 20 GB default
