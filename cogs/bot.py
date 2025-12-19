import discord
from discord.ext import commands, tasks
import asyncpg
import traceback
import datetime
import zoneinfo
import logging

logger = logging.getLogger(__name__)

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
                f"各コマンドの説明: !help <コマンド名>\n"
                f"各カテゴリの説明: !help <カテゴリ名>\n")

# ------------------------------------------------------------------
# Bot本体のクラス定義
# ------------------------------------------------------------------
class MyBot(commands.Bot):
    def __init__(self, command_prefix, DSN):
        super().__init__(
            command_prefix=command_prefix,
            intents=discord.Intents.all(),
            help_command=JapaneseHelpCommand()
        )
        self.dsn = DSN
        self.pool = None
        # タイムゾーンはここで定義しておくと便利
        self.jst = zoneinfo.ZoneInfo('Asia/Tokyo') 

    async def setup_hook(self):
        """
        Bot起動時に最初に実行される処理。
        ここでCog（機能拡張）をロードします。
        """
        logger.info("--- Setup Hook Started ---")

        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
            logger.info("[OK] Database connection pool created.")
        except Exception:
            logger.exception("[ERROR] Failed to connect to database")
        # ロードしたいCogのリスト
        # ※ ファイル名が正しいか必ず確認してください (大文字小文字など)
        initial_extensions = [
            "cogs.romazi_to_hiragana",  # ← これを上に移動！

            "cogs.Pokeconf",
            "cogs.SQL",
            "cogs.HOME",
            "cogs.Func",
            "cogs.Role",
            "cogs.Wordle",
            "cogs.cmd_card",
            "cogs.tts",
            "cogs.unite_info", 
            "cogs.unite",
            "cogs.reaction",
            "cogs.Greet",
            "cogs.Game",
            "cogs.batteledata_commit",
            "cogs.manage_unite_data"
        ]

        logger.info("--- Cog Loading Started ---")
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"[OK] Loaded extension: {extension}")
            except commands.ExtensionAlreadyLoaded:
                logger.warning(f"[SKIP] Already loaded: {extension}")
            except commands.ExtensionNotFound:
                logger.error(f"[ERROR] Cog not found: {extension}")
            except commands.NoEntryPointError:
                logger.error(f"[ERROR] No setup function in: {extension}")
            except Exception:
                logger.exception(f"[ERROR] Failed to load {extension}")
        logger.info("--- Cog Loading Finished ---")

    async def close(self):
        """Bot終了時の処理"""
        # ★追加: 終了時にDB接続を閉じる
        if self.pool:
            await self.pool.close()
            logger.info("[INFO] Database connection closed.")
        await super().close()

        # スラッシュコマンドの同期 (必要に応じてコメントアウトを外す)
        # 開発中は特定のギルドのみに同期したほうが早いですが、
        # ここではグローバル同期の例を書いておきます。
        # try:
        #     synced = await self.tree.sync()
        #     print(f"Synced {len(synced)} slash commands.")
        # except Exception as e:
        #     print(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        """起動完了時の処理"""
        # 親クラス(commands.Bot)のon_readyがあれば呼ぶ（通常は不要だが念のため）
        # await super().on_ready()
        
        # ログイン情報の表示などは main.py の on_ready に任せてもいいが、
        # タスクの起動はここで行うのが確実
        if not self.update_pokemon_home_database.is_running():
            self.update_pokemon_home_database.start()
            logger.info("[TASK] Pokémon HOME database update task started.")

    # ------------------------------------------------------------------
    # ユーティリティ & タスク
    # ------------------------------------------------------------------

    @tasks.loop(seconds=86400)
    async def update_pokemon_home_database(self):
        """24時間ごとに実行される定期タスク"""
        now = datetime.datetime.now(self.jst).strftime('%y/%m/%d %H:%M:%S')
        
        battledata_cog = self.get_cog('BatteledataCommit')
        
        if battledata_cog:
            try:
                logger.info(f"{now} - Starting periodic Pokémon HOME DB update...")
                # ★注意: battledata_cog の中身も asyncpg に対応させる必要があります
                await battledata_cog.run_update_logic()
                logger.info(f"{now} - Update completed successfully.")
            except Exception:
                logger.exception("Error during periodic update")
        else:
            logger.warning(f"{now} - [WARNING] Cog 'BatteledataCommit' not found. Task skipped.")

    @update_pokemon_home_database.before_loop
    async def before_update_pokemon_home_database(self):
        await self.wait_until_ready()

    # ------------------------------------------------------------------
    # エラーハンドリング
    # ------------------------------------------------------------------

    async def on_command_error(self, ctx: commands.Context, error):
        """
        グローバルエラーハンドリング
        Botクラス直下の場合は @commands.Cog.listener は不要で、
        メソッド名が一致していればオーバーライドされます。
        """
        # コマンドが見つからないエラーは無視する（頻発するため）
        if isinstance(error, commands.CommandNotFound):
            return

        # Embedでのエラー表示
        embed = discord.Embed(
            title="ERROR!",
            description=f"```{ctx.message.content}```",
            color=0xff0000
        )
        embed.add_field(
            name="Detail",
            value=f"```{error}```",
            inline=False
        )
        embed.add_field(
            name="Help",
            value=f"Type `!help {ctx.command}` for details.",
            inline=False
        )
        
        # 権限不足などでメッセージが送れない場合のエラーを避けるtry-except
        try:
            await ctx.send(embed=embed, delete_after=120)
        except discord.Forbidden:
            logger.warning(f"Cannot send error message to {ctx.channel}: {error}")