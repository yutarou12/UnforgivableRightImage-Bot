import os
import traceback

import discord
from discord import Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands

import libs.env as env
from libs.Database import Database


extensions_list = [f[:-3] for f in os.listdir("./cogs") if f.endswith(".py")]


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        traceback_channel = await bot.fetch_channel(env.TRACEBACK_CHANNEL_ID)

        tracebacks = getattr(error, 'traceback', error)
        tracebacks = ''.join(traceback.TracebackException.from_exception(tracebacks).format())
        tracebacks = discord.utils.escape_markdown(tracebacks)
        embed_traceback = discord.Embed(title='Traceback Log', description=f'```{tracebacks}```')
        await traceback_channel.send(embed=embed_traceback)

    async def setup_hook(self):
        await bot.load_extension('jishaku')
        for ext in extensions_list:
            await bot.load_extension(f'cogs.{ext}')

    async def get_context(self, message, *args, **kwargs):
        return await super().get_context(message, *args, **kwargs)


intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(
    command_prefix=commands.when_mentioned_or('uri.'),
    intents=intents,
    allowed_mentions=discord.AllowedMentions(replied_user=False, everyone=False),
    help_command=None
)

bot.db = Database()

if __name__ == '__main__':
    bot.run(env.DISCORD_BOT_TOKEN)
