import discord
from discord.ext import commands
import aiohttp  # requestsの代わりにこれを使用
import os
import asyncio
import uuid  # ファイル名被り防止用

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
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
        """VOICEVOXで音声を生成しVCで再生（非同期・UUID対応版）"""
        
        params = {"text": text, "speaker": SPEAKER_ID}
        
        # 非同期セッションの開始
        async with aiohttp.ClientSession() as session:
            # 1. 音声クエリ作成 (Audio Query)
            async with session.post(f"{VOICEVOX_URL}/audio_query", params=params) as res1:
                if res1.status != 200:
                    print(f"音声クエリ作成失敗: {res1.status}")
                    return
                query = await res1.json()

            # 2. 音声合成 (Synthesis)
            async with session.post(f"{VOICEVOX_URL}/synthesis", params=params, json=query) as res2:
                if res2.status != 200:
                    print(f"音声合成失敗: {res2.status}")
                    return
                audio_data = await res2.read()

        # 3. 音声ファイルの保存（UUIDでファイル名重複を回避）
        filename = f"tts_{uuid.uuid4()}.wav"

        with open(filename, "wb") as f:
            f.write(audio_data)

        # 既に再生中なら待機
        while vc.is_playing():
            await asyncio.sleep(1)

        # 4. 再生 & 再生終了後に削除
        vc.play(
            discord.FFmpegPCMAudio(filename, executable="ffmpeg", options="-loglevel quiet"),
            after=lambda e: self.cleanup(filename)
        )

    def cleanup(self, filename):
        """再生終了後にファイルを削除するコールバック"""
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"ファイル削除エラー: {e}")

async def setup(bot):
    await bot.add_cog(TTS(bot))