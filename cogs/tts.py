import discord
from discord.ext import commands
import aiohttp
import os
import asyncio
import uuid
import json

# Docker Composeで設定した環境変数を読み込む
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://voicevox:50021")
SPEAKER_ID = 3  # 3: ずんだもん（ノーマル/あまあま）

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
            await ctx.send("退出しました")
        else:
            await ctx.send("接続していません")

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージが来たら読み上げる"""
        if message.author.bot:
            return

        guild = message.guild
        if not guild:
            return

        # ボットがVCにいるか確認
        vc = guild.voice_client
        if vc and vc.is_connected():
            # 【条件】VCの名前と、テキストチャンネルの名前が同じなら読む
            # （条件を外したければ、ここを削除してインデントを戻せばOK）
            vc_channel_name = vc.channel.name
            text_channel_name = message.channel.name

            if vc_channel_name == text_channel_name:
                await self.speak_text(vc, message.content)

    async def speak_text(self, vc, text):
        """VOICEVOX APIを叩いて音声を再生"""
        
        # 連続で来てもファイルが被らないように、ランダムな名前を作る
        filename = f"voice_{uuid.uuid4()}.wav"

        params = {"text": text, "speaker": SPEAKER_ID}

        try:
            async with aiohttp.ClientSession() as session:
                # 1. 音声合成用のクエリを作成 (audio_query)
                async with session.post(f"{VOICEVOX_URL}/audio_query", params=params) as res1:
                    if res1.status != 200:
                        print(f"Query Error: {res1.status}")
                        return
                    query = await res1.json()

                # 2. 音声合成を実行 (synthesis)
                async with session.post(f"{VOICEVOX_URL}/synthesis", params=params, json=query) as res2:
                    if res2.status != 200:
                        print(f"Synthesis Error: {res2.status}")
                        return
                    
                    # 音声データをファイルに保存
                    with open(filename, "wb") as f:
                        f.write(await res2.read())

            # 3. 再生キュー処理
            while vc.is_playing():
                await asyncio.sleep(0.5)

            # 4. 再生
            vc.play(
                discord.FFmpegPCMAudio(filename),
                after=lambda e: self.cleanup(filename)
            )
            print(f"再生開始: {text}")

        except Exception as e:
            print(f"TTS Error: {e}")
            self.cleanup(filename)

    def cleanup(self, filename):
        """再生終わったファイルを削除"""
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def setup(bot):
    await bot.add_cog(TTS(bot))