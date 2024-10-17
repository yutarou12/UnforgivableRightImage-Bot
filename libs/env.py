import os
from dotenv import load_dotenv

load_dotenv()


DISCORD_BOT_TOKEN: str = os.environ.get("DISCORD_BOT_TOKEN", "")
TRACEBACK_CHANNEL_ID: int = int(os.environ.get("TRACEBACK_CHANNEL_ID", ""))
