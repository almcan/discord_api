import discord
from discord.ext import commands
import jaconv
import datetime
import random
import os
from cogs import cmd_card
from cogs.wordle import wordle
IMG_PATH="database/tmp/"
wordle_statuses = {}

#Wordleの回答状況を記録しておくクラス
class Wrodle_Class():
    def __init__(self,pool):
        self.pool = pool
        self.questions = [] # Wordleで使用する単語一覧
        self.question = None
        # self.question = self.questions.pop(random.randrange(len(self.questions))) # 正解(text)
        self.before_Answerer = [None, None] # 直前の回答者と回答した時間、連続回答に制限を付けないのであれば不要
        self.mode = 5 # 絶対値が正解の文字数、負数であれば対戦モード
        self.is_battle = False # 対戦モード（短時間での複数回答に制限）
        self.COOLTIME = 15.0 # 連続回答を避けるためのクールタイム
        self.ans_len = 5 # 正解の文字数
        self.is_correct = ['？']*5 # 現在分かっている文字、不明は「？」
        self.cnt = 1 # 現在の問題に対する回答数
        # 以下は使用済みの文字を表示するためのリスト、多分何かしらのライブラリでもっといい方法がある
        self.char_list = [['ア', 'イ', 'ウ', 'エ', 'オ'],
                        ['カ', 'キ', 'ク', 'ケ', 'コ'],
                        ['サ', 'シ', 'ス', 'セ', 'ソ'],
                        ['タ', 'チ', 'ツ', 'テ', 'ト'],
                        ['ナ', 'ニ', 'ヌ', 'ネ', 'ノ'],
                        ['ハ', 'ヒ', 'フ', 'ヘ', 'ホ'],
                        ['マ', 'ミ', 'ム', 'メ', 'モ'],
                        ['ヤ', ''  , 'ユ', ''  , 'ヨ'],
                        ['ラ', 'リ', 'ル', 'レ', 'ロ'],
                        ['ワ', ''  , 'ン', ''  , 'ー'  ],
                        [''],
                        ['ァ', 'ィ', 'ゥ', 'ェ', 'ォ'],
                        ['ガ', 'ギ', 'グ', 'ゲ', 'ゴ'],
                        ['ザ', 'ジ', 'ズ', 'ゼ', 'ゾ'],
                        ['ダ', 'ヂ', 'ヅ', 'デ', 'ド'],
                        [''  , ''  , 'ッ', ''  , ''  ],
                        ['バ', 'ビ', 'ブ', 'ベ', 'ボ'],
                        ['パ', 'ピ', 'プ', 'ペ', 'ポ'],
                        ['ャ', ''  , 'ュ', ''  , 'ョ'],
                        [''],
                        ['♀', '♂', '・'  , '2' , 'Z' ]]
        self.char_flg = [[0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0],
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0],
                        [0]*5]        
    async def initialize(self):
        self.questions = await wordle.makewordlist(self.pool)
        
        # リストが空でなければ、そこから出題する
        if self.questions:
            self.question = self.questions.pop(random.randrange(len(self.questions)))

    # 文字の使用状況の初期化 
    def char_flg_reset(self):   #0:None, 1:White 2:yellow, 3:green
        self.char_flg = [[0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0],
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0]*5,
                        [0],
                        [0]*5]
        return

    # 判明した文字があればステータスに反映
    def make_status(self):
        txt = ''
        for c in self.is_correct:
            txt += c
        return txt

# wordle_status = Wrodle_Class()

# コマンド一覧
class __WORDLE(commands.Cog, name= 'Pokemon Wordle'):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.wordle_status = Wrodle_Class(self.bot.pool)

        if not os.path.exists(IMG_PATH):
            os.makedirs(IMG_PATH, exist_ok=True)
            print(f"[System] Created directory: {IMG_PATH}")
        
    def get_wordle_status(self, guild_id):
        if guild_id not in wordle_statuses:
            wordle_statuses[guild_id] = Wrodle_Class(self.bot.pool)
        return wordle_statuses[guild_id]
    
    async def cog_load(self):
        await self.wordle_status.initialize()
    
    # 問題設定
    async def set_Question(self, guild_id):
        wordle_status = self.get_wordle_status(guild_id)
        if len(wordle_status.questions) == 0:
            wordle_status.questions = await wordle.makewordlist(wordle_status.pool, mode=wordle_status.mode)  # 問題キューが空なら再度生成
        if len(wordle_status.questions) == 0:
            await self.bot.change_presence(activity=discord.Game(name="問題がありません"))
            return
        wordle_status.question = wordle_status.questions.pop(random.randrange(len(wordle_status.questions)))  # 問題キューから1単語取り出して今回の正解単語とする
        wordle_status.ans_len = len(wordle_status.question)  # 正解の文字数
        wordle_status.cnt = 1  # 回答数の初期化
        wordle_status.is_correct = ['？'] * wordle_status.ans_len  # ステータスの設定
        wordle_status.before_Answerer = [None, None]  # 回答権の初期化
        if wordle_status.mode != 0:  # 文字数の指定があればステータスに現在の回答状況を表示
            activity = discord.Activity(name=f'「{wordle_status.make_status()}」', type=discord.ActivityType.playing)
        else:  # 文字数の指定が無ければステータスに表示しない
            activity = discord.Activity(name=f'Wordle（文字数不明）', type=discord.ActivityType.playing)
        await self.bot.change_presence(activity=activity)
        wordle_status.char_flg_reset()
        return

    # wordle コマンドの変更
    @commands.command()
    async def wordle(self, ctx, poke_name):
        """ポケモン名を回答する"""
        wordle_status = self.get_wordle_status(ctx.guild.id)
        if wordle_status.question is None:
            await self.set_Question(ctx.guild.id)
        poke_name = poke_name.replace('２', '2').replace('Ｚ', 'Z').replace(':male_sign:', '♂').replace(':female_sign:', '♀').replace(':', '：') # 表記揺れがありそうな場所の修正
        converter = self.bot.get_cog('RomajiConverter')
        poke_name = converter.convert(poke_name) # ローマ字→カタカナ変換
        poke_name = jaconv.hira2kata(poke_name) # 平仮名→片仮名変換
        if not wordle.is_correctpokename(wordle_status.pool, poke_name): # 正規のポケモン名であるか判定
            await ctx.send('ポケモン名に誤りがあります。')
            return
        elif wordle_status.mode != 0 and len(poke_name) != wordle_status.mode: # 文字数に制限があれば文字数の確認
            await ctx.send(f'ポケモンは{wordle_status.mode}文字です')
            return

        current_time = datetime.datetime.now()
        try:
            if wordle_status.is_battle and wordle_status.before_Answerer[0] == ctx.author and (current_time - wordle_status.before_Answerer[1]).total_seconds() < wordle_status.COOLTIME: # 回答権の確認
                await ctx.send(f'回答権は{wordle_status.COOLTIME - (current_time - wordle_status.before_Answerer[1]).total_seconds()}秒後に復活します')
                return
        except:
            pass

        if poke_name == wordle_status.question: # 正解の場合
            await ctx.send('CLEAR!\nプレイ回数：' + str(wordle_status.cnt) + '回')
            await self.set_Question(ctx.guild.id)
            return

        wordle_status.before_Answerer = [ctx.author, current_time] # 正解でなければ連続回答防止用に記憶

        question = [x for x in wordle_status.question] # 以下は部分一致の確認、おそらく人がやるのと同じ方法

        l = len(poke_name)
        result_list = [0] * l
        action_change_flg = False
        for i, ans in enumerate(poke_name):
            if result_list[i]:
                continue

            for j in range(len(question)):
                if ans == question[j]:
                    if i == j:
                        result_list[j] = 3
                    elif j < l and poke_name[j] == ans:
                        result_list[j] = 3
                    else:
                        result_list[i] = 2
                    question[j] = None
                    break

            if result_list[i] == 0:
                result_list[i] = 1

        result_txt = ''
        for i, x in enumerate(result_list):
            ans = poke_name[i]
            if x == 3:
                result_txt += ':green_circle:'
                if wordle_status.is_correct[i] != ans:
                    action_change_flg = True
                    wordle_status.is_correct[i] = ans
            if x == 2:
                result_txt += ':yellow_circle:'
            if x == 1:
                result_txt += ':white_circle:'
            charflg = False
            for x1, x2 in zip(wordle_status.char_list, wordle_status.char_flg):
                for y1, y2, list_id in zip(x1, x2, range(len(x1))):
                    if y1 == ans and y2 < x:
                        x2[list_id] = x
                        charflg = True
                        break
                if charflg:
                    break
        wordle_status.cnt += 1

        await ctx.send(result_txt) # 結果の送信
        if action_change_flg:
            if wordle_status.mode != 0:
                act = ''
                for x in wordle_status.is_correct:
                    act += x
                activity = discord.Activity(name=f'「{act}」', type=discord.ActivityType.playing)
            else:
                activity = discord.Activity(name=f'Wordle（文字数不明）', type=discord.ActivityType.playing)
            await self.bot.change_presence(activity=activity)
        return
    
    @commands.command()
    async def w(self, ctx, poke_name):
        """ポケモン名を回答する"""
        # 上記のコマンドと中身が同じ
        wordle_status = self.get_wordle_status(ctx.guild.id)
        if wordle_status.question is None:
            await self.set_Question(ctx.guild.id)
        poke_name = poke_name.replace('２', '2').replace('Ｚ', 'Z').replace(':male_sign:', '♂').replace(':female_sign:', '♀').replace(':', '：')
        converter = self.bot.get_cog('RomajiConverter')
        if converter:
            poke_name = converter.to_katakana(poke_name)
        poke_name = jaconv.hira2kata(poke_name)
        if await wordle.is_correctpokename(wordle_status.pool, poke_name) == False:
            await ctx.send('ポケモン名に誤りがあります。')
            return
        elif (wordle_status.mode != 0 and len(poke_name) != wordle_status.mode):
            await ctx.send(f'ポケモンは{wordle_status.mode}文字です')
            return

        current_time = datetime.datetime.now()
        try:
            if (wordle_status.is_battle and wordle_status.before_Answerer[0] == ctx.author and (current_time - wordle_status.before_Answerer[1]).total_seconds() < wordle_status.COOLTIME):
                await ctx.send(f'回答権は{wordle_status.COOLTIME-(current_time - wordle_status.before_Answerer[1]).total_seconds()}秒後に復活します')
                return
        except:
            pass
        
        if (poke_name == wordle_status.question):
            await ctx.send('CLEAR!\nプレイ回数：'+str(wordle_status.cnt)+'回')
            await self.set_Question(ctx.guild.id)
            return
        
        wordle_status.before_Answerer = [ctx.author, current_time]

        question = [x for x in wordle_status.question]

        l = len(poke_name)
        result_list = [0] * l
        action_change_flg = False
        for i, ans in enumerate(poke_name):
            if (result_list[i]):
                continue
            
            for j in range(len(question)):
                if (ans == question[j]):
                    if (i == j):
                        result_list[j] = 3
                    elif (j < l and poke_name[j] == ans):
                        result_list[j] = 3
                    else:
                        result_list[i] = 2
                    question[j] = None
                    break
            
            if (result_list[i] == 0):
                result_list[i] = 1

        result_txt = ''
        for i, x in enumerate(result_list):
            ans = poke_name[i]
            if (x == 3):
                result_txt += ':green_circle:'
                if (wordle_status.is_correct[i] != ans):
                    action_change_flg = True
                    wordle_status.is_correct[i] = ans
            if (x == 2):
                result_txt += ':yellow_circle:'
            if (x == 1):
                result_txt += ':white_circle:'
            charflg = False
            for x1, x2 in zip(wordle_status.char_list, wordle_status.char_flg):
                for y1, y2, list_id in zip(x1, x2, range(len(x1))):
                    if (y1 == ans and y2 < x):
                        x2[list_id] = x
                        charflg = True
                        break
                if charflg:
                    break

        wordle_status.cnt += 1

        await ctx.send( result_txt)
        if (action_change_flg):
            if (wordle_status.mode != 0):
                act = ''
                for x in wordle_status.is_correct:
                    act += x
                activity = discord.Activity(name=f'「{act}」', type=discord.ActivityType.playing)
            else:
                activity = discord.Activity(name=f'Wordle（文字数不明）', type=discord.ActivityType.playing)
            await self.bot.change_presence(activity=activity)
        return
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        channel_id = message.channel.id
        if channel_id != 1354847926874145024:  # ここに特定のチャンネルIDを設定
            return

        poke_name = message.content
        if poke_name.startswith('!'):
            return

        wordle_status = self.get_wordle_status(ctx.guild.id)
        if wordle_status.question is None:
            await self.set_Question(ctx.guild.id)
        poke_name = poke_name.replace('２', '2').replace('Ｚ', 'Z').replace(':male_sign:', '♂').replace(':female_sign:', '♀').replace(':', '：')
        converter = self.bot.get_cog('RomajiConverter')
        if converter:
            poke_name = converter.to_katakana(poke_name)
        poke_name = jaconv.hira2kata(poke_name)
        if not await wordle.is_correctpokename(wordle_status.pool, poke_name):
            await ctx.send('ポケモン名に誤りがあります。')
            return
        elif wordle_status.mode != 0 and len(poke_name) != wordle_status.mode:
            await ctx.send(f'ポケモンは{wordle_status.mode}文字です')
            return

        current_time = datetime.datetime.now()
        try:
            if wordle_status.is_battle and wordle_status.before_Answerer[0] == message.author and (current_time - wordle_status.before_Answerer[1]).total_seconds() < wordle_status.COOLTIME:
                await ctx.send(f'回答権は{wordle_status.COOLTIME - (current_time - wordle_status.before_Answerer[1]).total_seconds()}秒後に復活します')
                return
        except:
            pass

        if poke_name == wordle_status.question:
            await ctx.send('CLEAR!\nプレイ回数：' + str(wordle_status.cnt) + '回')
            await self.set_Question(ctx.guild.id)
            return

        wordle_status.before_Answerer = [message.author, current_time]

        question = [x for x in wordle_status.question]

        l = len(poke_name)
        result_list = [0] * l
        action_change_flg = False
        for i, ans in enumerate(poke_name):
            if result_list[i]:
                continue

            for j in range(len(question)):
                if ans == question[j]:
                    if i == j:
                        result_list[j] = 3
                    elif j < l and poke_name[j] == ans:
                        result_list[j] = 3
                    else:
                        result_list[i] = 2
                    question[j] = None
                    break

            if result_list[i] == 0:
                result_list[i] = 1

        result_txt = ''
        for i, x in enumerate(result_list):
            ans = poke_name[i]
            if x == 3:
                result_txt += ':green_circle:'
                if wordle_status.is_correct[i] != ans:
                    action_change_flg = True
                    wordle_status.is_correct[i] = ans
            if x == 2:
                result_txt += ':yellow_circle:'
            if x == 1:
                result_txt += ':white_circle:'
            charflg = False
            for x1, x2 in zip(wordle_status.char_list, wordle_status.char_flg):
                for y1, y2, list_id in zip(x1, x2, range(len(x1))):
                    if y1 == ans and y2 < x:
                        x2[list_id] = x
                        charflg = True
                        break
                if charflg:
                    break
        wordle_status.cnt += 1

        await ctx.send(result_txt)
        if action_change_flg:
            if wordle_status.mode != 0:
                act = ''
                for x in wordle_status.is_correct:
                    act += x
                activity = discord.Activity(name=f'「{act}」', type=discord.ActivityType.playing)
            else:
                activity = discord.Activity(name=f'Wordle（文字数不明）', type=discord.ActivityType.playing)
            await self.bot.change_presence(activity=activity)
        return

    @commands.command()
    async def wordlemode(self, ctx, poke_len):
        """ 0:全解禁 3~6:文字数指定 負数:対戦モード(全解禁は-7以下) """
        wordle_status = self.get_wordle_status(ctx.guild.id)  # サーバーごとの wordle_status を取得
        await ctx.send('CORRECT:' + wordle_status.question + '\nプレイ回数：' + str(wordle_status.cnt - 1) + '回')
        try:
            wordle_status.mode = int(poke_len)
        except ValueError:
            await ctx.send('引数にはポケモンの文字数または0を指定してください')
            wordle_status.mode = 5

        if wordle_status.mode < 0:
            wordle_status.is_battle = True
            wordle_status.before_Answerer = None
            wordle_status.mode = -1 * wordle_status.mode
        else:
            wordle_status.is_battle = False

        if wordle_status.mode < 3 or wordle_status.mode > 6:
            wordle_status.mode = 0

        wordle_status.questions = await wordle.makewordlist(wordle_status.pool, mode=wordle_status.mode)
        await self.set_Question(ctx.guild.id)

        return
    
    @commands.command()
    async def wmode(self, ctx, poke_len):
        """ 0:全解禁 3~6:文字数指定 負数:対戦モード(全解禁は-7以下) """
        wordle_status = self.get_wordle_status(ctx.guild.id)  # サーバーごとの wordle_status を取得
        await ctx.send('CORRECT:' + wordle_status.question + '\nプレイ回数：' + str(wordle_status.cnt - 1) + '回')
        try:
            wordle_status.mode = int(poke_len)
        except ValueError:
            await ctx.send('引数にはポケモンの文字数または0を指定してください')
            wordle_status.mode = 5

        if wordle_status.mode < 0:
            wordle_status.is_battle = True
            wordle_status.before_Answerer = None
            wordle_status.mode = -1 * wordle_status.mode
        else:
            wordle_status.is_battle = False

        if wordle_status.mode < 3 or wordle_status.mode > 6:
            wordle_status.mode = 0

        wordle_status.questions = await wordle.makewordlist(wordle_status.pool, mode=wordle_status.mode)
        await self.set_Question(ctx.guild.id)

        return

    @commands.command()
    async def wrem(self, ctx):
        """ 使用した文字の一覧を表示 """
        wordle_status = self.get_wordle_status(ctx.guild.id)
        # 使用状況の画像生成。処理が遅いので注意。IMG_PATHは画像の保存先
        cmd_card.make_Japanese_syllabary_table(wordle_status.char_flg, wordle_status.char_list, IMG_PATH, wordle_status.make_status(), print_current_name=(wordle_status.mode != 0))
        file_img = discord.File(IMG_PATH + 'table.jpg')
        await ctx.send(file=file_img)
        return

    @commands.command()
    async def wordleremaining(self, ctx):
        """ 使用した文字の一覧を表示 """
        wordle_status = self.get_wordle_status(ctx.guild.id)
        cmd_card.make_Japanese_syllabary_table(wordle_status.char_flg, wordle_status.char_list, IMG_PATH, wordle_status.make_status(), print_current_name=(wordle_status.mode != 0))
        file_img = discord.File(IMG_PATH + 'table.jpg')
        await ctx.send(file=file_img)
        return

    @commands.command()
    async def howtoplay(self, ctx):
        """ Wordleの遊び方を表示 """
        text="1. 特に設定しなければポケモンの名前が5文字のモードになっています。正しいポケモン名を入力すると、結果が表示されます。ひらがな・カタカナの両方に対応しています。\n\n2. `!wrem`とDiscordにメッセージを送信すると、今まで使用した文字が一覧表示されます。\n\n3. ポケモン名を正確に当てることができればクリアです！\n\n※ `!wmode -7~6のいずれか`とDiscordにメッセージを送信すると、ゲームの設定をすることができます。デフォルトは`!wmode 5`です。\n\n指定する数字: 設定\n0: 全解禁(メガあり・フォルムなし)\n1 ~ 6: 文字数指定(1~6文字)\n-1 ~ -6: 対戦モード(文字数指定)\n-7: 対戦モード(全解禁)`"
        embed = discord.Embed(title="Wordleの遊び方",description=text) # まずは普通にEmbedを定義
        fname="howtoplay.png" # アップロードするときのファイル名 自由に決めて良いですが、拡張子を忘れないように
        file = discord.File(fp=IMG_PATH+fname,filename=fname,spoiler=False) # ローカル画像からFileオブジェクトを作成
        embed.set_image(url=f"attachment://{fname}") # embedに画像を埋め込むときのURLはattachment://ファイル名        
        await ctx.send(file=file, embed=embed)
        return
    
    #「?」コマンドを受け取るリスナー
    @commands.Cog.listener(name='on_message')
    async def on_sqlcmd(self,message):
        #botならreturn
        if message.author.bot:
            return
        
        ctx = await self.bot.get_context(message)
        channel_name=message.channel.name
        if channel_name!="wordleで遊ぶ場所":
            return
        
        poke_name=message.content
        # ポケモン名を受け取った場合、!wコマンドを実行
        if poke_name[0]=='!':
            return
        wordle_status = self.get_wordle_status(ctx.guild.id)
        poke_name = poke_name.replace('２', '2').replace('Ｚ', 'Z').replace(':male_sign:', '♂').replace(':female_sign:', '♀').replace(':', '：') # 表記揺れがありそうな場所の修正
        converter = self.bot.get_cog('RomajiConverter')
        if converter:
            poke_name = converter.to_katakana(poke_name)
        poke_name  = jaconv.hira2kata(poke_name) # 平仮名→片仮名変換
        if (wordle.is_correctpokename(poke_name) == False): # 正規のポケモン名であるか判定
            await ctx.send('ポケモン名に誤りがあります。')
            return
        elif (wordle_status.mode != 0 and len(poke_name) != wordle_status.mode): #文字数に制限があれば文字数の確認
            await ctx.send(f'ポケモンは{wordle_status.mode}文字です')
            return
        else:
            current_time = datetime.datetime.now()
            try:
                if (wordle_status.is_battle and wordle_status.before_Answerer[0] == ctx.author and (current_time - wordle_status.before_Answerer[1]).total_seconds() < wordle_status.COOLTIME): # 回答権の確認
                    await ctx.send(f'回答権は{wordle_status.COOLTIME-(current_time - wordle_status.before_Answerer[1]).total_seconds()}秒後に復活します')
                    return
            except:
                pass
            
            if (poke_name == wordle_status.question): # 正解の場合
                await ctx.send('CLEAR!\nプレイ回数：'+str(wordle_status.cnt)+'回')
                await self.set_Question(ctx.guild.id)
                return
            
            wordle_status.before_Answerer = [ctx.author, current_time] # 正解でなければ連続回答防止用に記憶

            question = [x for x in wordle_status.question] # 以下は部分一致の確認、おそらく人がやるのと同じ方法

            l = len(poke_name)
            result_list = [0] * l
            action_change_flg = False
            for i, ans in enumerate(poke_name):
                if (result_list[i]):
                    continue
                
                for j in range(len(question)):
                    if (ans == question[j]):
                        if (i == j):
                            result_list[j] = 3
                        elif (j < l and poke_name[j] == ans):
                            result_list[j] = 3
                        else:
                            result_list[i] = 2
                        question[j] = None
                        break
                
                if (result_list[i] == 0):
                    result_list[i] = 1

            result_txt = ''
            for i, x in enumerate(result_list):
                ans = poke_name[i]
                if (x == 3):
                    result_txt += ':green_circle:'
                    if (wordle_status.is_correct[i] != ans):
                        action_change_flg = True
                        wordle_status.is_correct[i] = ans
                if (x == 2):
                    result_txt += ':yellow_circle:'
                if (x == 1):
                    result_txt += ':white_circle:'
                charflg = False
                for x1, x2 in zip(wordle_status.char_list, wordle_status.char_flg):
                    for y1, y2, list_id in zip(x1, x2, range(len(x1))):
                        if (y1 == ans and y2 < x):
                            x2[list_id] = x
                            charflg = True
                            break
                    if charflg:
                        break
            wordle_status.cnt += 1

            await ctx.send(result_txt) # 結果の送信
            if (action_change_flg):
                if (wordle_status.mode != 0):
                    act = ''
                    for x in wordle_status.is_correct:
                        act += x
                    activity = discord.Activity(name=f'「{act}」', type=discord.ActivityType.playing)
                else:
                    activity = discord.Activity(name=f'Wordle（文字数不明）', type=discord.ActivityType.playing)
                await self.bot.change_presence(activity=activity)
            return

async def setup(bot):
    await bot.add_cog(__WORDLE(bot))
