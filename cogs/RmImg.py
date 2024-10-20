import os
import cv2
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

from libs.Database import Database


class RmImg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="反転",
            callback=self.cmd_reverse,
        )
        self.ctx_menu_delete = app_commands.ContextMenu(
            name="削除",
            callback=self.image_user_delete,
        )
        self.bot.tree.add_command(self.ctx_menu)
        self.bot.tree.add_command(self.ctx_menu_delete)
        self.cache_msg_dict = {}
        self.cache_msg_delete.start()
        self.db: Database = self.bot.db

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
    async def set_remove(self, interaction: discord.Interaction, value: str, ratio: float):
        guild_data = await self.db.get_guild_setting(interaction.guild.id)
        auto_remove, manual_remove = list(map(bool, list(map(int, list(value)))))
        if not guild_data:
            await self.db.add_guild_setting(interaction.guild.id, value, ratio, auto_remove, manual_remove)
        else:
            await self.db.update_guild_setting(interaction.guild.id, value, ratio)
        guild_data = await self.db.get_guild_setting(interaction.guild.id)
        return await interaction.response.send_message(str(guild_data), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if len(message.attachments) == 0:
            return

        guild_data = await self.db.get_guild_setting(message.guild.id)
        if not guild_data:
            return

        if guild_data.get("AutoRemove") is False:
            return

        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                name = f"{message.id}-{message.attachments.index(attachment)}-{attachment.id}.{attachment.filename.split('.')[-1]}"
                await attachment.save(f"./tmp/{name}")

                white_area_ratio, _ = await self.white_raito_img(fp=f"./tmp/{name}")

                if white_area_ratio > guild_data.get("Ratio"):
                    self.reverse_img(fp=f"./tmp/{name}")

                    if "Right Img Replace <UnforgivableRightImageBot>" not in [w.name for w in await message.channel.webhooks()]:
                        webhook = await message.channel.create_webhook(name="Right Img Replace <UnforgivableRightImageBot>")
                    else:
                        webhook = [w for w in await message.channel.webhooks() if w.name == "Right Img Replace <UnforgivableRightImageBot>"][0]

                    cache_msg = message
                    await message.delete()
                    webhook_msg = await webhook.send(content=cache_msg.content, username=cache_msg.author.display_name, avatar_url=cache_msg.author.display_avatar, file=discord.File(f"./tmp/{name}"), wait=True)
                    self.cache_msg_dict[webhook_msg.id] = {"Author": cache_msg.author.id, "CacheTime": datetime.now() + timedelta(minutes=30)}

                    await cache_msg.channel.send(
                        f"{message.author.mention} 画像に白色が大量に含まれているため削除しました。", delete_after=5)

                os.remove(f"./tmp/{name}")

    async def cmd_reverse(self, interaction: discord.Interaction, message: discord.Message):
        guild_data = await self.db.get_guild_setting(message.guild.id)
        if not guild_data or guild_data.get("ManualRemove") is False:
            return await interaction.response.send_message("このサーバーでは画像の手動削除が有効になっていません。", ephemeral=True)

        if message.author.bot:
            return await interaction.response.send_message("Botのメッセージは削除できません。", ephemeral=True)

        # 画像がない場合
        if len(message.attachments) == 0:
            return await interaction.response.send_message("画像はないよ！", ephemeral=True)

        # 画像を白黒反転します。
        for attachment in message.attachments:
            if attachment.content_type.startswith("image"):
                name = f"{message.id}-{message.attachments.index(attachment)}-{attachment.id}.{attachment.filename.split('.')[-1]}"
                await attachment.save(f"./tmp/{name}")

                white_area_ratio, black_area_ratio = await self.white_raito_img(fp=f"./tmp/{name}")
                if white_area_ratio > guild_data.get("Ratio"):
                    self.reverse_img(fp=f"./tmp/{name}")

                    if "Right Img Replace <UnforgivableRightImageBot>" not in [w.name for w in
                                                                               await interaction.channel.webhooks()]:
                        webhook = await interaction.channel.create_webhook(name="Right Img Replace <UnforgivableRightImageBot>")
                    else:
                        webhook = [w for w in await interaction.channel.webhooks() if
                                   w.name == "Right Img Replace <UnforgivableRightImageBot>"][0]

                    cache_msg = message
                    await message.delete()
                    webhook_msg = await webhook.send(content=cache_msg.content, username=cache_msg.author.display_name,
                                                     avatar_url=cache_msg.author.display_avatar, file=discord.File(f"./tmp/{name}"), wait=True)
                    self.cache_msg_dict[webhook_msg.id] = {"Author": cache_msg.author.id, "CacheTime": datetime.now() + timedelta(minutes=30)}

                    await interaction.response.send_message("画像に白色が大量に含まれているため削除しました。", ephemeral=True)

                os.remove(f"./tmp/{name}")

    async def image_user_delete(self, interaction: discord.Interaction, message: discord.Message):
        if len(message.attachments) == 0:
            return await interaction.response.send_message("画像はないよ！", ephemeral=True)

        if self.cache_msg_dict.get(message.id):
            cache_msg_data = self.cache_msg_dict.get(message.id)
            if cache_msg_data.get("Author") == interaction.user.id:
                await message.delete()
                return await interaction.response.send_message("画像を削除しました。", ephemeral=True)
            else:
                return await interaction.response.send_message("このメッセージはあなたではありません！", ephemeral=True)
        elif not message.webhook_id and message.author.id == interaction.user.id:
            return await interaction.response.send_message("自分で消せませんか！？", ephemeral=True)
        elif not message.webhook_id and message.author.id != interaction.user.id:
            return await interaction.response.send_message("このメッセージはあなたではありません！", ephemeral=True)
        else:
            return await interaction.response.send_message("このメッセージはもう削除できません！", ephemeral=True)

    @tasks.loop(seconds=1)
    async def cache_msg_delete(self):
        for cache_msg_id, cache_msg_data in self.cache_msg_dict.items():
            if cache_msg_data.get("CacheTime") < datetime.now():
                self.cache_msg_dict.pop(cache_msg_id)


async def setup(bot):
    await bot.add_cog(RmImg(bot))
