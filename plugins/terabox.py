import os
import asyncio
import math
from pyrogram import filters
from pyrogram.types import Message
from main import app
from helpers.iteraplay_api import fetch_player_page, extract_m3u8_links, map_qualities
from helpers.ffmpeg_downloader import run_ffmpeg_hls_to_mp4
from helpers.logger import logger
from plugins.progress import human_readable_size, send_progress_edit
from config import MAX_FILE_SIZE

QUALITY_ORDER = ["720p", "480p", "360p", "auto"]

@app.on_message(filters.private & filters.text)
async def handle_terabox(client, message: Message):
    url = message.text.strip()
    if "terabox" not in url:
        return

    status_msg = await message.reply_text("🔎 Resolving iTeraPlay player…")
    try:
        html = fetch_player_page(url)
        m3u8_links = extract_m3u8_links(html)
        if not m3u8_links:
            await status_msg.edit_text("❌ Could not find any HLS streams in API response.")
            return

        qualities = map_qualities(m3u8_links)
        if not qualities:
            await status_msg.edit_text("❌ No playable streams found.")
            return

        # reorder according to desired quality strategy: try highest then fallback
        ordered = []
        # build dict
        qual_dict = {q:link for q,link in qualities}
        for q in QUALITY_ORDER:
            if q in qual_dict:
                ordered.append((q, qual_dict[q]))
        # if nothing matched, append whatever was found
        if not ordered:
            ordered = qualities

        chosen = None
        chosen_label = None

        # Try each quality until ffmpeg can finish (we consider success if ffmpeg returns 0)
        for label, m3u8 in ordered:
            await status_msg.edit_text(f"⬇️ Attempting {label} stream...")
            logger.info("Trying quality %s -> %s", label, m3u8)
            # prepare output filename
            safe_name = f"terabox_{message.from_user.id}_{int(asyncio.get_event_loop().time())}_{label}.mp4"
            # progress callback updates the message
            def progress_cb(percent, downloaded, path):
                try:
                    text = f"🔁 Downloading {label} — {human_readable_size(downloaded)}"
                    # percent may be None while ffmpeg running; we show size
                    asyncio.get_event_loop().create_task(send_progress_edit(status_msg, text))
                except Exception:
                    pass

            try:
                out_path = await run_ffmpeg_hls_to_mp4(m3u8, safe_name, progress_cb=progress_cb)
                # check size
                size = os.path.getsize(out_path)
                if size == 0:
                    raise RuntimeError("Downloaded file size is zero")
                if size > MAX_FILE_SIZE:
                    await status_msg.edit_text(f"⚠️ File too large ({human_readable_size(size)}). Limit reached.")
                    os.remove(out_path)
                    return
                chosen = out_path
                chosen_label = label
                break
            except Exception as e:
                logger.warning("Quality %s failed: %s", label, e)
                # try next quality
                await status_msg.edit_text(f"⚠️ {label} failed, trying lower quality...")
                await asyncio.sleep(1)
                continue

        if not chosen:
            await status_msg.edit_text("❌ All qualities failed to download.")
            return

        # Uploading
        await status_msg.edit_text(f"📤 Uploading {chosen_label} — {human_readable_size(os.path.getsize(chosen))} ...")
        await client.send_document(chat_id=message.chat.id, document=chosen, caption=f"TeraBox ({chosen_label})")
        await status_msg.delete()
        # cleanup
        try:
            os.remove(chosen)
        except Exception:
            pass

    except Exception as e:
        logger.exception("Error in handler: %s", e)
        try:
            await status_msg.edit_text("❌ Error: " + str(e))
        except Exception:
            pass
