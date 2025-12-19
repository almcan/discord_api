import discord
from discord.ext import commands
from cogs.romazi_to_hiragana import RomajiConverter
import json
import os

class Unite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.converter = RomajiConverter(bot)
        self.pokemon_list = []
        self.load_pokemon_list()
        self.draft_sessions = {}
        self.command_history = {}

    def load_pokemon_list(self):
        """all_pokemon_data.json からポケモンの名前リストを読み込む"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # ファイルパス: cogs/unite_info/all_pokemon_data.json
        json_path = os.path.join(base_dir, 'unite_info', 'all_pokemon_data.json')

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # "Name"キーがあるデータから名前を抽出してリストにする
                    self.pokemon_list = [p.get("Name") for p in data if "Name" in p]
                print(f"[Unite] ポケモンリストをロードしました: {len(self.pokemon_list)} 体")
            except Exception as e:
                print(f"[ERROR] ポケモンリストの読み込みに失敗しました: {e}")
                self.pokemon_list = []
        else:
            print(f"[WARNING] ファイルが見つかりません: {json_path}")
            self.pokemon_list = []

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Unite Cog: ログイン完了 - {self.bot.user}")

    @commands.command(name="draft")
    async def start_draft(self, ctx):
        """ポケモンドラフトを開始する"""
        if ctx.channel.id in self.draft_sessions:
            await ctx.send("⚠️ すでにドラフトが進行中です！")
            return

        players = ["先行", "後攻"]
        available_pokemon = set(self.pokemon_list)
        player_teams = {player: [] for player in players}
        ban_list = []
        snake_pick_order = ["先行", "後攻", "後攻", "先行", "先行", "後攻", "後攻", "先行", "先行", "後攻"]

        self.draft_sessions[ctx.channel.id] = {
            "ban_order": players.copy(),
            "pick_order": snake_pick_order.copy(),
            "current_phase": "ban",
            "available_pokemon": available_pokemon,
            "player_teams": player_teams,
            "ban_list": ban_list,
            "pick_count": 0
        }
        self.command_history[ctx.channel.id] = []

        await ctx.send("=== ポケモンユナイト ドラフト練習を開始します ===\n"
                       "BANフェーズを開始します。`!ban <ポケモン名>` でポケモンをBANしてください。\n"
                       "現在の状況は `!list` で確認できます。")
        await ctx.send("**先行** のBANターンです。")

    @commands.command(name="ban")
    async def ban_pokemon(self, ctx, *, pokemon: str):
        """ポケモンをBANする"""
        if ctx.channel.id not in self.draft_sessions:
            await ctx.send("⚠️ ドラフトが開始されていません！`!draft` で開始してください。")
            return

        session = self.draft_sessions[ctx.channel.id]
        if session["current_phase"] != "ban":
            await ctx.send("⚠️ 現在はBANフェーズではありません！")
            return

        pokemon = self.converter.to_katakana(pokemon.strip())
        if pokemon not in session["available_pokemon"]:
            await ctx.send("⚠️ そのポケモンは選択できません（既にBAN/ピック済み、または存在しません）。")
            return

        current_player = session["ban_order"][0]
        session["ban_list"].append(pokemon)
        session["available_pokemon"].remove(pokemon)
        session["ban_order"].append(session["ban_order"].pop(0))
        self.command_history[ctx.channel.id].append({"action": "ban", "pokemon": pokemon, "player": current_player})

        await ctx.send(f"❌ **{current_player}** が **{pokemon}** をBANしました！")

        if len(session["ban_list"]) == 4:
            session["current_phase"] = "pick"
            await ctx.send(f"\n=== BANフェーズ終了 ===\n"
                           f"BANされたポケモン: {', '.join(session['ban_list'])}\n"
                           "ピックフェーズ（スネーク形式）を開始します。`!pick <ポケモン名>` でポケモンを選んでください。\n"
                           f"**{session['pick_order'][0]}** のピックターンです。")
        else:
            next_player = session["ban_order"][0]
            await ctx.send(f"**{next_player}** のBANターンです。")

    @commands.command(name="pick")
    async def pick_pokemon(self, ctx, *, pokemon: str):
        """ポケモンをピックする"""
        if ctx.channel.id not in self.draft_sessions:
            await ctx.send("⚠️ ドラフトが開始されていません！`!draft` で開始してください。")
            return

        session = self.draft_sessions[ctx.channel.id]
        if session["current_phase"] != "pick":
            await ctx.send("⚠️ 現在はピックフェーズではありません！")
            return

        pokemon = self.converter.to_katakana(pokemon.strip())
        if pokemon not in session["available_pokemon"]:
            await ctx.send("⚠️ そのポケモンは選択できません（既にBAN/ピック済み、または存在しません）。")
            return

        current_player = session["pick_order"][0]
        session["player_teams"][current_player].append(pokemon)
        session["available_pokemon"].remove(pokemon)
        session["pick_count"] += 1
        session["pick_order"].pop(0)
        self.command_history[ctx.channel.id].append({"action": "pick", "pokemon": pokemon, "player": current_player})

        await ctx.send(f"✅ **{current_player}** が **{pokemon}** をピックしました！")

        if session["pick_count"] == 10:
            await self.show_draft_result(ctx)
        else:
            next_player = session["pick_order"][0]
            await ctx.send(f"**{next_player}** のピックターンです。")

    async def show_draft_result(self, ctx):
        """ドラフトの結果を表示"""
        session = self.draft_sessions[ctx.channel.id]
        embed = discord.Embed(title="=== ドラフト終了 ===", color=discord.Color.green())
        embed.add_field(name="BANされたポケモン", value=", ".join(session["ban_list"]) or "なし", inline=False)
        embed.add_field(name="先行のチーム", value=", ".join(session["player_teams"]["先行"]), inline=True)
        embed.add_field(name="後攻のチーム", value=", ".join(session["player_teams"]["後攻"]), inline=True)
        await ctx.send(embed=embed)
        del self.draft_sessions[ctx.channel.id]
        del self.command_history[ctx.channel.id]

    @commands.command(name="list")
    async def show_available(self, ctx):
        """ドラフトの全体状況を表示"""
        if ctx.channel.id not in self.draft_sessions:
            await ctx.send("⚠️ ドラフトが開始されていません！`!draft` で開始してください。")
            return

        session = self.draft_sessions[ctx.channel.id]
        embed = discord.Embed(title="現在のドラフト状況", color=discord.Color.blue())
        embed.add_field(name="利用可能なポケモン", 
                        value=", ".join(sorted(session["available_pokemon"])) or "なし", 
                        inline=False)
        embed.add_field(name="BANされたポケモン", 
                        value=", ".join(session["ban_list"]) or "なし", 
                        inline=False)
        embed.add_field(name="先行のピック", 
                        value=", ".join(session["player_teams"]["先行"]) or "未選択", 
                        inline=True)
        embed.add_field(name="後攻のピック", 
                        value=", ".join(session["player_teams"]["後攻"]) or "未選択", 
                        inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="back")
    async def undo_last_action(self, ctx):
        """前回の操作を元に戻す"""
        if ctx.channel.id not in self.command_history or not self.command_history[ctx.channel.id]:
            await ctx.send("⚠️ 戻せる操作がありません！")
            return

        if ctx.channel.id not in self.draft_sessions:
            await ctx.send("⚠️ ドラフトが進行中ではありません！")
            return

        session = self.draft_sessions[ctx.channel.id]
        last_action = self.command_history[ctx.channel.id].pop()

        if last_action["action"] == "ban":
            pokemon = last_action["pokemon"]
            player = last_action["player"]
            session["ban_list"].remove(pokemon)
            session["available_pokemon"].add(pokemon)
            session["ban_order"].insert(0, player)
            session["ban_order"].pop()
            if len(session["ban_list"]) < 4:
                session["current_phase"] = "ban"
            await ctx.send(f"✅ **{pokemon}** のBANを元に戻しました。\n"
                           f"**{player}** のBANターンに戻ります。")

        elif last_action["action"] == "pick":
            pokemon = last_action["pokemon"]
            player = last_action["player"]
            session["player_teams"][player].remove(pokemon)
            session["available_pokemon"].add(pokemon)
            session["pick_count"] -= 1
            original_pick_order = ["先行", "後攻", "後攻", "先行", "先行", "後攻", "後攻", "先行", "先行", "後攻"]
            session["pick_order"].insert(0, player)
            session["pick_order"] = original_pick_order[:session["pick_count"] + 1]
            await ctx.send(f"✅ **{player}** がピックした **{pokemon}** を元に戻しました。\n"
                           f"**{player}** のピックターンに戻ります。")

    @commands.command(name="reset_draft")
    async def reset_draft(self, ctx):
        """ドラフトをリセット"""
        if ctx.channel.id in self.draft_sessions:
            del self.draft_sessions[ctx.channel.id]
            del self.command_history[ctx.channel.id]
            await ctx.send("✅ ドラフトをリセットしました！")
        else:
            await ctx.send("⚠️ リセットするドラフトがありません！")

async def setup(bot):
    await bot.add_cog(Unite(bot))