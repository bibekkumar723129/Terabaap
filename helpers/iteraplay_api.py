import re
import requests
from helpers.logger import logger
from config import ITERAPLAY_KEY

API_TEMPLATE = "https://iteraplay.com/api/play.php?url={url}&key={key}"

M3U8_REGEX = re.compile(r"https?:\/\/[^\s'\"<>]+\.m3u8[^\s'\"<>]*")

def fetch_player_page(terabox_url: str, timeout=15):
    api_url = API_TEMPLATE.format(url=terabox_url, key=ITERAPLAY_KEY)
    logger.info("Fetching player page: %s", api_url)
    resp = requests.get(api_url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text

def extract_m3u8_links(html: str):
    # Find unique m3u8 links
    matches = M3U8_REGEX.findall(html)
    # return unique while preserving order
    seen = set()
    out = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            out.append(m)
    logger.info("Found %d m3u8 links", len(out))
    return out

def map_qualities(m3u8_links: list):
    # map quality label by a simple heuristics: look for '720','480','360' in the URL
    qualities = {}
    for link in m3u8_links:
        l = link.lower()
        if "720" in l:
            qualities["720p"] = link
        elif "480" in l:
            qualities["480p"] = link
        elif "360" in l:
            qualities["360p"] = link
        else:
            # fallback generic
            qualities.setdefault("auto", link)
    # keep order: 720,480,360,auto
    ordered = []
    for q in ("720p","480p","360p","auto"):
        if q in qualities:
            ordered.append((q, qualities[q]))
    return ordered
