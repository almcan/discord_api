import discord
from discord.ext import commands
from discord.ext.commands.errors import (
    BadArgument,
    TooManyArguments,
    MissingRequiredArgument,
    CommandOnCooldown
)
import random
import pandas as pd
from tabulate import tabulate
import asyncio
import os

class Func(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 共通ユーティリティ: データフレーム表示 ---
    async def df2out(self, ctx, df, column=[], tablefmt="plain"):
        table = tabulate(
            tabular_data=df,
            headers=column,
            stralign="left",
            numalign="right",
            showindex=True,
            tablefmt=tablefmt
        )
        await ctx.send(f"```\n{table}```")

    # ==================================================
    # 機能1: シャッフル
    # ==================================================
    @commands.command(name="shuffle", description="!shuffle 並び替える単語群")
    async def shuffle(self, ctx: commands.Context, *, word: str = commands.parameter(description="並び替える単語群")):
        """
        与えられた複数の単語や数字をランダムに並び替えます
        """
        l = word.split()
        l_shuffled = random.sample(l, len(l))
        df = pd.DataFrame(l_shuffled, columns=["Result"])
        df.index += 1
        await self.df2out(ctx, df)

    # ==================================================
    # 機能2: ダイス (Game.py統合)
    # ==================================================
    @commands.command(name="dice", description="!dice ダイス数 目の数")
    @commands.cooldown(rate=2, per=60, type=commands.BucketType.guild)
    async def dice(self, ctx: commands.Context, a: int, b: int):
        """サイコロを振る (例: !dice 2 6 -> 6面ダイスを2個)"""
        result = random.choices(range(1, b + 1), k=a)
        return await ctx.send(
            f'{a}D{b}の結果は{sum(result)}です．\n内訳{result}'
        )

    @dice.error
    async def on_dice_error(self, ctx: commands.Context, error):
        if isinstance(error, BadArgument):
            return await ctx.send('引数はいずれも整数です')
        if isinstance(error, MissingRequiredArgument):
            return await ctx.send('引数は2つ必要です')
        if isinstance(error, TooManyArguments):
            return await ctx.send('必要な引数は2つのみです')
        if isinstance(error, CommandOnCooldown):
            return await ctx.send('1分間に2回までです')

    # ==================================================
    # 機能3: 挨拶 (Greet.py統合)
    # ==================================================
    @commands.command(name="greet", description="挨拶機能")
    async def greet(self, ctx: commands.Context):
        """30秒以内に返事を待つ挨拶コマンド"""
        message = ctx.message
        member = ctx.author
        channel = message.channel

        # === 画像送信機能 (エラー回避のためコメントアウト中) ===
        # fname = "セグカミラッシャ.png"
        # image_path = f"database/Partycard/{member}/{fname}"
        # if os.path.exists(image_path):
        #     file = discord.File(fp=image_path, filename=fname, spoiler=False)
        #     await channel.send(file=file)
        # ==================================================

        await channel.send("30秒以内に「おはよう」と言ってみて！")

        def check(m):
            return m.content == 'おはよう' and m.channel == channel and m.author == member
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await channel.send('Session Timeout: 30秒以内に「おはよう」が送られませんでした')
        else:
            await channel.send(f'こんにちは、{msg.author.mention}さん！')

async def setup(bot):
    await bot.add_cog(Func(bot))