import discord
from discord.ext import commands
import subprocess
import json
import asyncio
import os

# --- Cog固有の設定---
CORRECT_PASSWORD = os.getenv("UNITE_RESET_PASSWORD")
if CORRECT_PASSWORD is None:
    print("【警告】環境変数 'UNITE_RESET_PASSWORD' が設定されていません。")

# 実際に実行するスクリプトパス
ACTUAL_SCRAPER_SCRIPT_PATH = "cogs/unite_info/unite_sq.py"

# スクリプトが出力するJSONファイル名
EXPECTED_JSON_FILENAME = "cogs/unite_info/all_pokemon_data.json"
# --------------------------------------------------------------------

class ManageDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scraped_data = {}
        
        self.correct_password = CORRECT_PASSWORD
        self.scraper_script_to_execute = ACTUAL_SCRAPER_SCRIPT_PATH
        self.json_to_load = EXPECTED_JSON_FILENAME

    @commands.command(name='unite_info_reset', hidden=True)
    async def unite_info_reset(self, ctx: commands.Context):
        """
        パスワード認証後、データ更新スクリプトを実行し、
        Unite Cogのデータをリロードします。
        """
        if self.correct_password is None:
             await ctx.send("環境変数 `UNITE_RESET_PASSWORD` が設定されていないため実行できません。")
             return

        await ctx.send(f"パスワードを入力してください。（60秒以内）")

        def check(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            password_message = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("タイムアウトしました。")
            return

        if password_message.content == self.correct_password:
            # パスワードメッセージを削除
            try: await password_message.delete()
            except: pass
            
            processing_message = await ctx.send(f"認証成功。データ更新を開始します...\n(数分かかる場合があります)")

            try:
                # 1. スクレイピングスクリプトを実行
                process = await asyncio.to_thread(
                    subprocess.run,
                    ['python', self.scraper_script_to_execute],
                    capture_output=True,
                    text=True,
                    check=False,
                    encoding='utf-8'
                )
                
                if process.returncode != 0:
                    error_output = process.stderr if process.stderr else "詳細は不明"
                    await processing_message.edit(content=f"スクリプト実行エラー (Code: {process.returncode})\n```\n{error_output[:1000]}\n```")
                    print(f"[Error] Script failed:\n{process.stderr}")
                    return

                # 2. JSON読み込み確認
                try:
                    with open(self.json_to_load, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.scraped_data = data
                except Exception as e:
                    await processing_message.edit(content=f"JSON読み込みエラー: {e}")
                    return

                # 3. Unite Cog のデータをリロード
                unite_cog = self.bot.get_cog('Unite')
                
                if unite_cog:
                    if hasattr(unite_cog, 'load_pokemon_list'):
                        unite_cog.load_pokemon_list()
                        await processing_message.edit(content=f"**更新完了！**\n最新のデータ({len(unite_cog.pokemon_list)}件)が反映されました。")
                        print("Unite Cog reloaded successfully.")
                    else:
                        await processing_message.edit(content="Unite Cogは見つかりましたが、データ読み込みメソッドが見つかりません。")
                else:
                    await processing_message.edit(content="JSONは更新されましたが、Unite Cogが見つからないためBot上のリストは更新されませんでした。")

            except Exception as e:
                await processing_message.edit(content=f"予期せぬエラー: {e}")
                import traceback
                traceback.print_exc()
        else:
            await ctx.send("パスワードが間違っています。")

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageDataCog(bot))