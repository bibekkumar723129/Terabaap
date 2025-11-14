from pyrogram.types import Message

def human_readable_size(size, decimals=2):
    if size is None:
        return "Unknown"
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024.0:
            return f"{size:.{decimals}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimals}f} PB"

async def send_progress_edit(message: Message, status_text: str):
    try:
        await message.edit_text(status_text)
    except Exception:
        pass
