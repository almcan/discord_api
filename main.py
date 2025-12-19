import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# .envファイルからトークンを読み込む
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 【重要】インテントの設定
# これがないとボットはメッセージの中身を読めません
intents = discord.Intents.default()
intents.message_content = True 

# ボットの作成（コマンドの頭に ! をつけると反応する設定）
bot = commands.Bot(command_prefix='!', intents=intents)

# 起動したときのイベント
@bot.event
async def on_ready():
    print(f'ログインしました: {bot.user}')
    print('------')

# コマンド: !ping と打つと Pong! と返す
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# 実行
if TOKEN:
    bot.run(TOKEN)
else:
    print("エラー: .envファイルにトークンが見つかりません")