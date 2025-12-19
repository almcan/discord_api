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

# ローカル実行時用: .envファイルがあれば読み込む
load_dotenv()

# ログ設定: print()の代わりにこれを使う
# Dockerのログ機能(STDOUT)と相性が良く、タイムスタンプも付く
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # 標準出力に流す
)
logger = logging.getLogger("main")

# ------------------------------------------------------------------
# 2. 設定値の取得 (Fail Fast原則)
# ------------------------------------------------------------------

TOKEN = os.getenv('DISCORD_TOKEN')
DSN = os.getenv('DSN')
GUILD_ID = os.getenv('GUILD_ID')
PREFIX = os.getenv('PREFIX', '!')

# 必須環境変数がない場合は、起動せずに即死させる（中途半端に動かさない）
if TOKEN is None:
    logger.critical("環境変数 'DISCORD_TOKEN' が設定されていません。終了します。")
    sys.exit(1)
if DSN is None:
    logger.critical("環境変数 'DSN' が設定されていません。終了します。")
    sys.exit(1)

# ------------------------------------------------------------------
# 3. Botの初期化
# ------------------------------------------------------------------

# MyBotクラスにDSNなどを渡す
bot = MyBot(command_prefix=PREFIX, DSN=DSN)

# ------------------------------------------------------------------
# 4. イベント定義
# ------------------------------------------------------------------

@bot.event
async def on_ready():
    """Bot起動完了時の処理（コマンド同期改良版）"""
    logger.info("--------------------------------------------------")
    logger.info(f'Logged in as: {bot.user.name} (ID: {bot.user.id})')
    
    try:
        if hasattr(bot, 'tree'):
            # GUILD_IDが.envに設定されている場合（開発モード: 即時反映）
            if GUILD_ID:
                guild_obj = discord.Object(id=int(GUILD_ID))
                
                # グローバルコマンドとして定義したものを、開発用サーバーにコピーして登録
                bot.tree.copy_global_to(guild=guild_obj)
                
                # 特定サーバーのみ同期実行
                await bot.tree.sync(guild=guild_obj)
                logger.info(f"✅ Command tree synced to SPECIFIC guild: {GUILD_ID} (Dev Mode)")
            
            # GUILD_IDがない場合（本番モード: 反映に最大1時間かかる場合あり）
            else:
                await bot.tree.sync()
                logger.info("🌎 Command tree synced GLOBALLY (Production Mode)")
        
        else:
            logger.warning("bot.tree not found. Skipping sync.")
            
    except Exception as e:
        logger.error(f"❌ Failed to sync command tree: {e}")

    logger.info("--------------------------------------------------")

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
        # トークンでログインして開始
        async with bot:
            await bot.start(TOKEN)
    except discord.LoginFailure:
        logger.critical("ログインに失敗しました。トークンを確認してください。")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")

if __name__ == '__main__':
    try:
        # KeyboardInterrupt (Ctrl+C) はDocker停止時にも送られるシグナル
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is shutting down...")