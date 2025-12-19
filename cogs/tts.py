import discord
from discord.ext import commands
import aiohttp
import os
import asyncio
import uuid
import logging
import shutil
from typing import Optional

# Docker環境で動かす場合のデフォルトを voicevox サービス名にする
VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://voicevox:50021")
SPEAKER_ID = int(os.getenv("SPEAKER_ID", "3"))

logger = logging.getLogger("tts")

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ffmpeg の有無をログに出しておく
        has_ffmpeg = shutil.which("ffmpeg") is not None
        if not has_ffmpeg:
            logger.warning("ffmpeg が見つかりません。音声再生が失敗する可能性があります。")
        # 最近送った通知のデデュープ用キャッシュ: (guild_id, message_text) -> timestamp
        self._recent_notifications: dict[tuple[int, str], float] = {}
        # 通知の重複判定ウィンドウ（秒）
        # 重複通知ウィンドウ（秒）: デフォルトを 5 秒にして誤検知を減らす
        self._notification_window = float(os.getenv("NOTIFY_DEDUP_WINDOW", "5.0"))

    async def _send_once(self, ctx_or_channel, text: str, guild_id: int):
        """短時間に同じメッセージを2回送らないためのヘルパー。ctx か channel を受け取る"""
        import time
        key = (guild_id, text)
        now = time.time()
        last = self._recent_notifications.get(key)
        if last and (now - last) < self._notification_window:
            logger.debug("Skip duplicate notification for %s: %s", guild_id, text)
            return
        self._recent_notifications[key] = now
        # クリーンアップ（古いエントリを削除）
        for k, t in list(self._recent_notifications.items()):
            if now - t > (self._notification_window * 5):
                del self._recent_notifications[k]

        if isinstance(ctx_or_channel, str):
            # raw チャンネル名（使わないが保険）
            return
        # ctx を渡された場合
        if hasattr(ctx_or_channel, "send"):
            await ctx_or_channel.send(text)
        else:
            # discord.Channel オブジェクト
            await ctx_or_channel.send(text)

    @commands.command()
    async def join(self, ctx: commands.Context):
        """ボイスチャンネルに参加（重複送信を防ぐため接続状態をチェック、リトライあり）"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await self._send_once(ctx, "先にボイスチャンネルに入ってください", ctx.guild.id)
            return

        channel = ctx.author.voice.channel
        # 既に接続済みなら一回だけメッセージを返す
        vc = ctx.guild.voice_client
        if vc and vc.is_connected():
            # 同じチャンネルなら既に接続済みとして報告、別チャンネルなら移動
            if vc.channel and vc.channel.id == channel.id:
                await self._send_once(ctx, f"既にボイスチャンネル「{channel.name}」に接続しています。", ctx.guild.id)
                return
            else:
                # 別チャンネルに接続中なら移動する
                try:
                    await vc.move_to(channel)
                    await self._send_once(ctx, f"ボイスチャンネルを「{channel.name}」に移動しました。", ctx.guild.id)
                    return
                except Exception:
                    logger.exception("Failed to move voice client to %s", channel.name)
                    await self._send_once(ctx, "ボイスチャンネルへの移動に失敗しました。ログを確認してください。", ctx.guild.id)
                    return

        # 未接続なら接続を試みる（短いリトライを行う）
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug("Attempting to connect to %s (attempt %d)", channel.name, attempt)
                await channel.connect()
                logger.debug("channel.connect() completed (attempt %d)", attempt)
                break
            except Exception as e:
                # 例外が出た場合でも短時間待って接続状態を再確認する（内部で成功していることがあるため）
                await asyncio.sleep(0.4)
                vc_check = ctx.guild.voice_client
                if vc_check and vc_check.is_connected() and vc_check.channel and vc_check.channel.id == channel.id:
                    # 接続が実際には成功していた場合は、例外はログのみに留めずユーザ通知は行わない
                    logger.info("Connect succeeded despite exception (suppressed error): %s", e)
                    break

                # 接続が成功していない場合はリトライまたは最終失敗として扱う
                if attempt < max_attempts:
                    logger.debug("Attempt %d failed (will retry): %s", attempt, e)
                    await asyncio.sleep(0.5)
                    continue

                # 最終失敗: ここで初めてエラーログを残してユーザに通知する
                logger.exception("Final failure connecting to voice channel %s after %d attempts", channel.name, attempt)
                await self._send_once(ctx, "ボイスチャンネルへの接続に失敗しました。ログを確認してください。", ctx.guild.id)
                return

        # 接続に成功したことを確認してからメッセージを送る
        # 少し待ってから再確認して、状態反映遅延での誤報を防ぐ
        await asyncio.sleep(0.2)
        vc_after = ctx.guild.voice_client
        if vc_after and vc_after.is_connected() and vc_after.channel and vc_after.channel.id == channel.id:
            logger.debug("Confirmed connected to %s", channel.name)
            await self._send_once(ctx, f"ボイスチャンネル「{channel.name}」に接続しました！", ctx.guild.id)
        else:
            logger.debug("Connection not fully established on check; sending fallback message")
            await self._send_once(ctx, "接続処理が完了しました（状態の確認に時間がかかる場合があります）。", ctx.guild.id)

    @commands.command()
    async def leave(self, ctx: commands.Context):
        """ボイスチャンネルから退出（重複送信を防ぐ）"""
        vc = ctx.guild.voice_client
        if not vc or not vc.is_connected():
            await self._send_once(ctx, "ボイスチャンネルに接続していません", ctx.guild.id)
            return

        # 切断を試みる
        try:
            logger.debug("Attempting to disconnect from %s", getattr(vc.channel, 'name', None))
            await vc.disconnect()
        except Exception as e:
            # 一時的な反映遅延で既に切断されていることがあるため短時間待って確認
            await asyncio.sleep(0.2)
            vc_check = ctx.guild.voice_client
            if not vc_check or not vc_check.is_connected():
                # 切断済みと判定された場合は例外は抑制し、成功メッセージのみ送る
                logger.info("Disconnect exception suppressed because client is already disconnected: %s", e)
                await self._send_once(ctx, "ボイスチャンネルから退出しました！", ctx.guild.id)
                return

            # まだ接続が残っている場合は例外としてログと通知を行う
            logger.exception("Failed to disconnect from voice channel %s: %s", getattr(vc.channel, 'name', None), e)
            await self._send_once(ctx, "ボイスチャンネルからの退出に失敗しました。ログを確認してください。", ctx.guild.id)
            return

        # 切断後の状態確認（状態反映の遅延に備える）
        await asyncio.sleep(0.2)
        vc_after = ctx.guild.voice_client
        if not vc_after or not vc_after.is_connected():
            await self._send_once(ctx, "ボイスチャンネルから退出しました！", ctx.guild.id)
        else:
            await self._send_once(ctx, "退出処理が完了しました（状態の確認に時間がかかる場合があります）。", ctx.guild.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
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

            # コマンドかどうかは Context を解析して判定する（より正確）
            try:
                ctx = await self.bot.get_context(message)
                is_command = ctx.command is not None
            except Exception:
                is_command = False

            if is_command:
                logger.debug("Skipping TTS for command message: %s", message.content)
            elif vc_channel_name == text_channel_name:
                logger.info(f"Speaking message from #{text_channel_name} in VC {vc_channel_name}: {message.content!r}")
                await self.speak_text(vc, message.content)
            else:
                logger.debug(f"Message in #{text_channel_name} ignored (VC is {vc_channel_name}).")

        # commands の処理を止めない
        try:
            await self.bot.process_commands(message)
        except Exception:
            logger.exception("Error processing commands for message")

    @commands.command()
    async def say(self, ctx: commands.Context, *, text: str):
        """手動でテキストを読み上げる（テスト用）"""
        # VC につながっていなければ接続を試みる
        vc = ctx.guild.voice_client
        if not vc or not vc.is_connected():
            if ctx.author.voice and ctx.author.voice.channel:
                await ctx.author.voice.channel.connect()
                vc = ctx.guild.voice_client
            else:
                await ctx.send("まずボイスチャンネルに接続してください。")
                return

        await ctx.send("読み上げを開始します...")
        await self.speak_text(vc, text)

    async def speak_text(self, vc: discord.VoiceClient, text: str):
        """VOICEVOXで音声を生成しVCで再生（非同期）"""
        logger.info("読み上げ開始: %s", text)

        params = {"text": text, "speaker": SPEAKER_ID}
        filename = f"voice_{uuid.uuid4().hex}.wav"

        try:
            async with aiohttp.ClientSession() as session:
                # 1. audio_query
                async with session.post(f"{VOICEVOX_URL}/audio_query", params=params) as res1:
                    if res1.status != 200:
                        logger.error("audio_query failed: %s", res1.status)
                        return
                    query = await res1.json()

                # 2. synthesis
                async with session.post(f"{VOICEVOX_URL}/synthesis", params=params, json=query) as res2:
                    if res2.status != 200:
                        logger.error("synthesis failed: %s", res2.status)
                        return
                    data = await res2.read()

            # ファイル書き込み
            with open(filename, "wb") as f:
                f.write(data)

            # 他の再生が終わるのを待つ
            while vc.is_playing():
                await asyncio.sleep(0.5)

            # 再生
            loop = asyncio.get_running_loop()
            def _after(err: Optional[Exception]):
                if err:
                    logger.error("Playback error: %s", err)
                # スレッドセーフにファイル削除をスケジュール
                try:
                    loop.call_soon_threadsafe(self.cleanup, filename)
                except Exception:
                    logger.exception("Failed to schedule cleanup for %s", filename)

            source = discord.FFmpegPCMAudio(filename, executable="ffmpeg", options=["-hide_banner", "-loglevel", "error"])
            vc.play(source, after=_after)
            logger.info("再生開始: %s", filename)

        except Exception as e:
            logger.exception("TTS error: %s", e)
            # 念のためファイルを削除
            self.cleanup(filename)

    def cleanup(self, filename: str):
        """再生終わったファイルを削除"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                logger.debug("Removed temporary file %s", filename)
        except Exception:
            logger.exception("Failed to remove file %s", filename)

async def setup(bot: commands.Bot):
    await bot.add_cog(TTS(bot))
