import os

import cv2
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks


class RmImg(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="反転",
            callback=self.cmd_reverse,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.guild_data = {}
        self.cache_msg_delete.start()

    # 画像の色の割合を出す関数
    async def white_raito_img(self, fp: str) -> tuple[float, float]:
        img = cv2.imread(fp, 0)  # 画像の読み込み
        ret1, img_th = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)  # 特定の範囲のGaussian分布から閾値を自動で決めて二値化
        whole_area = img_th.size  # 全体の画素数
        white_area = cv2.countNonZero(img_th)  # 白部分の画素数
        black_area = whole_area - white_area  # 黒部分の画素数

        white_area_ratio = white_area / whole_area  # 白部分の割合
        black_area_ratio = black_area / whole_area

        return white_area_ratio, black_area_ratio

    # 画像の色を反転する関数
    def reverse_img(self, fp: str) -> None:
        img = cv2.imread(fp, 0)  # 画像の読み込み
        img_rewrite = cv2.bitwise_not(img)  # 白黒反転
        cv2.imwrite(fp, img_rewrite)

    @app_commands.command(name="削除設定")
    async def set_remove(self, interaction: discord.Interaction, value: str):
        if not interaction.guild.id in self.guild_data:
            self.guild_data[interaction.guild.id] = {"AutoRemove": False, "ManualRemove": False, "Ratio": 0.85}
        if value == "00":
            self.guild_data[interaction.guild.id]["AutoRemove"] = False
            self.guild_data[interaction.guild.id]["ManualRemove"] = False
        elif value == "10":
            self.guild_data[interaction.guild.id]["AutoRemove"] = True
            self.guild_data[interaction.guild.id]["ManualRemove"] = False
        elif value == "01":
            self.guild_data[interaction.guild.id]["AutoRemove"] = False
            self.guild_data[interaction.guild.id]["ManualRemove"] = True
        elif value == "11":
            self.guild_data[interaction.guild.id]["AutoRemove"] = True
            self.guild_data[interaction.guild.id]["ManualRemove"] = True
        return await interaction.response.send_message(str(self.guild_data[interaction.guild.id]), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if len(message.attachments) == 0:
            return

        if not message.guild.id in self.guild_data:
            return

        if self.guild_data.get(message.guild.id).get("AutoRemove") is False:
            return

        cache_msg_dict = {}
        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                name = f"{message.id}-{message.attachments.index(attachment)}-{attachment.id}.{attachment.filename.split('.')[-1]}"
                await attachment.save(f"./tmp/{name}")
                cache_msg_dict[message.channel.id] = cache_msg_dict.get(message.channel.id, []) + [f"./tmp/{name}"]

                white_area_ratio, _ = await self.white_raito_img(fp=f"./tmp/{name}")

                if white_area_ratio > 0.85:
                    self.reverse_img(fp=f"./tmp/{name}")

                    if "Right Img Replace <UnforgivableRightImageBot>" not in [w.name for w in await message.channel.webhooks()]:
                        webhook = await message.channel.create_webhook(name="Right Img Replace <UnforgivableRightImageBot>")
                    else:
                        webhook = [w for w in await message.channel.webhooks() if w.name == "Right Img Replace <UnforgivableRightImageBot>"][0]

                    cache_msg = message
                    await message.delete()
                    await webhook.send(content=cache_msg.content, username=cache_msg.author.display_name, avatar_url=cache_msg.author.display_avatar, file=discord.File(f"./tmp/{name}"))
                    await cache_msg.channel.send(
                        f"{message.author.mention} 画像に白色が大量に含まれているため削除しました。")

                os.remove(f"./tmp/{name}")
                cache_msg_dict.pop(message.channel.id)

    async def cmd_reverse(self, interaction: discord.Interaction, message: discord.Message):

        if not message.guild.id in self.guild_data or self.guild_data.get(message.guild.id).get("ManualRemove") is False:
            return await interaction.response.send_message("このサーバーでは画像の手動削除が有効になっていません。", ehemeral=True)

        """画像を白黒反転します。"""
        if len(message.attachments) == 0:
            return await interaction.response.send_message("画像はないよ！", ehemeral=True)

        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                name = f"{message.id}-{message.attachments.index(attachment)}-{attachment.id}.{attachment.filename.split('.')[-1]}"
                await attachment.save(f"./tmp/{name}")

                white_area_ratio, black_area_ratio = await self.white_raito_img(fp=f"./tmp/{name}")
                if white_area_ratio > 0.85:
                    self.reverse_img(fp=f"./tmp/{name}")

                    if "Right Img Replace <UnforgivableRightImageBot>" not in [w.name for w in
                                                                               await interaction.channel.webhooks()]:
                        webhook = await interaction.channel.create_webhook(name="Right Img Replace <UnforgivableRightImageBot>")
                    else:
                        webhook = [w for w in await interaction.channel.webhooks() if
                                   w.name == "Right Img Replace <UnforgivableRightImageBot>"][0]

                    cache_msg = message
                    await message.delete()
                    await webhook.send(content=cache_msg.content, username=cache_msg.author.display_name,
                                       avatar_url=cache_msg.author.display_avatar, file=discord.File(f"./tmp/{name}"))
                    await interaction.response.send_message("画像に白色が大量に含まれているため削除しました。")

                os.remove(f"./tmp/{name}")

    @tasks.loop(seconds=1)
    async def cache_msg_delete(self):
        for cache_msg_id, cache_msg_data in self.cache_msg_dict.items():
            if cache_msg_data.get("CacheTime") < datetime.now():
                self.cache_msg_dict.pop(cache_msg_id)


async def setup(bot):
    await bot.add_cog(RmImg(bot))
