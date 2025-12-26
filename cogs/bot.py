import discord
from discord.ext import commands, tasks
import asyncpg
import traceback
import datetime
import zoneinfo
import logging
import asyncio

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
    # ★変更点1: testing_guild_id を受け取るように変更
    def __init__(self, command_prefix, DSN, testing_guild_id=None):
        super().__init__(
            command_prefix=command_prefix,
            intents=discord.Intents.all(),
            help_command=JapaneseHelpCommand()
        )
        self.dsn = DSN
        self.testing_guild_id = testing_guild_id # IDを保存
        self.pool = None
        # タイムゾーンはここで定義しておくと便利
        self.jst = zoneinfo.ZoneInfo('Asia/Tokyo') 

    async def setup_hook(self):
        """
        Bot起動時（ログイン直後、接続前）に1回だけ実行される処理。
        Cogのロードとコマンド同期はここで行うのがベストプラクティス。
        """
        logger.info("--- Setup Hook Started ---")

        # 1. データベース接続
        for i in range(5):  # 5回まで挑戦
            try:
                self.pool = await asyncpg.create_pool(dsn=self.dsn)
                self.db = self.pool
                logger.info("[OK] Database connection pool created.")
                break
            except Exception as e:
                logger.warning(f"[RETRY] Database connection failed ({i+1}/5). Retrying in 5s... Error: {e}")
                await asyncio.sleep(5)
        else:
            logger.error("[ERROR] Could not connect to database after retries.")

        # 2. Cog（機能拡張）のロード
        initial_extensions = [
            "cogs.romazi_to_hiragana", 

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
            # "cogs.battledata_commit",
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

        # 3. コマンド同期 (Sync)
        # setup_hook内で実行することで、再接続時の無駄なSyncを防ぐ
        logger.info("--- Command Sync Started ---")
        try:
            if self.testing_guild_id:
                guild_obj = discord.Object(id=int(self.testing_guild_id))
                self.tree.copy_global_to(guild=guild_obj)
                await self.tree.sync(guild=guild_obj)
                logger.info(f"[SYNC] Command tree synced to SPECIFIC guild: {self.testing_guild_id} (Dev Mode)")
            else:
                await self.tree.sync()
                logger.info("[SYNC] Command tree synced GLOBALLY (Production Mode)")
        except Exception as e:
            logger.error(f"[ERROR] Failed to sync command tree: {e}")
        
        logger.info("--- Setup Hook Finished ---")

    async def close(self):
        """Bot終了時の処理"""
        if self.pool:
            await self.pool.close()
            logger.info("[INFO] Database connection closed.")
        await super().close()

    async def on_ready(self):
        """起動完了時の処理（タスク開始など）"""
        # ここではもう sync は行わない
        
        if not self.update_pokemon_home_database.is_running():
            self.update_pokemon_home_database.start()
            logger.info("[TASK] Pokémon HOME database update task started.")

    # ------------------------------------------------------------------
    # ユーティリティ & タスク
    # ------------------------------------------------------------------

    # @tasks.loop(seconds=86400)
    # async def update_pokemon_home_database(self):
    #     """24時間ごとに実行される定期タスク"""
    #     now = datetime.datetime.now(self.jst).strftime('%y/%m/%d %H:%M:%S')
        
    #     battledata_cog = self.get_cog('BattledataCommit')
        
    #     if battledata_cog:
    #         try:
    #             logger.info(f"{now} - Starting periodic Pokémon HOME DB update...")
    #             await battledata_cog.run_update_logic()
    #             logger.info(f"{now} - Update completed successfully.")
    #         except Exception:
    #             logger.exception("Error during periodic update")
    #     else:
    #         logger.warning(f"{now} - [WARNING] Cog 'BattledataCommit' not found. Task skipped.")

    # @update_pokemon_home_database.before_loop
    # async def before_update_pokemon_home_database(self):
    #     await self.wait_until_ready()

    # ------------------------------------------------------------------
    # エラーハンドリング
    # ------------------------------------------------------------------

    async def on_command_error(self, ctx: commands.Context, error):
        """グローバルエラーハンドリング"""
        if isinstance(error, commands.CommandNotFound):
            return

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
        
        try:
            await ctx.send(embed=embed, delete_after=120)
        except discord.Forbidden:
            logger.warning(f"Cannot send error message to {ctx.channel}: {error}")