import asyncio
import os
import logging
import discord
from dotenv import load_dotenv

# 自作クラスのインポート
# (cogsフォルダの中に bot.py を作り、そこに MyBotクラス を書きます)
from cogs.bot import MyBot

# ------------------------------------------------------------------
# 1. 前準備: 環境変数の読み込みとログ設定
# ------------------------------------------------------------------

load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("main")

# ------------------------------------------------------------------
# 2. 設定値の取得 (Fail Fast)
# ------------------------------------------------------------------

TOKEN = os.getenv('DISCORD_TOKEN')
DSN = os.getenv('DSN')
GUILD_ID = os.getenv('GUILD_ID')
PREFIX = os.getenv('COMMAND_PREFIX')  # .envに合わせて修正

# 必須変数がなければ即死させる
if TOKEN is None:
    logger.critical("環境変数 'DISCORD_TOKEN' が設定されていません。終了します。")
    exit(1)
if DSN is None:
    logger.critical("環境変数 'DSN' が設定されていません。終了します。")
    exit(1)

# ------------------------------------------------------------------
# 3. Botの初期化とイベント定義
# ------------------------------------------------------------------

# MyBotクラスに設定を渡して初期化
bot = MyBot(command_prefix=PREFIX, dsn=DSN, guild_id=GUILD_ID)

@bot.event
async def on_ready():
    """Bot起動完了時の処理"""
    logger.info("--------------------------------------------------")
    logger.info(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Target Guild ID: {GUILD_ID}')
    logger.info(f'Database DSN: {DSN[:10]}... (masked)')
    logger.info("--------------------------------------------------")

    # コマンド同期 (Slash Commands用)
    try:
        if hasattr(bot, 'tree'):
            # 開発中は特定のギルドだけで即時同期すると早い
            if GUILD_ID:
                guild = discord.Object(id=int(GUILD_ID))
                bot.tree.copy_global_to(guild=guild)
                await bot.tree.sync(guild=guild)
                logger.info(f"Command tree synced to guild {GUILD_ID}.")
            else:
                await bot.tree.sync()
                logger.info("Command tree synced globally.")
    except Exception as e:
        logger.error(f"Failed to sync command tree: {e}")

@bot.command()
async def ping(ctx):
    """ヘルスチェック用コマンド"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')
    logger.info(f"Ping command executed by {ctx.author}")

# ------------------------------------------------------------------
# 4. 起動プロセス
# ------------------------------------------------------------------

async def main():
    try:
        async with bot:
            await bot.start(TOKEN)
    except discord.LoginFailure:
        logger.critical("ログインに失敗しました。トークンを確認してください。")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is shutting down...")