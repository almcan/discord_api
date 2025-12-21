import psycopg2.extras
import discord,asyncio
from discord.ext import commands
import pandas as pd
from tabulate import tabulate
from collections import deque
import matplotlib.pyplot as plt
import time,pdf2image,os,io,japanize_matplotlib,gspread,re
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe


l2s=lambda s,l:s.join(map(str,l))
class SQL(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embedmsg=None
        self.outoptionpage=0
        os.makedirs("database/pdf", exist_ok=True)
        os.makedirs("database/png", exist_ok=True)
    
    def get_connection(self):
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            raise Exception("環境変数 DATABASE_URL が設定されていません。")
        return psycopg2.connect(dsn)

    async def pageview(self,ctx:commands.context,page_desc,color=0x3cc332):
        #リアクション用Emojiリスト
        emoji_list = ['⏪', '⏩']
        #何ページ目かを表す変数
        page = 0

        #embedとボタン代わりのリアクションを追加
        embed = discord.Embed(description=f"""```sql\n{page_desc[page]} ```"""
                              ,color=color)
        if len(page_desc)>1:
            embed.set_footer(text=f'page {page+1} of {len(page_desc)}')
        #一定時間(delete_afterで秒数を指定)経過すると自動的に出力を削除
        msg = await ctx.channel.send(embed=embed)
        self.embedmsg=msg

        if len(page_desc)>1:
            
            for add_emoji in emoji_list:
                await msg.add_reaction(add_emoji)

            #リアクションチェック用の関数
            def check1(reaction,user):
                #botを呼び出した本人からのリアクションのみ受け付ける場合は
                #user == ctx.author and reaction...
                #reaction.message == msg を入れないと複数出したときに全て連動して動いてしまう
                return reaction.message == msg and str(reaction.emoji) in emoji_list
            
            #文字列「<<」「>>」が入力された場合
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

                        #メッセージ内容の更新
                        embed = discord.Embed(description=f"""```sql\n{page_desc[page]} ```"""
                                            ,color=color)
                        embed.set_footer(text=f'page {page+1} of {len(page_desc)}')

                        await msg.edit(embed=embed)
                        #リアクションをもう一度押せるように消しておく
                        await msg.remove_reaction(reaction.emoji, ctx.author)

                    """文字列「<<」「>>」が入力された場合
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
                        embed = discord.Embed(description=f\"""```sql\n{page_desc[page]}```\"""
                                            ,color=color)
                        embed.set_footer(text=f'page {page+1} of {len(page_desc)}')
                        await self.embedmsg.edit(embed=embed)
                        #1秒待機
                        time.sleep(1)
                    """
                            

    async def df2out(self,ctx,df,index=False,column=[],k=20,tablefmt="plain"):
        #k: 1DataFrameあたりの行数
        dfs = [df.loc[i:i+k-1, :] for i in range(0, len(df), k)]
        #headerをつける場合
        #column=df.columns.values.tolist(),
        tablelist=[tabulate(
            tabular_data=df,
            headers=column,
            stralign="left",
            numalign="right",
            showindex=index,
            tablefmt=tablefmt) for df in dfs]
        await SQL.pageview(self,ctx,tablelist)

    @commands.command(name="sql",
                             description="!sql [-a,-o] SQL文")
    async def sql(self,ctx:commands.Context,
                  opt:str=commands.parameter(default="no option",description="オプション"),*,
                  args:str=commands.parameter(default="null",description="実行したいSQL文")):
        """
        SQL文を実行します
        オプション
        -a:実行計画を表示
        -o:Spread Sheetに出力
        -ao or -oa:実行計画をSpread Sheetに出力
        """
        conn = self.get_connection() # 新しい接続メソッドを使用
        try:
            with conn:
                with conn.cursor() as cur:
                    if args=="last":
                        cur.execute(f"SELECT cmd FROM sqlcmd WHERE name='last'")
                        last_cmd=cur.fetchone()[0]
                        args=last_cmd
                    sql="INSERT INTO sqlcmd (name,cmd) VALUES (%s,%s)"
                    values=[name,args]
                    cur.execute(sql,values)
                    conn.commit()
                    await ctx.send(f"コマンド ?{name} を登録しました")
                    cur.execute(f"SELECT name||chr(10)||cmd FROM sqlcmd WHERE name= '{name}'")
                    table=cur.fetchall()
                    df=pd.DataFrame(table)
            await SQL.df2out(self,ctx,df,tablefmt="plain")
        except Exception as e:
            await ctx.send(f"エラー: {e}")
        finally:
            conn.close()
        df=pd.DataFrame(table,columns=cols)
        if re.match('-a?oa?',opt):
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                # ***.json　は各自ダウンロードしたjsonファイル名に変更
                credentials = ServiceAccountCredentials.from_json_keyfile_name('database/gas/credentials.json', scope)
                gc = gspread.authorize(credentials)
                # スプレッドシートのキー
                key = os.environ["SPREAD_SHEET_KEY"]
                workbook = gc.open_by_key(key)
                worksheet_list = workbook.worksheets()
                s1=worksheet_list[0]
                s1.update_title("!sql")
                #内容をすべて削除
                s1.clear()
                #　1つ目のシートの内容をDiscordに送ったメッセージ内容で更新
                set_with_dataframe(s1, df)
                await ctx.send(f"<https://docs.google.com/spreadsheets/d/{key}>")
            except:
                await ctx.send("spread sheetの出力に失敗しました")
        else:
            await SQL.df2out(self,ctx,df,column=cols,tablefmt="plain")
                

    @commands.command(name="addsql",
                             description="!addsql コマンド名 SQL文")
    async def addsql(self,ctx:commands.Context
                     ,name:str=commands.parameter(description="登録するコマンド名"),
                     *,args:str=commands.parameter(description="登録するSQL文|last")):
        """
        SQL文をコマンドとして登録します
        実行できるコマンドはSELECTから始まるもののみです
        第二引数に「登録するSQL文」の代わりに「last」を入力すると、
        ?lastコマンドに格納されているSQL文がコマンドとして登録されます
        """
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #?lastに格納されているSQL文をコマンドとして登録する
                if args=="last":
                    cur.execute(f"SELECT cmd FROM sqlcmd WHERE name='last'")
                    last_cmd=cur.fetchone()[0]
                    args=last_cmd
                sql="INSERT INTO sqlcmd (name,cmd) VALUES (%s,%s)"
                values=[name,args]
                cur.execute(sql,values)
                conn.commit()
                await ctx.send(f"コマンド ?{name} を登録しました")
                cur.execute(f"SELECT name||chr(10)||cmd FROM sqlcmd WHERE name= '{name}'")
                table=cur.fetchall()
                df=pd.DataFrame(table)
        await SQL.df2out(self,ctx,df,tablefmt="plain")
        
    @commands.command(name="delsql",
                             description="!delsql コマンド名")
    async def delsql(self,ctx:commands.Context,
                     name:str=commands.parameter(description="削除するコマンド名")):
        """コマンドを削除します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT id FROM sqlcmd WHERE name='{name}'")
                cmdid=cur.fetchone()[0]
                if cmdid>0:
                    cur.execute(f"UPDATE sqlcmd SET id=id-1 WHERE id>'{cmdid}' AND not id=0")
                    conn.commit()
                sql="DELETE FROM sqlcmd WHERE name = %s"
                #SQL文を実行
                cur.execute(sql,(name,))
                conn.commit()
                await ctx.send(f"コマンド ?{name} を削除しました")

    @commands.command(aliases=["esql"],name="editsql",
                             description="!esql/!editsql コマンド名 説明文")
    async def editsql(self,ctx:commands.Context,
                     name:str=commands.parameter(description="コマンド名"),
                     *,description:str=commands.parameter(description="登録する説明文")):
        """コマンドに説明を追加・変更します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                cur.execute(f"UPDATE sqlcmd SET text = '{description}' WHERE name ='{name}'")
                cur.execute(f"UPDATE sqlcmd set modified=now() WHERE name='{name}'")
                conn.commit()
                await ctx.send(f"コマンド ?{name} の説明文を追加・変更しました")
                cur.execute(f"SELECT name||chr(10)||text FROM sqlcmd WHERE sqlcmd.name= '{name}'")
                table=cur.fetchall()
                df=pd.DataFrame(table)
        await SQL.df2out(self,ctx,df,tablefmt="plain")
    
    @commands.command(aliases=["esqlcmd"],name="editsqlcmd",
                             description="!esqlcmd/!editsqlcmd コマンド名 SQL文")
    async def editsqlcmd(self,ctx:commands.Context,
                     name:str=commands.parameter(description="コマンド名"),
                     *,cmd:str=commands.parameter(description="上書きするSQL文")):
        """コマンドのSQL文をを上書きします"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                sql="UPDATE sqlcmd SET cmd = %s WHERE name = %s"
                #SQL文を実行
                cur.execute(sql,(cmd,name,))
                cur.execute(f"UPDATE sqlcmd set modified=now() WHERE name='{name}'")
                conn.commit()
                await ctx.send(f"コマンド ?{name} のSQL文を上書きしました")
                cur.execute(f"SELECT name||chr(10)||cmd FROM sqlcmd WHERE name= '{name}'")
                table=cur.fetchall()
                df=pd.DataFrame(table)
        await SQL.df2out(self,ctx,df,tablefmt="plain")   
        
    @commands.command(aliases=["fsql"],name="findsql",
                             description="!fsql/!findsql 検索する単語")
    async def findsql(self,ctx:commands.Context,
                         *,word:str=commands.parameter(description="検索する単語")):
        """説明文からコマンドを検索します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                try:
                    cur.execute(
                        f"""
                        SELECT name||chr(10)||
                        i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                        text||chr(10)||
                        '-----------------------------'
                        FROM sqlcmd WHERE text like '%{word}%'
                        """)
                    table=cur.fetchall()
                    df=pd.DataFrame(table)
                    await SQL.df2out(self,ctx,df,k=10,tablefmt="plain")
                except:
                    await ctx.send("検索結果が見つかりませんでした")

    @commands.command(aliases=["fsqlcmd"],name="findsqlcmd",
                             description="!fsqlcmd/!findsqlcmd 検索する単語/コマンド名")
    async def findsqlcmd(self,ctx:commands.Context,
                         *,word:str=commands.parameter(description="検索する単語/コマンド名")):
        """
        SQL文からコマンドを検索します
        コマンドの依存関係を調べるときに便利です
        """
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                cur.execute(
                    f"""
                    SELECT name||chr(10)||
                    cmd||chr(10)||
                    i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                    text||chr(10)
                    FROM sqlcmd WHERE  name='{word}'
                    """)
                table=cur.fetchall()
                if table:
                    df=pd.DataFrame(table)
                    await SQL.df2out(self,ctx,df,tablefmt="plain")
                try:
                    cur.execute(
                        f"""
                        SELECT name||chr(10)||
                        cmd||chr(10)||
                        i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                        text||chr(10)||
                        '-----------------------------' 
                        FROM sqlcmd WHERE cmd LIKE '%{word}%'
                        """)
                    table=cur.fetchall()
                    df=pd.DataFrame(table)
                    await SQL.df2out(self,ctx,df,k=5,tablefmt="plain")
                except:
                    await ctx.send("検索結果が見つかりませんでした")

    @commands.command(name="psql",
                             description="!psql コマンド名")
    async def psql(self,ctx:commands.Context,
                   name:str=commands.parameter(default='*',description="コマンド名")):
        """コマンドの説明を表示します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                try:
                    if name=='*':
                        cur.execute(f"SELECT name,text FROM sqlcmd ORDER BY id")
                        table=cur.fetchall()
                        df=pd.DataFrame(table)
                        await SQL.df2out(self,ctx,df,k=20,tablefmt="plain")  
                    else:
                        cur.execute(
                            f"""
                            SELECT name||chr(10)||
                            i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                            text||chr(10)||
                            '-----------------------------'
                            FROM sqlcmd WHERE name like '%{name}%' ORDER BY id
                            """)
                        table=cur.fetchall()
                        df=pd.DataFrame(table)
                        await SQL.df2out(self,ctx,df,k=5,tablefmt="plain")  
                except:
                    await ctx.send("検索結果が見つかりませんでした")

    @commands.command(name="psqlcmd",
                             description="!psqlcmd コマンド名")
    async def psqlcmd(self,ctx:commands.Context,
                   name:str=commands.parameter(default='*',description="コマンド名")):
        """コマンドのSQL文を表示します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                try:
                    if name=='*':
                        cur.execute(
                            f"""
                            SELECT name||chr(10)||cmd||chr(10)||
                            i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                            text||chr(10)||
                            '-----------------------------' 
                            FROM sqlcmd ORDER BY id""")
                    else:    
                        cur.execute(
                            f"""
                            SELECT name||chr(10)||cmd||chr(10)||
                            i1||', '||i2||', '||i3||'  ==> '||o1||', '||o2||', '||o3||chr(10)||
                            text||chr(10)||
                            '-----------------------------' 
                            FROM sqlcmd WHERE name like '%{name}%' ORDER BY id
                            """)
                    table=cur.fetchall()
                    df=pd.DataFrame(table)
                    await SQL.df2out(self,ctx,df,k=5,tablefmt="plain")
                except:
                    await ctx.send("検索結果が見つかりませんでした")

    @commands.command(name="psqlio",
                             description="!psqlio コマンド名")
    async def psqlio(self,ctx:commands.Context,
                   name:str=commands.parameter(default='*',description="コマンド名")):
        """コマンドの表示優先順位,引数,出力を表示します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                try:
                    if name=='*':
                        cur.execute(f"SELECT id,name,i1,i2,i3,o1,o2,o3 FROM sqlcmd ORDER BY id")
                    else:
                        cur.execute(
                            f"""
                            SELECT id,name,i1,i2,i3,o1,o2,o3 
                            FROM sqlcmd WHERE name like '%{name}%' ORDER BY id
                            """)
                    cols = [col.name for col in cur.description]
                    table=cur.fetchall()
                    df=pd.DataFrame(table)
                    await SQL.df2out(self,ctx,df,column=cols,tablefmt="plain")
                except:
                    await ctx.send("検索結果が見つかりませんでした")

    @commands.command(aliases=["esqlio"],name="editsqlio",
                             description="!esqlio/!editsqlio コマンド名 変更箇所 変更内容")
    async def editsqlio(self,ctx:commands.Context,
                     name:str=commands.parameter(description="コマンド名"),
                     targets:str=commands.parameter(description="変更箇所"),
                     changes:str=commands.parameter(description="登録する変更内容")):
        """
        表示優先順位,名前,引数,出力を追加・変更します
        - 表示優先順位[id]
        - コマンド名[name]
        - 引数[i1,i2,i3]
        - 出力[o1,i2,i3]
        また、targets,changesは同時に複数指定することもできます
        Ex) !esqlio test id,i1,o1 2,特性,ポケモン
        """
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                targetlist=targets.split(',')
                changelist=changes.split(',')
                for target,change in zip(targetlist,changelist):
                    #SQL文を実行
                    if target=="id":
                        cur.execute(f"SELECT id FROM sqlcmd WHERE name='{name}'")
                        cmdid=cur.fetchone()[0]
                        change=int(change)
                        #changeの値が同じときは除外
                        if cmdid!=change and cmdid>=0 and change>=0:
                            if cmdid==0:
                                cur.execute(f"UPDATE sqlcmd SET id=id+1 WHERE id>={change}")
                                conn.commit()
                            elif change==0:
                                cur.execute(f"UPDATE sqlcmd SET id=id-1 WHERE id>={cmdid+1}")
                                conn.commit()
                            elif cmdid<change:
                                cur.execute(f"UPDATE sqlcmd SET id=id-1 WHERE id BETWEEN {cmdid+1} AND {change}")
                                conn.commit()
                            elif change<cmdid:
                                cur.execute(f"UPDATE sqlcmd SET id=id+1 WHERE id BETWEEN {change} AND {cmdid-1}")
                                conn.commit()
                    cur.execute(f"UPDATE sqlcmd SET {target} = '{change}' WHERE name ='{name}'")
                    conn.commit()
                    if target=="name":
                        name=change
                #名前の変更をしたとき、変更後の名前を参照する
                if "name" in targets:
                    d=dict(zip(targetlist,changelist))
                    cur.execute(f"UPDATE sqlcmd set modified=now() WHERE name='{d['name']}'")
                    conn.commit()
                    cur.execute(f"SELECT {targets} FROM sqlcmd WHERE sqlcmd.name= '{d['name']}'")
                else:
                    cur.execute(f"UPDATE sqlcmd set modified=now() WHERE name='{name}'")
                    conn.commit()
                    cur.execute(f"SELECT name,{targets} FROM sqlcmd WHERE sqlcmd.name= '{name}'")
                cols = [col.name for col in cur.description]
                table=cur.fetchall()
                df=pd.DataFrame(table)
                await ctx.send(f"コマンド ?{name} の{targets}を追加・変更しました")
        await SQL.df2out(self,ctx,df,column=cols,tablefmt="plain")
    
    @commands.command(aliases=["dt"],name="desctbl",description="!dt/!desctbl")
    async def desctbl(self,ctx:commands.Context):
        """すべてのテーブルの説明を表示します"""
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                cur.execute(
                    """
                    SELECT pg_stat_user_tables.relname AS "テーブル名",
                    pg_description.description AS "説明"
                    FROM pg_stat_user_tables,pg_description
                    WHERE pg_stat_user_tables.relname
                    IN (SELECT relname AS table_name FROM pg_stat_user_tables)
                    AND pg_stat_user_tables.relid=pg_description.objoid
                    AND pg_description.objsubid=0
                    AND pg_stat_user_tables.schemaname=current_schema() ORDER BY "テーブル名"
                    """
                    )
                cols = [col.name for col in cur.description]
                table=cur.fetchall()
                df=pd.DataFrame(table)
        await SQL.df2out(self,ctx,df,column=cols,tablefmt="plain")

    @commands.command(aliases=["d"],name="dtltbl",description="!d/!dtltbl テーブル名")
    async def dtltbl(self,ctx:commands.Context,
                      table:str=commands.parameter(description="テーブル名")):
        """
        テーブルの列名,データ型などの情報を表示します
        すべてのテーブルは!desctbl/!dtで確認できます
        """
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                #SQL文を実行
                cur.execute(
                    f"""
                    SELECT information_schema.columns.column_name AS "列名",
                    (SELECT description 
                    FROM pg_description 
                    WHERE pg_description.objoid=pg_stat_user_tables.relid 
                    AND pg_description.objsubid=information_schema.columns.ordinal_position) AS "説明" 
                    FROM pg_stat_user_tables,information_schema.columns 
                    WHERE pg_stat_user_tables.relname='{table}'
                    AND pg_stat_user_tables.relname=information_schema.columns.table_name
                    """)
                cols = [col.name for col in cur.description]
                table=cur.fetchall()
                df=pd.DataFrame(table)
        await SQL.df2out(self,ctx,df,column=cols,tablefmt="plain")

    #以下「?」を受け取るイベントリスナー
    def setvars(self):
            self.cmdoplist=deque()
            self.args=deque()
            self.opargs=deque()
            self.dflist=deque()
            self.query=""
            self.breakcode="preview"
            self.errorcode=""
            self.showindex=False
            self.argrepltable={
                               '>=?':">=0",
                               '?<=':"0<=",
                               '<=?':"<=65535",
                               '?>=':"65535>=",
                               '>= ?':">= 0",
                               '? <=':"0 <=",
                               '<= ?':"<= 65535",
                               '? >=':"65535 >=",
                               '>?':">0",
                               '?<':"0<",
                               '<?':"<65535",
                               '?>':"65535>",
                               '> ?':"> 0",
                               '? <':"0 <",
                               '< ?':"< 65535",
                               '? >':"65535 >",
                               '\'%\'||?||\'%\'':"\'%\'",
                               '\'%\'||?':"\'%\'",
                               '?||\'%\'':"\'%\'",
                               '=?':" LIKE '%'",
                               '= ?':" LIKE '%'",
                               '!=?':" LIKE '%'",
                               '!= ?':" LIKE '%'",
                               '? in (':"\'%\' in (\'%\',",
                               '? IN (':"\'%\' IN (\'%\',",
                               '? not in (':"\'%\' in (\'%\',",
                               '? NOT IN (':"\'%\' IN (\'%\',"
                               }
            self.whererepltable={
                                '>=?':">=0",
                                '?<=':"0<=",
                                '<=?':"<=65535",
                                '?>=':"65535>=",
                                '>= ?':">= 0",
                                '? <=':"0 <=",
                                '<= ?':"<= 65535",
                                '? >=':"65535 >=",
                                '>?':">0",
                                '?<':"0<",
                                '<?':"<65535",
                                '?>':"65535>",
                                '> ?':"> 0",
                                '? <':"0 <",
                                '< ?':"< 65535",
                                '? >':"65535 >",
                                'str.contains("?")':".str.match(\'.*\')",
                                'str.startswith("?")':".str.match(\'.*\')",
                                'str.endswith("?")':".str.match(\'.*\')",
                                '==\'?\'':".str.match(\'.*\')",
                                '== \'?\'':".str.match(\'.*\')",
                                '!=\'?\'':".str.match(\'.*\')",
                                '!= \'?\'':".str.match(\'.*\')",
                                '==\'?\'':".str.match(\'.*\')",
                                '== \'?\'':".str.match(\'.*\')",
                                '!=\'?\'':".str.match(\'.*\')",
                                '!= \'?\'':".str.match(\'.*\')",
                                '=="?"':".str.match(\'.*\')",
                                '== "?"':".str.match(\'.*\')",
                                '!="?"':".str.match(\'.*\')",
                                '!= "?"':".str.match(\'.*\')",
                                '=="?"':".str.match(\'.*\')",
                                '== "?"':".str.match(\'.*\')",
                                '!="?"':".str.match(\'.*\')",
                                '!= "?"':".str.match(\'.*\')"
                                }

    #受け取ったメッセージをcmd・opのリスト,argsに変換
    async def msg2cmdop_and_args(self,ctx,msg):
        oplist=["and","or","show","desc",
                "inner","outer","diff","left","right",
                "sort","drop","loc","rename","dup","unique",
                "plot","groupby","out"]
        msg_seg=deque(msg.split())
        cmdoplist=[]
        args=[]
        opargs=[]
        while(1):
            if not msg_seg:
                for i in range(len(cmdoplist)):
                    self.cmdoplist.insert(i,cmdoplist[i])
                for i in range(len(args)):
                    self.args.insert(i,args[i])
                for i in range(len(opargs)):
                    self.opargs.insert(i,opargs[i])
                break
            else:
                seg=msg_seg.popleft()
                if seg[0] in ['?','`'] or seg in oplist:
                    if seg[0]=='?' or seg in ["and","or","show","desc","out"]:
                        cmdoplist.append(seg)
                    elif seg[0]=='`':
                        if seg[-1]=='`':
                            cmdoplist.append(seg)
                        else:
                            where=seg+' '
                            while(1):
                                try:
                                    seg=msg_seg.popleft()
                                    if seg[-1]=='`':
                                        where+=seg
                                        cmdoplist.append(where)
                                        break
                                    else:
                                        where+=seg+' '
                                except Exception as error:
                                    self.errorcode=error
                                    await ctx.send("'`'が閉じられませんでした")
                                    break
                    elif seg in ["inner","outer","diff","left","right","drop","unique","loc","rename","dup","plot"]:
                        cmdoplist.append(seg)
                        if seg=="plot" and not msg_seg:
                            oparg="no entry"
                        else:
                            oparg=msg_seg.popleft()
                        opargs.append(oparg)
                    elif seg in ["groupby"]:
                        cmdoplist.append(seg)
                        for i in range(2):
                            oparg=msg_seg.popleft()
                            opargs.append(oparg)
                    elif seg in ["sort"]:
                        cmdoplist.append(seg)
                        sort_key=msg_seg.popleft()
                        opargs.append(sort_key)
                        if msg_seg and set(msg_seg[0].split(','))<={'a','d'}:
                            ascstr=msg_seg.popleft()
                            asclist=ascstr.split(',')
                            bools=[]
                            for asc in asclist:
                                if asc=="d":
                                    boolean=False
                                elif asc=="a":
                                    boolean=True
                                bools.append(boolean)
                        else:
                            bools=[False for i in range(len(sort_key.split(',')))]
                        opargs.append(bools)
                else:
                    args.append(seg)

    #コマンド名からSQL文を取得
    async def fetchcmd(self,ctx,cmd):
        conn=self.bot.get_connection()
        with conn:
            with conn.cursor() as cur:
                try:
                    cmdname=cmd[1:]
                    cur.execute(f"SELECT cmd FROM sqlcmd WHERE name='{cmdname}'") #SQLコマンドを検索
                    sqlcmd=cur.fetchone()[0]
                    return sqlcmd
                except Exception as error:
                    self.errorcode=error
                    await ctx.send("コマンドが見つかりませんでした")
                
    async def cmd2df(self,ctx,cmd):
        self.query+=f"{cmd}[\n"
        sqlcmd=await SQL.fetchcmd(self,ctx,cmd)
        if sqlcmd[0]=='?':
            await SQL.msg2cmdop_and_args(self,ctx,sqlcmd)
            await SQL.execmd(self,ctx)
        else:
            conn=self.bot.get_connection()
            with conn:
                with conn.cursor() as cur:
                    try:
                        if sqlcmd.count('?')>0:
                            #左から順に「?」をargに置換
                            for i in range(sqlcmd.count('?')):
                                if self.args:
                                    arg=self.args.popleft()
                                    if arg=='*':
                                        repltable=self.argrepltable
                                        search_keys_list=[re.escape(key) for key in repltable.keys()]
                                        search_keys=l2s('|',search_keys_list)
                                        #辞書のキーのいずれかに一致する文字列を左から探索
                                        key=re.search(search_keys,sqlcmd).group()
                                        sqlcmd=sqlcmd.replace(key,repltable[key],1)                             
                                    else:
                                        sqlcmd=sqlcmd.replace("\?",f"?",1)
                                        sqlcmd=sqlcmd.replace("!??",arg)
                                        sqlcmd=sqlcmd.replace("??",f"'{arg}'")                                  
                                        sqlcmd=sqlcmd.replace("!?",arg,1)
                                        sqlcmd=sqlcmd.replace('?',f"'{arg}'",1)
                                else:
                                    break
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("引数が不足しています")
                        self.query+=f"{sqlcmd}\n"
                    else:
                        #SQL文を実行
                        try:
                            self.query+=sqlcmd
                            cur.execute(sqlcmd)
                            cols = [col.name for col in cur.description]
                        except Exception as error:
                            self.errorcode=error
                            await ctx.send("コマンドが実行できませんでした")
                        else:
                            data=cur.fetchall()
                            df=pd.DataFrame(data,columns=cols)
                            self.dflist.append(df)
                            if data==[]:
                                await ctx.send("検索結果が見つかりませんでした")
        self.query+="]\n"

    async def execmd(self,ctx):
        while(1):
            if self.errorcode!="":
                self.breakcode="error"
                break
            elif not self.cmdoplist:
                break
            else:
                item=self.cmdoplist.popleft()
                if item[0]=='?':
                    if self.dflist:
                        self.cmdoplist.appendleft(item)
                        self.cmdoplist.appendleft("and")
                    else:
                        await SQL.cmd2df(self,ctx,item)
                elif item=="and":
                    self.query+="and (inner join on name)\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        df3=pd.merge(df1,df2,how="inner",on="name")
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("列名がnameの列がありません")
                elif item=="or":
                    self.query+="or (outer join on name)\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        df3=pd.merge(df1,df2,how="outer",on="name")
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("列名がnameの列がありません")
                elif item=="inner":
                    join_key=self.opargs.popleft()
                    self.query+=f"inner join on {join_key}\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        join_key=join_key.split(',')
                        df3=pd.merge(df1,df2,how="inner",on=join_key)
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("共通項がありません")
                elif item=="outer":
                    join_key=self.opargs.popleft()
                    self.query+=f"outer join on {join_key}\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        join_key=join_key.split(',')
                        df3=pd.merge(df1,df2,how="outer",on=join_key)
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("共通項がありません")
                elif item=="diff":
                    join_key=self.opargs.popleft()
                    self.query+=f"diff (outer join on {join_key})\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        join_key=join_key.split(',')
                        df3=pd.merge(df1,df2,how="outer",on=join_key,indicator=True)
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("共通項がありません")
                elif item=="left":
                    join_key=self.opargs.popleft()
                    self.query+=f"left join on {join_key}\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        join_key=join_key.split(',')
                        df3=pd.merge(df1,df2,how="left",on=join_key)
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("共通項がありません")
                elif item=="right":
                    join_key=self.opargs.popleft()
                    self.query+=f"rigit join on {join_key}\n"
                    df1=self.dflist.pop()
                    item=self.cmdoplist.popleft()
                    await SQL.cmd2df(self,ctx,item)
                    df2=self.dflist.pop()
                    try:
                        join_key=join_key.split(',')
                        df3=pd.merge(df1,df2,how="right",on=join_key)
                        self.dflist.append(df3)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("共通項がありません")
                elif item=="sort":
                    sort_key_str=self.opargs.popleft()
                    sort_key_list=sort_key_str.split(',')
                    bools=self.opargs.popleft()
                    self.query+=f"sort by {sort_key_str},asc={bools}\n"
                    df=self.dflist.pop()
                    try:
                        df_s=df.sort_values(sort_key_list,ascending=bools).reset_index(drop=True)
                        self.dflist.append(df_s)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("ソートに失敗しました")
                elif item=="drop":
                    drop_key_str=self.opargs.popleft()
                    drop_key_list=drop_key_str.split(',')
                    self.query+=f"drop column {drop_key_list}\n"
                    df=self.dflist.pop()
                    try:
                        df_d=df.drop(columns=drop_key_list).reset_index(drop=True)
                        self.dflist.append(df_d)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("列削除に失敗しました")
                elif item=="loc":
                    loc_key_str=self.opargs.popleft()
                    df=self.dflist.pop()
                    try:
                        if ':' in loc_key_str:
                            loc_key_list=loc_key_str.split(':')
                            df_d=df.loc[:,loc_key_list[0]:loc_key_list[1]].reset_index(drop=True)
                            self.query+=f"loc column {loc_key_str}\n"
                        elif ',' in loc_key_str:
                            loc_key_list=loc_key_str.split(',')
                            df_d=df.loc[:,loc_key_list].reset_index(drop=True)
                            self.query+=f"loc column {loc_key_str}\n"
                        else:
                            loc_key=loc_key_str
                            df_d=pd.DataFrame(df.loc[:,loc_key],columns=[loc_key])
                            self.query+=f"loc column {loc_key_str}\n"
                        self.dflist.append(df_d)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("列抽出に失敗しました")
                elif item=="dup":
                    subset=self.opargs.popleft().split(',')
                    df=self.dflist.pop()
                    try:
                        df_dup=df[df.duplicated(subset=subset,keep=False)]
                        df_dup=df_dup.reset_index(drop=True)
                        self.dflist.append(df_dup)
                        self.query+=f"extract rows with duplicate ({subset})\n"
                    except Exception as error:
                        self.errorcode=error
                        print("重複行の抽出に失敗しました")
                elif item=="unique":
                    uq_check_cols=self.opargs.popleft().split(',')
                    df=self.dflist.pop()
                    try:
                        df_uq=df[~df.duplicated(uq_check_cols)]
                        df_uq=df_uq.reset_index(drop=True)
                        self.dflist.append(df_uq)
                        self.query+=f"drop rows with duplicate ({uq_check_cols})\n"
                    except Exception as error:
                        self.errorcode=error
                        print("重複行の削除に失敗しました")
                elif item=="groupby":
                    groupby_key_str=self.opargs.popleft()
                    groupby_key=groupby_key_str.split(',')
                    groupby_agg=self.opargs.popleft().split(',')
                    agg={}
                    df_g_cols=[key for key in groupby_key]
                    for seg in groupby_agg:
                        col,applys=seg.split(':')
                        applys=applys.split(';')
                        agg[col]=applys
                        for apply in applys:
                            df_g_cols.append(col+'.'+apply)
                    df=self.dflist.pop()
                    self.query+=f"group by {groupby_key_str} \nagg={agg}\n"
                    try:
                        df_g=df.groupby(groupby_key,as_index=False).agg(agg)
                        df_g=df_g.set_axis(df_g_cols,axis=1)
                        df_g=df_g.reset_index(drop=True)
                        self.dflist.append(df_g)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("集約化に失敗しました")
                elif item=="rename":
                    rename_list=self.opargs.popleft().split(',')
                    rename_dict={}
                    for seg in rename_list:
                        origin,changes=seg.split(':')
                        changes=changes
                        rename_dict[origin]=changes
                    df=self.dflist.pop()
                    self.query+=f"rename {rename_dict}"
                    try:
                        df_re=df.rename(columns=rename_dict)
                        df_re=df_re.reset_index(drop=True)
                        self.dflist.append(df_re)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("列名の変更に失敗しました")
                elif item=="show":
                    self.query+="show\n"
                    try:
                        embed = discord.Embed(description=f"""```sql\n{self.query} ```"""
                                            ,color=0x3cc332)
                        await ctx.send(embed=embed)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("クエリが表示制限を超えました")
                elif item=="desc":
                    self.query+="desc"
                    df=self.dflist.pop()
                    orgcols=df.columns.tolist()
                    orgcols.insert(0,"stat")
                    try:
                        df_desc=df.describe(include='all').reset_index(inplace=False)
                        df_desc.columns=orgcols
                        self.dflist.append(df_desc)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("データの要約に失敗しました")
                elif item=="sort":
                    sort_key_str=self.opargs.popleft()
                    sort_key_list=sort_key_str.split(',')
                    bools=self.opargs.popleft()
                    b2s=lambda b:["asc" if tf else "desc" for tf in bools]
                    self.query+=f"sort by {sort_key_str}, asc={b2s(bools)}\n"
                    df=self.dflist.pop()
                    try:
                        df_s=df.sort_values(sort_key_list,ascending=bools).reset_index(drop=True)
                        self.dflist.append(df_s)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("ソートに失敗しました")
                elif item[0]=="`":
                    where=item[1:-1]
                    df=self.dflist.pop()
                    try:
                    #左から順に「?」をargに置換
                        for i in range(where.count('?')):
                            arg=self.args.popleft()
                            if arg=='*':
                                repltable=self.whererepltable
                                search_keys_list=[re.escape(key) for key in repltable.keys()]
                                search_keys=l2s('|',search_keys_list)
                                #辞書のキーのいずれかに一致する文字列を左から探索
                                key=re.search(search_keys,where).group()
                                where=where.replace(key,repltable[key],1)
                            elif arg=='\*':
                                where=where.replace('?','"*"',1)
                            else:
                                where=where.replace('\?',"?",1)
                                where=where.replace('?',f"{arg}",1)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("引数が不足しています")
                    else:
                        try:
                            df_w=df[df.eval(where)].reset_index(drop=True)
                        except:
                            try:
                                df_w=pd.DataFrame(df.eval(where)).reset_index(drop=True)
                            except Exception as error:
                                self.errorcode=error
                                await ctx.send("行抽出が実行できませんでした")
                            else:
                                self.dflist.append(df_w)
                        else:
                            self.dflist.append(df_w)
                    self.query+=f"where {where}\n"
                elif item=="out":
                    self.breakcode="out"
                    break
                elif item=="plot":
                    self.breakcode="plot"
                    break

                """elif item=="dtype":
                    self.query+="dtype"
                    df=self.dflist.pop()
                    try:
                        df_dt=pd.DataFrame(df.dtypes)
                        df_dt.reset_index(inplace=True)
                        df_dt.columns=["column","dtype"]
                        self.dflist.append(df_dt)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("データ型の表示に失敗しました")"""

    async def sqlexe(self,ctx,msg):
        SQL.setvars(self)
        await SQL.msg2cmdop_and_args(self,ctx,msg)
        await SQL.execmd(self,ctx)
        #errorcodeがerrorならpass
        if self.breakcode!="error":
            df=self.dflist.pop()
            if df.empty:
                await ctx.send("検索結果が見つかりませんでした")
            else:
                #実行したmsgを?lastに登録する
                conn=self.bot.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        #実行したmsgに?lastが含まれている場合
                        #?lastを現在?lastに格納されているcmdに置換する
                        if re.search('\?last',msg):
                            cur.execute(f"SELECT cmd FROM sqlcmd WHERE name='last'")
                            last_cmd=cur.fetchone()[0]
                            msg=msg.replace('?last',last_cmd)
                        #lastのcmdにmsgをupsert
                        sql="""
                        INSERT INTO sqlcmd (name,cmd) VALUES (%s,%s) 
                        ON CONFLICT (name) DO UPDATE SET cmd=excluded.cmd"""
                        values=["last",msg]
                        cur.execute(sql,values)
                        conn.commit()
                if self.breakcode=="preview":
                    await SQL.df2out(self,ctx,df,
                                    index=self.showindex,
                                    column=df.columns.values.tolist(),
                                    tablefmt='plain')
                elif self.breakcode=="plot":
                    try:
                        def isint(string):
                            try:
                                integer=int(string)
                            except ValueError:
                                return  string
                            else:
                                return integer
                        pltargs={
                            'kind':"line",
                            'figsize':[4,3],
                            'x':df.columns[0],
                            'y':df.columns[1:]}         
                        if self.opargs[0]!="no entry":
                            plt_setting_str=self.opargs.popleft().split(',')
                            for seg in plt_setting_str:
                                col,applys=seg.split(':')
                                applys=[isint(app) for app in applys.split(';')]
                                sclist=lambda l:l[0] if len(l)==1 else l
                                pltargs[col]=sclist(applys)

                            presets={
                            'pie':{
                                'startangle':90,
                                'counterclock':False,
                                'labels':df[pltargs['x']].tolist(),
                                'autopct':"%1.1f%%"
                                }
                            }
                            if pltargs['kind'] in presets:
                                preset=presets[pltargs['kind']]
                                for key in preset.keys():
                                    if key not in pltargs:
                                        pltargs[key]=preset[key]

                        df2=pd.DataFrame.from_dict(pltargs,orient = "index")
                        df2=df2.reset_index(inplace=False)
                        df2=df2.set_axis(["params","args"],axis=1)
                        await SQL.df2out(self,ctx,df2,
                                    index=self.showindex,
                                    column=df.columns.values.tolist(),
                                    tablefmt='plain')
                        plt.figure()
                        df.plot(**pltargs).legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
                        fname=f'tmp.png'
                        plt.savefig(fname,bbox_inches='tight')
                        plt.close()
                        file = discord.File(fp=fname,filename=f"tmp.png",spoiler=False)
                        await ctx.send(file=file)
                        os.remove(fname)
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("プロットに失敗しました")

                elif self.breakcode=="out":
                    try:
                        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                        # ***.json　は各自ダウンロードしたjsonファイル名に変更
                        credentials = ServiceAccountCredentials.from_json_keyfile_name('database/gas/credentials.json', scope)
                        gc = gspread.authorize(credentials)
                        # スプレッドシートのキー
                        key = os.environ.get("SPREAD_SHEET_KEY")
                        if not key:
                            await ctx.send("環境変数 SPREAD_SHEET_KEY が設定されていません")
                            return
                        workbook = gc.open_by_key(key)
                        worksheet_list = workbook.worksheets()
                        #s1=worksheet_list[self.outoptionpage%5]
                        s1=worksheet_list[0]
                        s1.update_title(msg[:-4])
                        #self.outoptionpage+=1
                        #内容をすべて削除
                        s1.clear()
                        #　1つ目のシートの内容をDiscordに送ったメッセージ内容で更新
                        set_with_dataframe(s1, df)
                        await ctx.send(f"<https://docs.google.com/spreadsheets/d/{key}>")
                    except Exception as error:
                        self.errorcode=error
                        await ctx.send("spread sheetの出力に失敗しました")

    #「?」コマンドを受け取るリスナー
    @commands.Cog.listener(name='on_message')
    async def on_sqlcmd(self,message):
        #botならreturn
        if message.author.bot:
            return
        
        ctx = await self.bot.get_context(message)
        msg=message.content
        #「?」から始まる文字列を受け取ったとき
        try:
            if msg[0]=='?':
                self.develop=0
                if self.develop==1:
                    await SQL.sqlexe(self,ctx,msg)
                #クエリの実行
                else:
                    try:
                        await SQL.sqlexe(self,ctx,msg)
                    except Exception as error:
                        self.errorcode=error
                    #実行できなかった場合
                    if self.errorcode!="":
                        try:
                            embed = discord.Embed(title="ERROR!",
                                        description=f"```{ctx.message.content} ```",
                                        color=0xff0000)
                            embed.add_field(name="Detail",
                                                value=f"```{self.errorcode}```",
                                                inline=False)
                            embed.add_field(name="Query",
                                            value=f"```\n{self.query} ```",
                                            inline=False)
                            embed.add_field(name="HELP",
                                            value=f"```!psql [コマンド名] でコマンドの詳細を確認できます```",
                                            inline=False)
                            await ctx.send(embed=embed,delete_after=120)
                        except:
                            page_desc=[
                                f"ERROR!\n{ctx.message.content}\nDetail\n{self.errorcode}\nHelp\n!psql [コマンド名] でコマンドの詳細を確認できます",
                                f"Query\n{self.query}"]
                            await SQL.pageview(self,ctx,page_desc,color=0xff0000)
        except:
            pass
        
        if message.attachments:
            for attachment in message.attachments:
                file_url=attachment.url
                print(file_url)
                # Attachmentの拡張子が.pdfだった場合
                if ".pdf" in file_url and message.content=="pdf2jpg":
                    #pdfファイルを画像化
                    for attachment in message.attachments:
                        if attachment.content_type != "application/pdf":
                            continue
                        await attachment.save(f"database/pdf/{message.id}.pdf")
                        images = pdf2image.convert_from_path(f"database/pdf/{message.id}.pdf")
                        for index, image in enumerate(images):
                            image.save(f"database/png/{message.id}-{str(index+1)}.png")
                            await message.channel.send(file=discord.File(f"database/png/{message.id}-{str(index+1)}.png"))
                            os.remove(f"database/png/{message.id}-{str(index+1)}.png")
                        os.remove(f"database/pdf/{message.id}.pdf")
                # Attachmentの拡張子が.csvだった場合
                #csvをembedに変換
                elif ".csv" in file_url:
                    for attachment in message.attachments and message.content=="csv2embed":
                        binary = await attachment.read()
                        csvdata=binary.decode("utf-8")
                        df=pd.read_csv(io.StringIO(csvdata))
                        await SQL.df2out(self,ctx,df,column=df.columns.values.tolist(),tablefmt='plain')

                    
async def setup(bot):
    await bot.add_cog(SQL(bot))