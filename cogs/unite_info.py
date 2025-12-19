import io
import discord
from discord.ext import commands
import json
import os
import math # ステータス表示の分割用
import asyncio # 連投対策用

# pokemon_info.py がある cogs ディレクトリの絶対パスを取得
cog_dir = os.path.dirname(os.path.abspath(__file__))
# JSONファイルのパスを構築 (cogs/unite_info/all_pokemon_data.json)
JSON_FILE_PATH = os.path.join(cog_dir, 'unite_info', 'all_pokemon_data.json')

def load_pokemon_data():
    """JSONファイルを読み込み、ポケモン名をキーとする辞書に変換する"""
    # print(f"デバッグ: JSONファイルパス -> {JSON_FILE_PATH}")
    try:
        # UTF-8を指定してファイルを開く
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            # ポケモン名をキーとする辞書に変換
            pokemon_dict = {item['Name']: item for item in data_list if 'Name' in item}
            print(f"ポケモンデータロード成功: {len(pokemon_dict)} 件")
            return pokemon_dict
    except FileNotFoundError:
        print(f"エラー: {JSON_FILE_PATH} が見つかりません。")
        return {}
    except json.JSONDecodeError as e:
        print(f"エラー: {JSON_FILE_PATH} のJSON形式が正しくありません。エラー箇所: {e}")
        return {}
    except Exception as e:
        print(f"ポケモンデータの読み込み中に予期せぬエラーが発生しました: {e}")
        return {}

class UniteInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pokemon_data = {}
        self.reload_data()

    def reload_data(self):
        """JSONファイルからポケモンデータを再読み込みする"""
        print("UniteInfoCog: ポケモンデータの再読み込みを開始します...")
        self.pokemon_data = load_pokemon_data()
        if not self.pokemon_data:
            print("警告(再読み込み): ポケモンデータが空です。")
        else:
            print(f"UniteInfoCog: {len(self.pokemon_data)}件のポケモンデータを再読み込みしました。")
        return bool(self.pokemon_data)

    @commands.command(name='unite', aliases=['ユナイト'])
    async def unite_command(self, ctx, *, pokemon_name: str):
        """指定されたポケモンのユナイト情報を表示します"""
        await self.send_pokemon_info(ctx, pokemon_name)

    # スラッシュコマンド用の定義例 (必要ならコメント解除)
    @discord.app_commands.command(name="unite", description="指定されたポケモンのユナイト情報を表示します")
    @discord.app_commands.describe(pokemon_name="ポケモンの名前 (カタカナ or ローマ字)")
    async def unite_slash_command(self, interaction: discord.Interaction, pokemon_name: str):
        await interaction.response.defer(ephemeral=False)
        await self.send_pokemon_info(interaction, pokemon_name)

    async def send_pokemon_info(self, context, pokemon_name):
        """ポケモン情報を検索して複数のEmbed/ファイルで送信する共通処理"""
        pokemon_name = pokemon_name.strip()

        is_interaction = isinstance(context, discord.Interaction)
        send_func = context.followup.send if is_interaction else context.send
        error_send_func = context.followup.send if is_interaction else context.send
        error_ephemeral = is_interaction

        if not self.pokemon_data:
            await error_send_func("ポケモンデータを読み込めませんでした。", ephemeral=error_ephemeral)
            return

        # --- 検索処理 (ローマ字変換対応) ---
        pokemon_info = None
        katakana_name_attempt = None
        if pokemon_name in self.pokemon_data:
            pokemon_info = self.pokemon_data[pokemon_name]
            # print(f"デバッグ: カタカナ名 '{pokemon_name}' でヒット")
        else:
            converter_cog = self.bot.get_cog('RomajiConverter')
            if converter_cog:
                katakana_name_attempt = converter_cog.to_katakana(pokemon_name.lower())
                # print(f"デバッグ: ローマ字入力かも？ '{pokemon_name}' -> '{katakana_name_attempt}' で再検索")
                if katakana_name_attempt in self.pokemon_data:
                    pokemon_info = self.pokemon_data[katakana_name_attempt]
                    # print(f"デバッグ: カタカナ変換名 '{katakana_name_attempt}' でヒット")

        # --- 検索結果の処理 ---
        if not pokemon_info:
            error_message = f"`{pokemon_name}` という名前のポケモンは見つかりませんでした。"
            if katakana_name_attempt and katakana_name_attempt != pokemon_name:
                 error_message += f" (カタカナ `{katakana_name_attempt}` でも見つかりません)"
            await error_send_func(error_message, ephemeral=error_ephemeral)
            return

        pokemon_display_name = pokemon_info.get('Name', '名前なし')

        # --- Embed 1: 基本情報と特性 ---
        try:
            embed1 = discord.Embed(
                title=f"{pokemon_display_name} の基本情報",
                description=f"Wikiページ: {pokemon_info.get('URL', '情報なし')}",
                color=discord.Color.blue()
            )

            # 特性
            abilities = pokemon_info.get('Abilities', [])
            if abilities:
                ability_text = ""
                for ability in abilities:
                    stage_info = f" ({ability.get('Stage')})" if ability.get('Stage') else ""
                    ability_desc = ability.get('Description', '説明なし')
                    if len(ability_text) + len(ability.get('Name', '')) + len(stage_info) + len(ability_desc) < 1000:
                         ability_text += f"**{ability.get('Name', '特性名不明')}{stage_info}**\n{ability_desc}\n\n"
                    else:
                         ability_text += f"**{ability.get('Name', '特性名不明')}{stage_info}**\n(説明省略)\n\n"
                embed1.add_field(name="特性", value=ability_text.strip() or "情報なし", inline=False)
            else:
                 embed1.add_field(name="特性", value="情報なし", inline=False)

            # --- 通常攻撃の情報ここから ---
            basic_attack_field_title = "通常攻撃"
            basic_attack_field_content = [] # 表示内容を一時的に格納するリスト

            # 1. 通常攻撃の効果（説明文）を取得・整形
            # BasicAttacks リスト (通常、状態別の説明がここにある想定)
            if 'BasicAttacks' in pokemon_info and isinstance(pokemon_info['BasicAttacks'], list) and pokemon_info['BasicAttacks']:
                for attack_info in pokemon_info['BasicAttacks']:
                    condition = attack_info.get('ConditionRaw') or attack_info.get('Condition')
                    description = attack_info.get('Description', '').strip()
                    
                    if description and description != "取得失敗":
                        condition_text = ""
                        # "Default" の場合はConditionを表示しないか、あるいは特定のポケモンでは表示するかを検討
                        # 例: ウーラオスのようにCondition名が重要な場合は表示する
                        if condition and condition.lower() != 'default': 
                            condition_text = f"**[{condition.strip()}]**\n"
                        basic_attack_field_content.append(f"{condition_text}{description}")
            
            # BasicAttacks に説明がなかった場合のフォールバックとして BasicAttack辞書のDescriptionも見る (オプション)
            if not basic_attack_field_content: 
                if 'BasicAttack' in pokemon_info and isinstance(pokemon_info['BasicAttack'], dict):
                    desc_from_dict = pokemon_info['BasicAttack'].get('Description', '').strip()
                    if desc_from_dict and desc_from_dict != "取得失敗":
                        basic_attack_field_content.append(desc_from_dict)

            if not basic_attack_field_content: # それでも説明がなければ
                basic_attack_field_content.append("通常攻撃の説明情報なし")

            # 2. 通常攻撃のダメージ計算式を取得・整形
            # BasicAttack 辞書 (計算式はここにある想定)
            damage_formulas_list = []
            if 'BasicAttack' in pokemon_info and isinstance(pokemon_info['BasicAttack'], dict):
                basic_attack_formulas = pokemon_info['BasicAttack']
                for key, value in basic_attack_formulas.items():
                    if key.startswith("DamageFormula"):
                        formula_type = key.replace("DamageFormula_", "").replace('_', ' ').title()
                        damage_formulas_list.append(f"- `{formula_type}`: `{value}`")
            
            if damage_formulas_list: # 計算式が1つでもあれば
                # 説明文と計算式の間に空行を入れるために、一度現在の内容を結合してから追加
                if basic_attack_field_content and basic_attack_field_content[-1].strip(): # 最後の要素が空行でなければ
                    basic_attack_field_content.append("") # 空行を追加
                basic_attack_field_content.append("**ダメージ計算式:**") # ヘッダーを追加
                basic_attack_field_content.extend(damage_formulas_list) # 各計算式を追加
            # else: # 計算式がない場合は何も追加しない (または「計算式なし」と明記も可能)
                # basic_attack_field_content.append("\nダメージ計算式情報なし") # 例

            # 最終的な表示文字列を組み立て
            final_basic_attack_text = "\n".join(basic_attack_field_content).strip()

            # 文字数制限とフィールド追加
            if len(final_basic_attack_text) > 1020: # Discordのフィールド値の文字数制限ケア
                final_basic_attack_text = final_basic_attack_text[:1020] + "..."
            
            embed1.add_field(name=basic_attack_field_title, value=final_basic_attack_text or "情報なし", inline=False)
            # --- 通常攻撃の情報ここまで ---

            await send_func(embed=embed1)
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Embed 1 ({pokemon_display_name}) 作成/送信エラー: {e}")
            await error_send_func("基本情報の表示中にエラーが発生しました。", ephemeral=error_ephemeral)

        # --- Embed 2...: わざ詳細 ---
        moves = pokemon_info.get('Moves', [])
        if moves:
            moves_per_embed = 3
            num_move_embeds = math.ceil(len(moves) / moves_per_embed)
            for i in range(num_move_embeds):
                try:
                    embed_moves = discord.Embed(
                        title=f"{pokemon_display_name} のわざ ({i+1}/{num_move_embeds})",
                        color=discord.Color.orange()
                    )
                    start_index = i * moves_per_embed
                    end_index = start_index + moves_per_embed
                    current_moves = moves[start_index:end_index]
                    for move in current_moves:
                        move_name = move.get('Name', '技名不明')
                        cooldown = f"(CD: {move.get('Cooldown', '-')})"
                        description = move.get('Description', '説明なし')
                        upgrade_desc = f"\n**[＋]** {move.get('UpgradeDescription', '')}" if move.get('UpgradeDescription') else ""
                        formula_text = ""
                        for key, value in move.items():
                             if 'Formula' in key or 'Recovery' in key:
                                 clean_key = key.replace('DamageFormula_', '').replace('HPRecovery', 'HP回復').replace('ShieldFormula_', 'シールド').replace('_', ' ').replace('Base', '基礎').replace('Upgraded', '+').replace('Additional', '追加').replace('Stage', '段階').replace('PerHit', 'ヒット毎').title()
                                 formula_text += f"\n- `{clean_key}`: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}"
                        value_text = f"{description}{upgrade_desc}{formula_text}"
                        if len(value_text) > 1020:
                           value_text = value_text[:1020] + "..."
                        embed_moves.add_field(name=f"{move_name} {cooldown}", value=value_text, inline=False)
                    await send_func(embed=embed_moves)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Embed (わざ {i+1}, {pokemon_display_name}) 作成/送信エラー: {e}")
                    await error_send_func("わざ情報の表示中にエラーが発生しました。", ephemeral=error_ephemeral)
                    break
        else:
             try:
                 embed_no_moves = discord.Embed(
                      title=f"{pokemon_display_name} のわざ",
                      description="わざ情報が登録されていません。",
                      color=discord.Color.orange()
                 )
                 await send_func(embed=embed_no_moves)
                 await asyncio.sleep(0.1)
             except Exception as e:
                 print(f"Embed (わざなし, {pokemon_display_name}) 作成/送信エラー: {e}")

        # --- ステータス表 (テキストファイルで送信) ---
        level_stats = pokemon_info.get('LevelStats', [])
        if level_stats:
            try:
                stats_file_content = f"--- {pokemon_display_name} の全レベルステータス ---\n\n"
                header_keys = list(level_stats[0].keys()) if level_stats else []
                col_widths = {}
                for key in header_keys:
                    max_width = len(key)
                    for stat_data in level_stats:
                        max_width = max(max_width, len(str(stat_data.get(key, '-'))))
                    col_widths[key] = max_width + 1
                header_line_parts = [f"{key:<{col_widths[key]}}" for key in header_keys]
                header_line = " | ".join(header_line_parts)
                stats_file_content += header_line + "\n"
                stats_file_content += "-" * len(header_line) + "\n"
                for stat_data in level_stats:
                     line_values = []
                     for key in header_keys:
                         value = stat_data.get(key, '-')
                         display_value = str(value)[:col_widths[key]].ljust(col_widths[key])
                         line_values.append(display_value)
                     stats_file_content += " | ".join(line_values) + "\n"

                stats_buffer = io.BytesIO(stats_file_content.encode('utf-8'))
                stats_buffer.seek(0) # バッファの読み込み位置を先頭に戻す

                # 送信時のファイル名を決定
                safe_pokemon_name = "".join(c if c.isalnum() else "_" for c in pokemon_display_name)
                filename = f"{safe_pokemon_name}_stats.txt"

                # ディスクに保存せず、メモリ上のデータ(stats_buffer)を直接渡す
                await send_func(
                    f"**{pokemon_display_name}** の全レベルステータスはこちらです:", 
                    file=discord.File(stats_buffer, filename=filename)
                )
            except Exception as e:
                print(f"ステータスファイル ({pokemon_display_name}) 作成/送信エラー: {e}")
                await error_send_func("ステータス情報の表示中にエラーが発生しました。", ephemeral=error_ephemeral)
        else:
            await send_func(f"{pokemon_display_name} のステータス情報が見つかりませんでした。")

# CogをBotに追加するための必須関数
async def setup(bot):
    if bot.get_cog('RomajiConverter') is None:
        print("警告: RomajiConverter Cogがロードされていません。ローマ字入力に対応できません。")
        # 必要に応じてここでロード処理を追加
        # try:
        #     await bot.load_extension('cogs.romaji_converter')
        #     print("RomajiConverter Cog をロードしました。")
        # except Exception as e:
        #     print(f"RomajiConverter Cog のロードに失敗しました: {e}")
    await bot.add_cog(UniteInfoCog(bot))
    print("UniteInfoCog をロードしました。")