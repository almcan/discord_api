import discord
from discord.ext import commands
import requests
import os
import asyncio 

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")  # VOICEVOXエンジンのURL
SPEAKER_ID = 3  # ずんだもん（あまあま）

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """ボイスチャンネルに参加"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"ボイスチャンネル「{channel.name}」に接続しました！")
        else:
            await ctx.send("先にボイスチャンネルに入ってください")

    @commands.command()
    async def leave(self, ctx):
        """ボイスチャンネルから退出"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("ボイスチャンネルから退出しました！")
        else:
            await ctx.send("ボイスチャンネルに接続していません")

    @commands.Cog.listener()
    async def on_message(self, message):
        """VCと同じ名前のテキストチャンネルのメッセージを読み上げ"""
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=guild)
        if vc and vc.is_connected():
            vc_channel_name = vc.channel.name if vc.channel else None
            text_channel_name = message.channel.name

            if vc_channel_name == text_channel_name:
                await self.speak_text(vc, message.content)

    async def speak_text(self, vc, text):
        """VOICEVOXで音声を生成しVCで再生"""
        print(f"読み上げ開始: {text}")

        params = {"text": text, "speaker": SPEAKER_ID}
        
        # 音声クエリ作成
        res1 = requests.post(f"{VOICEVOX_URL}/audio_query", params=params)
        if res1.status_code != 200:
            print(f"音声クエリ作成失敗: {res1.status_code}")
            return
        query = res1.json()

        # 音声合成
        res2 = requests.post(f"{VOICEVOX_URL}/synthesis", params=params, json=query)
        if res2.status_code != 200:
            print(f"音声合成失敗: {res2.status_code}")
            return

        filename = "zundamon_voice.wav"
        with open(filename, "wb") as f:
            f.write(res2.content)

        if vc.is_playing():
            print("再生待機中（既に音声を再生中）")
            while vc.is_playing():
                await asyncio.sleep(1)

        # ffmpegのパスを指定
        vc.play(discord.FFmpegPCMAudio(filename, executable="ffmpeg", options="-loglevel quiet"), after=lambda e: os.remove(filename))

async def setup(bot):
    await bot.add_cog(TTS(bot))
