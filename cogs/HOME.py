import asyncio
import discord
from discord.ext import commands
import pandas as pd
import numpy as np
import re
import time
from typing import Union
from tabulate import tabulate
import datetime

l2s=lambda s,l:s.join(map(str,l))
df2tb=lambda df:tabulate(
        tabular_data=df,
        stralign="left",
        numalign="right",
        showindex=False,
        tablefmt="plain")

class HOME(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embedmsg=None

    async def pageview(self,ctx:commands.context,page_desc):
        #リアクション用Emojiリスト
        emoji_list = ['⏪', '⏩']
        #何ページ目かを表す変数
        page = 0
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        #embedとボタン代わりのリアクションを追加
        embed = discord.Embed(title=f"{page_desc[page]['name']}",
                              description=f"""{page_desc[page]["rule"]} 使用率:{page_desc[page]["rank"]}""",
                              color=0x3cc332)
        embed.set_thumbnail(url=page_desc[page]["icon"])
        embed.add_field(name="特性",value=f"{page_desc[page]['abl']}")
        embed.add_field(name="性格",value=f"{page_desc[page]['nature']}")
        embed.add_field(name="持ち物",value=f"{page_desc[page]['item']}")
        embed.add_field(name="一緒にいるポケモン",value=f"{page_desc[page]['party']}")
        embed.add_field(name="技の採用率",value=f"{page_desc[page]['move']}")
        embed.add_field(name="テラスタイプ",value=f"{page_desc[page]['teras']}")
        embed.set_footer(text=f'最終更新:{now_str} page {page+1} of {len(page_desc)}')
        #一定時間(delete_afterで秒数を指定)経過すると自動的に出力を削除
        msg = await ctx.channel.send(embed=embed)
        self.embedmsg=msg

        if len(page_desc)>1:
            
            for add_emoji in emoji_list:
                await msg.add_reaction(add_emoji)

            #リアクションチェック用の関数
            def check1(reaction, user):
                #botを呼び出した本人からのリアクションのみ受け付ける場合は
                #user == ctx.author and reaction...
                #reaction.message == msg を入れないと複数出したときに全て連動して動いてしまう
                return reaction.message == msg and str(reaction.emoji) in emoji_list

            def check2(m):
                return m.content == ">>" or m.content=="<<"
            
            while True:
                try:
                    #リアクションもしくは文字列「<<」「>>」が入力されるまで待機
                    pending_tasks = [
                        self.bot.wait_for('reaction_add',check=check1),
                        self.bot.wait_for('message',check=check2)]
                    done_tasks, pending_tasks = await asyncio.wait(pending_tasks,
                                                                   return_when=asyncio.FIRST_COMPLETED,
                                                                   timeout=600)
                    for task in pending_tasks:
                        task.cancel()
                    payload=done_tasks.pop().result()
                except:
                    for add_emoji in emoji_list:
                        await msg.remove_reaction(add_emoji,self.bot.user)
                    break
                else:
                    #リアクションが付与された場合
                    if type(payload)==tuple:
                        reaction=payload[0]
                        #付けられたリアクションに対応した処理を行う
                        if str(reaction.emoji) == (emoji_list[0]):
                            #ページ戻し
                            #ページ数の更新(0~最大ページ数-1の範囲に収める)
                            page = (page - 1) % len(page_desc)

                        if str(reaction.emoji) == (emoji_list[1]):
                            #ページ送り
                            #ページ数の更新(0~最大ページ数-1の範囲に収める)
                            page = (page + 1) % len(page_desc)
                    
                    #文字列「<<」「>>」が入力された場合
                    elif type(payload)==discord.message.Message:
                        #文字列を削除
                        #await payload.delete()
                        
                        if payload.content=='<<':
                            #ページ戻し
                            #ページ数の更新(0~最大ページ数-1の範囲に収める)
                            page = (page - 1) % len(page_desc)
                        else:
                            #ページ送り
                            #ページ数の更新(0~最大ページ数-1の範囲に収める)
                            page = (page + 1) % len(page_desc)

                    #メッセージ内容の更新
                    embed.clear_fields()
                    embed = discord.Embed(title=f"{page_desc[page]['name']}",
                                        description=f"""{page_desc[page]["rule"]} 使用率:{page_desc[page]["rank"]}""",
                                        color=0x3cc332)
                    embed.set_thumbnail(url=page_desc[page]["icon"])
                    embed.add_field(name="特性",value=f"{page_desc[page]['abl']}")
                    embed.add_field(name="性格",value=f"{page_desc[page]['nature']}")
                    embed.add_field(name="持ち物",value=f"{page_desc[page]['item']}")
                    embed.add_field(name="一緒にいるポケモン",value=f"{page_desc[page]['party']}")
                    embed.add_field(name="技の採用率",value=f"{page_desc[page]['move']}")
                    embed.add_field(name="テラスタイプ",value=f"{page_desc[page]['teras']}")
                    embed.set_footer(text=f'最終更新:{now_str} page {page+1} of {len(page_desc)}')
                        
                    if type(payload)==tuple:
                        await msg.edit(embed=embed)
                        #リアクションをもう一度押せるように消しておく
                        await msg.remove_reaction(reaction.emoji, ctx.author)

                    elif type(payload)==discord.message.Message:                        
                        await self.embedmsg.edit(embed=embed)
                        #1秒待機
                        await asyncio.sleep(1)

    #あいまい検索
    def fetch_fnames(cur,name):
        cur.execute(
            f"""
            SELECT pokedex.name 
            FROM pokedex,home_pokerank_single AS rank
            WHERE pokedex.name LIKE '%{name}%'
            AND rank.id=pokedex.id
            ORDER BY rank.rank
            """
            )
        #ヒットしたすべての結果:fnames
        fnames=list(np.array(cur.fetchall()).flatten())
        return fnames

    @commands.command(aliases=["pi"],name="pokeinfo",
                      description="!pokeinfo/!pi ポケモン名 [1=シングル,2=ダブル]")
    async def pokeinfo(self,ctx:commands.Context,
                       name:str=commands.parameter(description="ポケモン名"),
                       rule_num:int=commands.parameter(default=1,description="1=シングル,2=ダブル")):
        """そのポケモンの採用率が高い性格や技、持ち物などを表示します"""
        
        num2rule = lambda num :"single" if num==1 else "double" if num==2 else ""
        num2rule2 = lambda num :"シングル" if num==1 else "ダブル" if num==2 else ""
        rule = num2rule(rule_num)
        rule2 = num2rule2(rule_num)
        
        # 1. ポケモン名検索
        search_sql = f"""
            SELECT pokemon
            FROM home_pokerank_single
            WHERE pokemon LIKE '%{name}%'
            ORDER BY rank
            LIMIT 5
        """
        
        records = await self.bot.db.fetch(search_sql)
        fnames = [r['pokemon'] for r in records]

        if not fnames:
            await ctx.send("ポケモンが見つかりませんでした。")
            return

        page_desc = []
        
        # 2. 詳細データの取得
        for fname in fnames:
            # --- アイコン ---
            icon_sql = f"SELECT icon FROM pokedex WHERE name = '{fname}'"
            icon_val = await self.bot.db.fetchval(icon_sql)
            icon = icon_val if icon_val else ""

            # --- 順位 ---
            rank_sql = f"""
                SELECT rank
                FROM home_pokerank_{rule}
                WHERE pokemon='{fname}'
            """
            rank_val = await self.bot.db.fetchval(rank_sql)
            rank = f"{rank_val}位" if rank_val else "150位圏外"

            # --- 特性 (Abilities) ---
            abl_sql = f"""
                SELECT rank::text||'.'||ability AS name, raito||'%' AS val
                FROM home_ability_{rule}
                WHERE pokemon='{fname}'
                ORDER BY rank
            """
            abl_res = await self.bot.db.fetch(abl_sql)
            tbabl = df2tb(pd.DataFrame([dict(r) for r in abl_res])) if abl_res else "データなし"

            # --- 持ち物 (Items) ---
            item_sql = f"""
                SELECT rank::text||'.'||item AS name, raito||'%' AS val
                FROM home_item_{rule}
                WHERE pokemon='{fname}'
                ORDER BY rank
            """
            item_res = await self.bot.db.fetch(item_sql)
            tbitem = df2tb(pd.DataFrame([dict(r) for r in item_res])) if item_res else "データなし"

            # --- 技 (Moves) ---
            move_sql = f"""
                SELECT rank::text||'.'||move AS name, raito||'%' AS val
                FROM home_move_{rule}
                WHERE pokemon='{fname}'
                ORDER BY rank
            """
            move_res = await self.bot.db.fetch(move_sql)
            tbmove = df2tb(pd.DataFrame([dict(r) for r in move_res])) if move_res else "データなし"

            # --- テラスタイプ (Teras) ---
            teras_sql = f"""
                SELECT rank::text||'.'||terastype AS name, raito||'%' AS val
                FROM home_terastype_{rule}
                WHERE pokemon='{fname}'
                ORDER BY rank
            """
            teras_res = await self.bot.db.fetch(teras_sql)
            tbteras = df2tb(pd.DataFrame([dict(r) for r in teras_res])) if teras_res else "データなし"

            # --- 性格とパーティ (今回は未実装のまま) ---
            tbnature = "データ未実装"
            tbparty = "データ未実装"

            # --- ページの作成 ---
            keys = ["rule", "name", "icon", "rank", "abl", "nature", "item", "party", "move", "teras"]
            vals = [rule2, fname, icon, rank, tbabl, tbnature, tbitem, tbparty, tbmove, tbteras]
            page = dict(zip(keys, vals))
            page_desc.append(page)

        await self.pageview(ctx, page_desc)
        
    @commands.command(name="pokerank1",
                      description="!pokerank1 順位の下限 or ポケモン名, [上限]")
    async def pokerank1(self,ctx:commands.Context,
                        arg:Union[int,str]=commands.parameter(default=30,description="順位の下限 or ポケモン名"),
                        min:int=commands.parameter(default=1,description="順位の上限(省略可)"),
                        ):
        """シングルにおけるポケモンの使用率を表示します"""
        if type(arg) is str:
            sql = f"""
                    SELECT rank1.rank,pokedex.name
                    FROM home_pokerank_single AS rank1,pokedex
                    WHERE pokedex.name like '%{arg}%'
                    AND rank1.pokemon = pokedex.name
                    ORDER BY rank
                    """
        else:
            sql = f"""
                    SELECT rank2.rank,pokedex.name
                    FROM home_pokerank_single AS rank2,pokedex
                    WHERE rank2.pokemon = pokedex.name
                    AND '{min}'<=rank2.rank AND rank2.rank<='{arg}'
                    ORDER BY rank
                    """
        frank = await self.bot.db.fetch(sql)
        
        if len(frank) >= 1:
            data = [dict(row) for row in frank]
            df = pd.DataFrame(data)
            
            table = df2tb(df)
            await ctx.send(f"```{table}```")
        else:
            await ctx.send(f"```150位圏外```")

    @commands.command(name="pokerank2",
                      description="!pokerank2 順位の下限 or ポケモン名, [上限]")
    async def pokerank2(self,ctx:commands.Context,
                        arg:Union[int,str]=commands.parameter(default=30,description="順位の下限 or ポケモン名"),
                        min:int=commands.parameter(default=1,description="順位の上限(省略可)"),
                        ):
        """ダブルにおけるポケモンの使用率を表示します"""
        
        if type(arg) is str:
            sql = f"""
                    SELECT rank1.rank,pokedex.name
                    FROM home_pokerank_double AS rank1,pokedex
                    WHERE pokedex.name like '%{arg}%'
                    AND rank1.pokemon = pokedex.name
                    ORDER BY rank
                    """
        else:
            sql = f"""
                    SELECT rank2.rank,pokedex.name
                    FROM home_pokerank_double AS rank2,pokedex
                    WHERE rank2.pokemon = pokedex.name
                    AND '{min}'<=rank2.rank AND rank2.rank<='{arg}'
                    ORDER BY rank
                    """
        
        # SQL実行
        frank = await self.bot.db.fetch(sql)
        
        if len(frank) >= 1:
            data = [dict(row) for row in frank]
            df = pd.DataFrame(data)
            
            table = df2tb(df)
            await ctx.send(f"```{table}```")
        else:
            await ctx.send(f"```150位圏外```")


                
async def setup(bot):
    await bot.add_cog(HOME(bot))