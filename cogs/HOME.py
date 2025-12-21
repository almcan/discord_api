import discord
from discord.ext import commands
import pandas as pd
from tabulate import tabulate
import asyncio

# データフレームをきれいな表テキストにする関数
df2tb = lambda df: tabulate(
        tabular_data=df,
        stralign="left",
        numalign="right",
        showindex=False,
        tablefmt="plain")

class HOME(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="usage")
    async def usage(self, ctx: commands.Context,
                       arg: str = commands.parameter(default="30", description="順位の下限 or ポケモン名"),
                       min_rank: int = commands.parameter(default=1, description="順位の上限(省略可)"),
                       ):
        """ダブルにおけるポケモンの使用率を表示します
        Usage: 
          ?usage 30       -> 1位~30位を表示
          ?usage ピカチュウ -> ピカチュウの順位を表示
          ?usage 60 31    -> 31位~60位を表示
        """
        
        # データベース接続チェック
        if not hasattr(self.bot, 'pool') or self.bot.pool is None:
            await ctx.send("⚠️ データベースに接続されていないため、このコマンドは使用できません。")
            return

        try:
            # asyncpg (非同期) の書き方に修正
            async with self.bot.pool.acquire() as conn:
                rows = []
                
                # 引数が数値か文字列かで分岐
                # (argが数字だけなら順位指定とみなす)
                if not arg.isdigit():
                    # ポケモン名検索
                    query = """
                        SELECT rank1.rank, pokedex.name
                        FROM home_pokerank_double AS rank1
                        JOIN pokedex ON rank1.id = pokedex.id
                        WHERE pokedex.name LIKE $1
                        ORDER BY rank
                    """
                    # 部分一致検索 (%)
                    rows = await conn.fetch(query, f'%{arg}%')
                else:
                    # 順位範囲検索
                    # argが上限(max), min_rankが下限(min)
                    # 元のコードの引数順序に合わせて調整: usage(limit, start)
                    upper_limit = int(arg)
                    lower_limit = min_rank
                    
                    query = """
                        SELECT rank2.rank, pokedex.name
                        FROM home_pokerank_double AS rank2
                        JOIN pokedex ON rank2.id = pokedex.id
                        WHERE $1 <= rank2.rank AND rank2.rank <= $2
                        ORDER BY rank
                    """
                    rows = await conn.fetch(query, lower_limit, upper_limit)

                if rows:
                    # asyncpgのRecordオブジェクトを辞書のリストに変換してからDataFrameへ
                    data = [dict(row) for row in rows]
                    df = pd.DataFrame(data)
                    
                    # カラム名を整える（必要であれば）
                    # df.columns = ['Rank', 'Name'] 
                    
                    table = df2tb(df)
                    await ctx.send(f"```\n{table}```")
                else:
                    await ctx.send(f"```該当データなし、または圏外です```")

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")
            print(f"[ERROR] usage command error: {e}")

async def setup(bot):
    await bot.add_cog(HOME(bot))