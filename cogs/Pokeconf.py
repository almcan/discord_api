import discord
from discord.ext import commands
import numpy as np
import pandas as pd
from tabulate import tabulate
import asyncio

# ヘルパー関数
l2s = lambda s, l: s.join(map(str, l))
cplist = lambda org: [org, org, org, org, org, org]

# データフレームを見やすい表にする関数
df2tb = lambda df: tabulate(
        tabular_data=df,
        stralign="left",
        numalign="right",
        showindex=False,
        tablefmt="plain")

class Pokeconf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # --- 計算ロジック (同期処理のまま利用可能) ---

    # レベル・個体値・努力値・性格補正を与え、種族値を実数値に変換
    @staticmethod
    def bst2ast_ij(j, bst, lv, iv, ev, ncor):
        # HP計算式: (種族値×2 + 個体値 + 努力値/4) × Lv/100 + Lv + 10
        # 他計算式: ((種族値×2 + 個体値 + 努力値/4) × Lv/100 + 5) × 性格補正
        
        # ※ 元のコードの計算式を再現
        f = lambda bst, iv, ev, lv: int(int(bst * 2 + iv + ev / 4) * lv / 100) + 5
        if j == 0: # HP
            ast_j = int(int(bst[j] * 2 + iv[j] + ev[j] / 4) * lv / 100) + lv + 10
        else: # 他
            ast_j = int((f(bst[j], iv[j], ev[j], lv)) * ncor[j])
        return ast_j

    @staticmethod
    def bst2ast_i(bst, lv, iv, ev, ncor):
        ast_i = []
        for j in range(6):
            ast_j = Pokeconf.bst2ast_ij(j, bst, lv, iv, ev, ncor)
            ast_i.append(ast_j)
        return ast_i
          
    # 最高・準・無振・最低を算出
    @staticmethod
    def bst2astdict(bst, lv):
        ncor_p = [1.0, 1.1, 1.1, 1.1, 1.1, 1.1] # 上昇補正
        ncor_n = [1.0, 0.9, 0.9, 0.9, 0.9, 0.9] # 下降補正
        ncor_f = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0] # 補正なし

        ast_max = Pokeconf.bst2ast_i(bst, lv, cplist(31), cplist(252), ncor_p) # 特化
        ast_semi = Pokeconf.bst2ast_i(bst, lv, cplist(31), cplist(252), ncor_f) # 準速/ぶっぱ
        ast_non = Pokeconf.bst2ast_i(bst, lv, cplist(31), cplist(0), ncor_f)   # 無振り
        ast_min = Pokeconf.bst2ast_i(bst, lv, cplist(0), cplist(0), ncor_n)    # 最遅/下降

        astdict = {
            "max": ast_max,
            "semi": ast_semi,
            "non": ast_non,
            "min": ast_min
        }
        return astdict

    # --- コマンド実装 ---

    @commands.command(name="conf", description="!conf [レベル] ポケモン名")
    async def conf(self, ctx: commands.Context,
                   lv: str = commands.parameter(default="50", description="レベル(省略可)"),
                   *, pkmn: str = commands.parameter(default="ピカチュウ", description="ポケモン名")):
        """
        ポケモンの種族値と実数値を表示します
        Usage: 
          ?conf ピカチュウ      -> Lv50の実数値
          ?conf 100 ピカチュウ  -> Lv100の実数値
        """
        # 引数の入れ替え処理（数字が先頭に来た場合への対応）
        if not lv.isdigit():
            pkmn = lv + " " + pkmn
            lv = "50"
        
        lv_int = int(lv)
        
        # DB接続チェック
        if not hasattr(self.bot, 'pool') or self.bot.pool is None:
            await ctx.send("⚠️ データベースに接続されていないため、データ取得ができません。")
            return

        try:
            async with self.bot.pool.acquire() as conn:
                # 1. ポケモンIDの取得
                # pokedexテーブル: id, name
                query_id = "SELECT id, name FROM pokedex WHERE name LIKE $1 LIMIT 1"
                row_poke = await conn.fetchrow(query_id, f'%{pkmn.strip()}%')
                
                if not row_poke:
                    await ctx.send(f"ポケモン「{pkmn}」が見つかりませんでした。")
                    return
                
                pid = row_poke['id']
                pname = row_poke['name']

                # 2. 種族値の取得
                # bstテーブル: id, h, a, b, c, d, s
                query_bst = "SELECT h, a, b, c, d, s FROM bst WHERE id = $1"
                row_bst = await conn.fetchrow(query_bst, pid)

                if not row_bst:
                    await ctx.send(f"「{pname}」の種族値データが見つかりませんでした。")
                    return

                # 種族値をリスト化
                bst_list = [row_bst['h'], row_bst['a'], row_bst['b'], row_bst['c'], row_bst['d'], row_bst['s']]

                # 3. 他言語名の取得 (オプション)
                query_lang = "SELECT eng, ger, fra FROM lang WHERE jpn = $1 LIMIT 1"
                row_lang = await conn.fetchrow(query_lang, pname)
                
                lang_text = ""
                if row_lang:
                    lang_text = f"Eng:{row_lang['eng']} Ger:{row_lang['ger']} Fra:{row_lang['fra']}"

                # --- 計算と表示 ---
                ast = self.bst2astdict(bst_list, lv_int)
                
                # DataFrame作成
                # 行ラベル: H, A, B, C, D, S, Total
                # 列データ: 種族値, 最遅, 無振, 準速, 最速(特化)
                
                idx = ["H", "A", "B", "C", "D", "S", "Total"]
                
                # 種族値列
                bst_disp = bst_list + [sum(bst_list)]
                
                # 実数値列 (合計値の計算も含む)
                min_disp = ast['min'] + [sum(ast['min'])]
                non_disp = ast['non'] + [sum(ast['non'])]
                semi_disp = ast['semi'] + [sum(ast['semi'])]
                max_disp = ast['max'] + [sum(ast['max'])]

                df = pd.DataFrame({
                    "BS": bst_disp,
                    "Min": min_disp,
                    "Non": non_disp,
                    "Semi": semi_disp,
                    "Max": max_disp
                }, index=idx)

                table = df2tb(df)

                embed = discord.Embed(title=f"{pname} (Lv.{lv_int})", description=lang_text, color=discord.Color.green())
                embed.add_field(name="能力値テーブル", value=f"```\n{table}```", inline=False)
                
                await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")
            print(f"[ERROR] conf command error: {e}")

    @commands.command(name="lang", description="!lang [言語名] 検索する単語")
    async def lang(self, ctx: commands.Context,
                   lang: str = commands.parameter(default="eng", description="表示する言語(eng, jpn等)"),
                   *, word: str = commands.parameter(default="null", description="検索したい単語")):
        """
        各言語のポケモン名を検索・翻訳します
        対応言語: jpn, eng, ger, fra, kor, cs, ct
        """
        # 引数調整
        if word == "null":
            word = lang
            lang = "eng"
        
        valid_langs = ["jpn", "eng", "ger", "fra", "kor", "cs", "ct"]
        if lang not in valid_langs:
            word = lang + ' ' + word
            lang = "eng"
        
        # DB接続チェック
        if not hasattr(self.bot, 'pool') or self.bot.pool is None:
            await ctx.send("⚠️ データベースに接続されていないため、データ取得ができません。")
            return

        try:
            async with self.bot.pool.acquire() as conn:
                # 検索クエリ構築
                # 全言語カラムに対してLIKE検索をかける
                query = f"""
                    SELECT jpn, {lang} 
                    FROM lang 
                    WHERE jpn LIKE $1 OR eng LIKE $1 OR ger LIKE $1 
                       OR fra LIKE $1 OR kor LIKE $1 OR cs LIKE $1 OR ct LIKE $1
                    LIMIT 20
                """
                search_term = f'%{word.strip()}%'
                
                rows = await conn.fetch(query, search_term)
                
                if rows:
                    data = [dict(row) for row in rows]
                    df = pd.DataFrame(data)
                    table = df2tb(df)
                    await ctx.send(f"```\n{table}```")
                else:
                    await ctx.send("該当するポケモンが見つかりませんでした。")

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")
            print(f"[ERROR] lang command error: {e}")

async def setup(bot):
    await bot.add_cog(Pokeconf(bot))