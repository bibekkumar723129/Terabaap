import asyncio
import os
import time
import shlex
from pathlib import Path
from helpers.logger import logger
from config import DOWNLOAD_DIR

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

async def run_ffmpeg_hls_to_mp4(m3u8_url: str, out_filename: str, progress_cb=None, timeout=None):
    """
    Downloads HLS m3u8 into MP4 using ffmpeg with -c copy.
    progress_cb(percent_estimate, downloaded_bytes, path) is called periodically.
    We cannot know final size before finishing; we supply estimates by file size growth.
    """
    out_path = Path(DOWNLOAD_DIR) / out_filename
    # remove existing
    if out_path.exists():
        out_path.unlink()

    # ffmpeg command: copy all streams to mp4 container
    cmd = f'ffmpeg -y -hide_banner -loglevel warning -i "{m3u8_url}" -c copy "{out_path}"'
    logger.info("Running ffmpeg: %s", cmd)
    # Start subprocess
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    last_report = 0
    try:
        # while running, report file-size based progress every 2s
        while True:
            if process.returncode is None:
                # process still running; poll
                await asyncio.sleep(2)
                downloaded = out_path.stat().st_size if out_path.exists() else 0
                now = time.time()
                # call progress callback with None percent (unknown)
                if progress_cb and now - last_report >= 2:
                    try:
                        progress_cb(None, downloaded, str(out_path))
                    except Exception:
                        pass
                    last_report = now
                # continue loop
                rc = process.returncode
                if rc is not None:
                    break
                # try to check if process finished without awaiting
                rc = await process.wait()
                break
            else:
                break
    except asyncio.CancelledError:
        logger.warning("ffmpeg task cancelled, terminating process")
        process.kill()
        raise
    except Exception as e:
        logger.exception("Error while running ffmpeg: %s", e)
        process.kill()
        raise

    # ensure process finished
    returncode = await process.wait()
    if returncode != 0:
        # try to read stderr
        stderr = await process.stderr.read()
        logger.error("ffmpeg failed (code %s): %s", returncode, stderr[:400])
        raise RuntimeError(f"ffmpeg failed with code {returncode}")
    # final size
    final_size = out_path.stat().st_size if out_path.exists() else 0
    if progress_cb:
        try:
            progress_cb(100, final_size, str(out_path))
        except Exception:
            pass
    return str(out_path)
