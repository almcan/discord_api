import discord
import asyncio
import os
import logging
import sys
from dotenv import load_dotenv

# 自作クラスのインポート
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
logger = logging.getLogger(__name__)  # "main" ではなく __name__ を使うのが一般的

# ------------------------------------------------------------------
# 2. 設定値の取得 (Fail Fast)
# ------------------------------------------------------------------

TOKEN = os.getenv('DISCORD_TOKEN')
DSN = os.getenv('DSN')
GUILD_ID = os.getenv('GUILD_ID') # 開発用サーバーID（あれば）
PREFIX = os.getenv('PREFIX', '!')

if TOKEN is None:
    logger.critical("環境変数 'DISCORD_TOKEN' が設定されていません。終了します。")
    sys.exit(1)
if DSN is None:
    logger.critical("環境変数 'DSN' が設定されていません。終了します。")
    sys.exit(1)

# ------------------------------------------------------------------
# 3. Botの初期化
# ------------------------------------------------------------------

bot = MyBot(command_prefix=PREFIX, DSN=DSN, testing_guild_id=GUILD_ID)

# ------------------------------------------------------------------
# 4. コマンド定義 (必要最低限)
# ------------------------------------------------------------------

@bot.command()
async def ping(ctx):
    """ヘルスチェック用コマンド"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')
    logger.info(f"Ping command executed by {ctx.author}")

# ------------------------------------------------------------------
# 5. 起動プロセス
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
        # KeyboardInterrupt は Docker停止時にも送られるシグナル
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is shutting down...")