import discord
from discord.ext import commands, tasks
import asyncpg
import traceback
import datetime
import zoneinfo

# ------------------------------------------------------------------
# ヘルプコマンドのカスタマイズクラス
# ------------------------------------------------------------------
class JapaneseHelpCommand(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = "その他"
        self.command_attrs["help"] = "コマンド一覧と簡単な説明を表示します"

    def get_ending_note(self):
        return (f"より詳細な説明を得るには：\n"
                f"各コマンドの説明: {self.context.prefix}help <コマンド名>\n"
                f"各カテゴリの説明: {self.context.prefix}help <カテゴリ名>\n")

# ------------------------------------------------------------------
# Bot本体のクラス定義
# ------------------------------------------------------------------
class MyBot(commands.Bot):
    def __init__(self, command_prefix, dsn, guild_id):
        super().__init__(
            command_prefix=command_prefix,
            intents=discord.Intents.all(),
            help_command=JapaneseHelpCommand()
        )
        self.dsn = dsn
        self.target_guild_id = guild_id # main.pyから渡されたGUILD_ID
        self.pool = None
        self.jst = zoneinfo.ZoneInfo('Asia/Tokyo') 

    async def setup_hook(self):
        print("--- Setup Hook Started ---")

        # データベース接続 (DSNがダミーだと失敗しますが、tryで守られているので落ちません)
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
            print("[OK] Database connection pool created.")
        except Exception as e:
            print(f"[WARNING] Failed to connect to database: {e}")
            # DBがないと動かない機能がある場合はここで処理を止めるか検討する

        # ロードしたいCogのリスト
        # ★今の環境にあるファイル名に合わせて調整しました
        initial_extensions = [
            "cogs.tts",

        ]

        print(f"--- Cog Loading Started ---")
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"[OK] Loaded extension: {extension}")
            except Exception as e:
                print(f"[ERROR] Failed to load {extension}")
                traceback.print_exc()
        print(f"--- Cog Loading Finished ---")

    async def close(self):
        """Bot終了時の処理"""
        if self.pool:
            await self.pool.close()
            print("[INFO] Database connection closed.")
        await super().close()

    async def on_ready(self):
        # 起動確認
        print("--------------------------------------------------")
        print(f'Logged in as: {self.user.name} (ID: {self.user.id})')
        print("--------------------------------------------------")

    # ------------------------------------------------------------------
    # エラーハンドリング
    # ------------------------------------------------------------------
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            return

        embed = discord.Embed(
            title="ERROR!",
            description=f"```{ctx.message.content}```",
            color=0xff0000
        )
        embed.add_field(name="Detail", value=f"```{error}```", inline=False)
        
        try:
            await ctx.send(embed=embed, delete_after=120)
        except discord.Forbidden:
            pass