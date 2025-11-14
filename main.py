import os
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH
from helpers.logger import logger

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")

app = Client(
    "terabox_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    sleep_threshold=10
)

# register plugins
from plugins import terabox, progress  # noqa: F401

if __name__ == "__main__":
    logger.info("Starting TeraBox Downloader Bot...")
    app.run()
