import os
from dotenv import load_dotenv

load_dotenv()


DISCORD_BOT_TOKEN: str = os.environ.get("DISCORD_BOT_TOKEN", "")
TRACEBACK_CHANNEL_ID: int = int(os.environ.get("TRACEBACK_CHANNEL_ID", ""))

POSTGRESQL_USER: str = os.environ.get("POSTGRESQL_USER", "")
POSTGRESQL_PASSWORD: str = os.environ.get("POSTGRESQL_PASSWORD", "")
POSTGRESQL_HOST_NAME: str = os.environ.get("POSTGRESQL_HOST_NAME", "")
POSTGRESQL_PORT: str = os.environ.get("POSTGRESQL_PORT", "")
POSTGRESQL_DATABASE_NAME: str = os.environ.get("POSTGRESQL_DATABASE_NAME", "")

DEBUG: int = int(os.environ.get("DEBUG", 0))
