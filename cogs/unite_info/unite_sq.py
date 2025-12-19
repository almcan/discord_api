# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup, Tag
import time
import re
import json
import traceback
import os
from patterns_config import formula_patterns

output_dir = os.path.dirname(os.path.abspath(__file__))
url_list_file = os.path.join(output_dir, "pokemon_urls.json")

# --- 関数: 改行をスペースに置換し、連続スペースをまとめる ---
def clean_text(text):
    """テキスト内の改行やタブなどをスペースに置換し、連続するスペースを1つにまとめる"""
    if not isinstance(text, str):
        return text
    # HTMLタグを除去する処理を追加
    text_no_tags = re.sub(r'<.*?>', '', text)
    cleaned = re.sub(r'\s+', ' ', text_no_tags).strip()
    return cleaned

# --- ポケモンデータ抽出関数 ---
def scrape_pokemon_data(driver, url):
    """指定されたURLからポケモンデータを抽出する関数"""
    pokemon_data = {'URL': url}
    start_time = time.time()

    try:
        # --- WebDriverの設定 ---

        # --- 目的のウェブサイトにアクセス ---
        print(f"\n--- 処理開始 ({url.split('/')[-1]}) ---")
        print(f"アクセス中: {url}")
        driver.get(url)

        # --- アコーディオンをクリックして開く処理 ---
        try:
            print("アコーディオン展開を試みます...")
            # 待機時間を最大10秒に設定（回線が遅い場合への保険。早ければ0.1秒で通過します）
            wait = WebDriverWait(driver, 10)

            # 1. 「わざや特性の仕様と詳細」アコーディオン
            accordion_header_xpath_1 = "//*[self::h3 or self::h4][contains(@class, 'accordion-header') and contains(., 'わざや特性の仕様と詳細')]"
            # ヘッダーがクリック可能になるまで待つ
            accordion_header_1 = wait.until(EC.element_to_be_clickable((By.XPATH, accordion_header_xpath_1)))
            driver.execute_script("arguments[0].click();", accordion_header_1)
            
            # 【重要】クリック後、中身のテーブルが表示されるまで待つ
            # ここでは「わざや特性」の中にあるはずのテーブル(theadが存在するものなど)の出現を待ちます
            # 特定が難しい場合は汎用的に .accordion-content の可視化を待ちますが、より具体的に待つ方が確実です
            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'accordion-content')]//table")))
                print("  -> 「わざや特性」展開確認")
            except:
                print("  -> 「わざや特性」展開確認の待機がタイムアウト（既に開いているか、中身がない可能性があります）")


            # 2. 「レベル別ステータス表」アコーディオン
            accordion_header_xpath_2 = "//*[self::h3 or self::h4][contains(., 'レベル別ステータス表')]"
            accordion_header_2 = wait.until(EC.element_to_be_clickable((By.XPATH, accordion_header_xpath_2)))
            driver.execute_script("arguments[0].click();", accordion_header_2)

            # 【重要】「レベル」という文字を含むヘッダーセルが表示されるまで待つ
            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, "//table//td[contains(text(), 'レベル')] | //table//th[contains(text(), 'レベル')]")))
                print("  -> 「レベル別ステータス」展開確認")
            except:
                 print("  -> 「レベル別ステータス」展開確認の待機がタイムアウト")

            print("アコーディオン展開処理完了。")

        except Exception as click_error:
            print(f"警告: アコーディオン展開処理中に問題が発生: {click_error}")
            # 失敗しても処理は続行させる（既に開いている場合などがあるため）

        # --- HTMLソース取得と解析 ---
        print("HTMLソースを取得・解析します...")
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        print("HTML解析完了。データ抽出を開始します。")

        # 1. ポケモンの名前
        try:
            pokemon_name_tag = soup.find('h1', class_='title')
            pokemon_data['Name'] = clean_text(pokemon_name_tag.string) if pokemon_name_tag and pokemon_name_tag.string else "取得失敗"
        except Exception as e: pokemon_data['Name'] = f"取得エラー: {e}"
        print(f"  ポケモン名: {pokemon_data.get('Name', 'N/A')}")

        # 2. 進化レベル (案B: リスト形式)
        pokemon_data['EvolutionLevels'] = [] # キー名を複数形にし、デフォルトを空リストに
        try:
            # テーブル特定ロジック (変更なし)
            evolution_header = soup.find('th', string=re.compile(r'^\s*進化\s*$'))
            evolution_table = None
            if evolution_header: evolution_table = evolution_header.find_parent('table')
            # ヘッダーから見つからない場合のフォールバック (変更なし)
            if not evolution_table:
                level_imgs_alt_search = soup.find_all('img', alt=re.compile(r'lvl\d+\.png'))
                if level_imgs_alt_search:
                     # 画像を含むテーブルを探す (より堅牢な方法も検討可)
                     potential_table = level_imgs_alt_search[0].find_parent('table')
                     if potential_table: evolution_table = potential_table

            levels_found = [] # 見つかったレベルを入れるリスト
            if evolution_table:
                # テーブルからレベル画像を検索
                level_imgs = evolution_table.find_all('img', alt=re.compile(r'lvl(\d+)\.png'))
                # alt属性からレベル数値を抽出しリストに追加
                for img in level_imgs:
                     match = re.search(r'lvl(\d+)\.png', img.get('alt',''))
                     if match:
                         try:
                             levels_found.append(int(match.group(1)))
                         except ValueError:
                             print(f"    警告: レベル画像のaltから数値変換エラー: {img.get('alt','')}")
                # 重複を除去し、昇順にソート
                if levels_found:
                     levels_found = sorted(list(set(levels_found))) # 重複除去 & ソート

            # 結果を格納 (levels_foundが空ならそのまま[]が入る)
            pokemon_data['EvolutionLevels'] = levels_found

            # 結果ログの調整
            if not evolution_table:
                print(f"  進化レベル: 進化テーブルが見つかりませんでした -> {pokemon_data['EvolutionLevels']}")
            elif not levels_found:
                print(f"  進化レベル: レベル情報はテーブル内に見つかりませんでした -> {pokemon_data['EvolutionLevels']}")
            else:
                print(f"  進化レベル(リスト): {pokemon_data['EvolutionLevels']}") # リストとして表示

        except Exception as e:
            pokemon_data['EvolutionLevels'] = "取得エラー" # エラー時はエラーを示す文字列を格納
            print(f"進化レベル抽出中にエラーが発生しました: {e}")
            # print(traceback.format_exc()) # 詳細なエラー表示が必要な場合

        # --- ここまでが進化レベルの処理 ---

        # 3. 特性 (複数対応版)
        print(f"\n--- 特性抽出 開始 ---")
        pokemon_data['Abilities'] = [] # キー名を複数形にし、リストで初期化
        try:
            # 「特性」ヘッダーを持つテーブルを探す
            ability_header = soup.find('th', string=re.compile(r'^\s*特性\s*$'))
            ability_table = None
            if ability_header:
                 ability_table = ability_header.find_parent('table')
                 print("  「特性」テーブルを発見。")
            else:
                 print("  情報: 「特性」テーブルが見つかりませんでした。")
                 # 他の場所から特性を探す処理が必要な場合はここに追加

            if ability_table:
                tbody = ability_table.find('tbody') if ability_table.find('tbody') else ability_table
                if tbody:
                    rows = tbody.find_all('tr')
                    extracted_count = 0
                    for row_index, row in enumerate(rows):
                        # 最初の行がヘッダーならスキップ
                        if row_index == 0 and row.find('th'):
                            continue

                        cells = row.find_all('td', recursive=False)
                        # セルが3つある行を特性情報行とみなす (アイコン, 名前+Stage, 説明)
                        if len(cells) == 3:
                            name_cell = cells[1]
                            name_tag = name_cell.find('strong')
                            desc_cell = cells[2]

                            if name_tag and desc_cell: # 名前と説明セルがあれば処理
                                ability_name = clean_text(name_tag.get_text(strip=True))

                                # 進化段階を抽出 (例: "(ダクマ)")
                                stage_text = clean_text(name_cell.get_text(separator=' ', strip=True))
                                stage_match = re.search(r'\((.*?)\)', stage_text)
                                ability_stage = clean_text(stage_match.group(1)) if stage_match else None

                                # 説明を抽出
                                ability_desc = clean_text(desc_cell.get_text(separator=' ', strip=True))

                                # 辞書に情報をまとめる
                                ability_info = {'Name': ability_name, 'Description': ability_desc}
                                if ability_stage:
                                    ability_info['Stage'] = ability_stage # Stageがあれば追加

                                pokemon_data['Abilities'].append(ability_info)
                                extracted_count += 1
                                print(f"    -> 特性追加: {ability_name} ({ability_stage if ability_stage else '段階不明'})")
                            else:
                                print(f"    情報: 行 {row_index} は必要な要素(strong/descセル)が不足しています。")
                        # else:
                            # print(f"    情報: 行 {row_index} はセル数が3ではありません ({len(cells)}個)。スキップします。")

                    if extracted_count == 0:
                         print("  警告: 「特性」テーブル内に有効な特性データ行が見つかりませんでした。")

                else:
                    print("  警告: 「特性」テーブル内に tbody が見つかりません。")
            # else: テーブルが見つからなかった場合

            if not pokemon_data['Abilities']:
                 print("  特性情報が見つかりませんでした。")
                 # pokemon_data['Abilities'] = "取得失敗" # またはエラーを示す文字列

        except Exception as e:
            print(f"特性抽出中にエラーが発生しました: {e}")
            print(traceback.format_exc())
            pokemon_data['Abilities'] = "取得エラー" # エラー時はエラーを示す文字列を格納
        print(f"--- 特性抽出 完了 ({len(pokemon_data.get('Abilities',[]))}個) ---")

        # 3-B. 通常攻撃の説明 (複数項目・一般化対応版)
        print(f"\n--- 通常攻撃 説明 抽出 開始 ---")
        pokemon_data['BasicAttacks'] = [] # リストで初期化
        processed_flag = False # いずれかの方法で処理されたかを示すフラグ

        try:
            # --- 方法1: 専用テーブルを探す ---
            basic_attack_header_th = None
            potential_headers = soup.find_all('th')
            for th in potential_headers:
                th_text = th.get_text(strip=True)
                # ヘッダーのテキストとcolspan属性で判断
                if '通常攻撃' in th_text and th.get('colspan'):
                    # TODO: より確実に目的のテーブルヘッダーか判定するロジックが必要な場合あり
                    # 例: 親テーブルのクラス名やID、兄弟要素など
                    basic_attack_header_th = th
                    break

            basic_attack_table = None
            if basic_attack_header_th:
                 basic_attack_table = basic_attack_header_th.find_parent('table')

            if basic_attack_table:
                print("  「通常攻撃」専用テーブルを発見。構造を解析します...")
                tbody = basic_attack_table.find('tbody') if basic_attack_table.find('tbody') else basic_attack_table
                if tbody:
                    rows = tbody.find_all('tr')
                    if len(rows) > 1: # ヘッダー以外のデータ行があるか
                        # 最初のデータ行のセル数をチェックして構造を推測
                        first_data_row_cells = rows[1].find_all('td', recursive=False)

                        if len(rows) > 2 and len(rows[2].find_all('td', recursive=False)) == 2:
                            # ウーラオス型（状態別）と推定
                            print("    状態別テーブルとして処理します。")
                            for row_index, row in enumerate(rows):
                                if row_index == 0 and row.find('th'): continue # ヘッダー行スキップ
                                cells = row.find_all('td', recursive=False)
                                condition_raw = "不明"; description = "取得失敗"; condition_key = "Unknown"
                                if len(cells) == 3: # 最初のデータ行
                                    condition_raw = clean_text(cells[1].get_text(strip=True))
                                    description = clean_text(cells[2].get_text(separator=' ', strip=True))
                                elif len(cells) == 2: # 2行目以降
                                    condition_raw = clean_text(cells[0].get_text(separator=' ', strip=True))
                                    description = clean_text(cells[1].get_text(separator=' ', strip=True))
                                else: continue # 想定外はスキップ

                                # 状態キーの標準化 (より多くのパターンに対応できるように拡張が必要)
                                if "ダクマ" in condition_raw: condition_key = "Kubfu"
                                elif "いちげき" in condition_raw: condition_key = "Urshifu_Single"
                                elif "れんげき" in condition_raw: condition_key = "Urshifu_Rapid"
                                elif "ブレード" in condition_raw: condition_key = "Aegislash_Blade"
                                elif "シールド" in condition_raw: condition_key = "Aegislash_Shield"
                                else: condition_key = clean_text(re.sub(r'\(.*?\)', '', condition_raw).strip()) # カッコ除去

                                pokemon_data['BasicAttacks'].append({
                                    'Condition': condition_key if condition_key else 'Unknown',
                                    'ConditionRaw': condition_raw, 'Description': description
                                })
                                # print(f"      -> 状態別情報追加: Condition='{condition_key}'")
                            processed_flag = True

                        elif len(first_data_row_cells) >= 2:
                            # 単一説明型（アローラキュウコン型など）と推定
                            print("    単一説明型テーブルとして処理します。")
                            desc_cell = None
                            if len(first_data_row_cells) == 2 and first_data_row_cells[0].find('img'): desc_cell = first_data_row_cells[1]
                            elif len(first_data_row_cells) == 3 and first_data_row_cells[0].find('img'): desc_cell = first_data_row_cells[2]
                            # 他の単一説明パターンがあればここに追加

                            if desc_cell:
                                description = clean_text(desc_cell.get_text(separator=' ', strip=True))
                                # 強化攻撃の説明かどうかを判定するのは難しいので、一旦Defaultとする
                                pokemon_data['BasicAttacks'].append({
                                    'Condition': 'Default', 'ConditionRaw': 'Default', 'Description': description
                                })
                                # print(f"      -> 単一情報追加: Condition='Default'")
                                processed_flag = True
                            else: print("    警告: 単一説明型テーブルの構造が予期したものではありません。")
                        else: print("    警告: テーブル構造を判別できませんでした。")
                    else: print("    警告: 通常攻撃テーブルにデータ行が見つかりません。")
                else: print("  警告: 通常攻撃テーブル内に tbody が見つかりません。")
            # else: 専用テーブルが見つからなかった場合

            # --- 方法2: 「わざや特性の仕様と詳細」から検索 (方法1で取得できなかった場合) ---
            if not processed_flag:
                print("  専用テーブルで処理できなかった（または存在しない）ため、「わざや特性の仕様と詳細」を探します...")
                details_h_ba = None; details_table_ba = None
                h_tags = soup.find_all(re.compile(r'^h[2-4]$'))
                for h in h_tags:
                     if 'わざや特性の仕様と詳細' in h.get_text(strip=True): details_h_ba = h; break

                if details_h_ba:
                    # テーブル特定ロジック (アコーディオン考慮)
                    parent = details_h_ba.find_parent(); container = None
                    if parent:
                        if parent.has_attr('class') and 'accordion-container' in parent['class']: container = parent
                        else: container = parent.find('div', class_='accordion-container')
                        if not container: container = parent.find_next_sibling('div', class_='accordion-container')
                    if not container: container = details_h_ba.find_next_sibling('div', class_='accordion-container')
                    if container:
                        content = container.find('div', class_='accordion-content')
                        if content:
                             scroll = content.find('div', class_='h-scrollable')
                             target = scroll if scroll else content
                             if target: details_table_ba = target.find('table')
                    elif details_h_ba: details_table_ba = details_h_ba.find_next('table')

                    if details_table_ba:
                        print("    「仕様と詳細」テーブル発見。通常攻撃セクションを探します...")
                        rows = details_table_ba.find_all('tr')
                        in_section = False; description = None
                        # TODO: ここでも複数の説明（例: 強化攻撃）を取得するロジックが必要な場合あり
                        for row in rows:
                            th = row.find('th', colspan='3')
                            if th: in_section = ("通常攻撃" in th.get_text(strip=True)); continue
                            if in_section:
                                desc_cell = row.find('td', colspan='3') # 説明はcolspan=3にあると仮定
                                if not desc_cell:
                                     tds = row.find_all('td')
                                     if len(tds) == 1 and not tds[0].get('colspan') == '2': desc_cell = tds[0]
                                if desc_cell :
                                     temp_desc = clean_text(desc_cell.get_text(separator=' ', strip=True).replace("効果：","").strip())
                                     if temp_desc and len(temp_desc) > 10: # 計算式などと間違えないように長さで判定(仮)
                                         description = temp_desc
                                         break # 最初に見つかった説明を採用
                        if description:
                             pokemon_data['BasicAttacks'].append({
                                 'Condition': 'Default_FromDetails', # 取得元が分かるように
                                 'ConditionRaw': 'Default_FromDetails',
                                 'Description': description
                             })
                             print(f"      -> 詳細テーブルから情報追加: Desc='{description[:20]}...'")
                             processed_flag = True
                        else: print("    「仕様と詳細」内に通常攻撃の説明が見つかりませんでした。")
                    else: print("    「仕様と詳細」内のテーブルが見つかりませんでした。")
                else: print("    「仕様と詳細」の見出しが見つかりませんでした。")

            # --- どの方法でも見つからなかった場合の処理 ---
            if not processed_flag or not pokemon_data['BasicAttacks']:
                print("  警告: 通常攻撃の説明情報が見つかりませんでした。")
                pokemon_data['BasicAttacks'] = [{'Condition': 'Default', 'Description': '取得失敗'}]

        except Exception as e:
            print(f"通常攻撃 説明抽出中にエラーが発生しました: {e}")
            print(traceback.format_exc())
            pokemon_data['BasicAttacks'] = [{'Condition': 'Default','Description': "取得エラー"}]
        print(f"--- 通常攻撃 説明 抽出完了 ({len(pokemon_data.get('BasicAttacks',[]))}項目) ---")


        # --- ユナイト技の名前を事前に取得 ---
        unite_move_name = None
        try:
            # ユナイト技テーブルのヘッダーを探す
            unite_th = soup.find('th', string=re.compile(r'^\s*ユナイトわざ\s*\[ZL\]\s*$', re.IGNORECASE))
            if unite_th:
                unite_table = unite_th.find_parent('table')
                if unite_table:
                    tbody = unite_table.find('tbody') if unite_table.find('tbody') else unite_table
                    if tbody:
                        rows = tbody.find_all('tr', recursive=False)
                        for row in rows:
                            if row.find('th'): continue # ヘッダー行スキップ
                            cells = row.find_all('td', recursive=False)
                            if len(cells) >= 2: # アイコン、名前セルがあるか
                                name_tag = cells[1].find('strong') # 2番目のセルにstrongタグ
                                if name_tag:
                                    unite_move_name = clean_text(name_tag.get_text(strip=True))
                                    break # 見つけたら終了
            # if unite_move_name: print(f"  ユナイト技名 事前特定: {unite_move_name}")
            # else: print("  ユナイト技名 事前特定: 失敗/なし")
        except Exception as e: print(f"  ユナイト技名 事前特定中にエラー: {e}")
        print(f"  ユナイト技名 事前特定: {unite_move_name if unite_move_name else '失敗/なし'}")


        # 4-A. 技の基本情報抽出
        print("--- 技基本情報抽出 開始 ---")
        pokemon_data['Moves'] = []
        move_sections_patterns = {
            re.compile(r'^\s*わざ1\s*\[R\]\s*$', re.IGNORECASE): 'わざ1',
            re.compile(r'^\s*わざ2\s*\[ZR\]\s*$', re.IGNORECASE): 'わざ2',
            re.compile(r'^\s*ユナイトわざ\s*\[ZL\]\s*$', re.IGNORECASE): 'ユナイトわざ'
        }
        processed_move_names = set()
        try:
            all_tables = soup.find_all('table')
            target_tables_map = {}
            for table in all_tables:
                 first_th = table.find('th', {'colspan': '3'})
                 if first_th:
                     th_text = clean_text(first_th.get_text(strip=True))
                     for pattern, label in move_sections_patterns.items():
                         if pattern.match(th_text): target_tables_map[label] = table; break

            for label, table in target_tables_map.items():
                print(f"  処理中: {label} テーブル")
                tbody = table.find('tbody') if table.find('tbody') else table
                if not tbody: print(f"    警告: {label} テーブルに tbody が見つかりません。"); continue

                rows = tbody.find_all('tr', recursive=False)
                i = 0
                while i < len(rows):
                    row = rows[i]
                    # スキップ条件を強化
                    is_header = row.find('th')
                    is_level_divider = row.find('td', {'colspan': '3'}) and ('レベル' in row.get_text() or '選べます' in row.get_text())
                    is_empty_row = not row.find('td')
                    if is_header or is_level_divider or is_empty_row:
                        i += 1; continue

                    cells = row.find_all('td', recursive=False)
                    # 技情報行の基本的な構造かチェック (アイコンセル＋名前セル＋CDセル)
                    if len(cells) >= 3 and cells[0].find('img'):
                        move_name_tag = cells[1].find('strong')
                        if not move_name_tag: i += 1; continue # 名前にstrongがない場合は一旦スキップ

                        move_name = clean_text(move_name_tag.get_text(strip=True))
                        ability_name = pokemon_data.get('Ability', {}).get('Name')
                        # スキップ条件：特性名と同じ or 既に処理済み
                        if (ability_name and move_name == ability_name) or (move_name in processed_move_names):
                            i += 1; continue

                        # CD抽出
                        cd = "不明"
                        cd_img_tag = cells[2].find('img', alt='CD.png')
                        if cd_img_tag and cd_img_tag.next_sibling and isinstance(cd_img_tag.next_sibling, str):
                            cd_match = re.search(r'(\d+(?:\.\d+)?)', cd_img_tag.next_sibling.strip())
                            if cd_match: cd = cd_match.group(1)
                            else: cd = clean_text(cd_img_tag.next_sibling.strip()) # 数値以外の場合

                        # 説明とアップグレード説明の抽出
                        desc = "不明"; upgrade_desc = ""
                        desc_row_idx = i + 1
                        has_type = False
                        # タイプ行の判定 (より堅牢に)
                        if desc_row_idx < len(rows):
                            next_row_cells = rows[desc_row_idx].find_all('td', recursive=False)
                            if len(next_row_cells) == 1 and next_row_cells[0].find('img', alt=lambda x: x and 'CD.png' not in x and x.endswith('.png')):
                                # さらにスタイルなどで判定を強化することも可能
                                has_type = True; desc_row_idx += 1

                        # 説明行の特定と内容取得
                        if desc_row_idx < len(rows):
                            desc_row = rows[desc_row_idx]
                            desc_cells = desc_row.find_all('td', recursive=False)
                            # 説明セルは colspan=3 が多い
                            if len(desc_cells) == 1 and desc_cells[0].get('colspan') == '3':
                                full_desc = clean_text(desc_cells[0].get_text(separator=' ', strip=True))
                                is_unite = (unite_move_name and move_name == unite_move_name)

                                # 説明文の分割ロジック (アローラキュウコンの例に基づく)
                                if is_unite: # ユナイト技
                                    if "ユナイトバフ：" in full_desc:
                                        parts = full_desc.split("ユナイトバフ：", 1)
                                        desc = clean_text(re.sub(r'^レベル\s*\d+\s*[:：]\s*', '', parts[0]).strip())
                                        upgrade_desc = clean_text("ユナイトバフ：" + parts[1])
                                    else: desc = clean_text(re.sub(r'^レベル\s*\d+\s*[:：]\s*', '', full_desc).strip())
                                else: # 通常技
                                    upg_match = re.search(r"(レベル\s*\d+\s*[:：]|アップグレード後\s*[:：])", full_desc)
                                    if upg_match:
                                        desc = clean_text(full_desc[:upg_match.start()])
                                        upgrade_desc = clean_text(re.sub(r'^(レベル\s*\d+|アップグレード後)\s*[:：]\s*', '', full_desc[upg_match.start():]).strip())
                                    else: desc = full_desc # アップグレード説明なし

                                # 基本説明が空なら移動
                                if (not desc or desc=="不明") and upgrade_desc:
                                     desc = upgrade_desc; upgrade_desc = ""
                            # else: 説明セルが見つからない場合

                        # 辞書に格納
                        move_dict = {'Name': move_name, 'Cooldown': cd, 'Description': desc}
                        if upgrade_desc: move_dict['UpgradeDescription'] = upgrade_desc
                        pokemon_data['Moves'].append(move_dict)
                        processed_move_names.add(move_name)
                        print(f"    -> 技追加: {move_name}")
                        i = desc_row_idx + 1 # 次の処理対象行へ (説明行の次)
                    else:
                        # 技情報行の構造でない場合
                        i += 1
                # --- whileループ終了 ---
            # --- テーブルループ終了 ---
            print(f"--- 技基本情報抽出 完了 ({len(pokemon_data['Moves'])}個) ---")
        except Exception as e: print(f"技基本情報抽出中にエラー: {e}\n{traceback.format_exc()}")


        # 4-B. ダメージ計算式抽出 (データ駆動型アプローチ)
        print("--- ダメージ計算式抽出 開始 ---")
        try:
            details_h = None
            for tag_name in ['h3', 'h4', 'h2']:
                headers = soup.find_all(tag_name)
                for h in headers:
                    if 'わざや特性の仕様と詳細' in h.get_text(strip=True):
                        details_h = h; break
                if details_h: break

            details_table = None
            if details_h:
                print(f"  見出し '{details_h.get_text(strip=True)}' を発見。テーブルを特定します。")
                parent = details_h.find_parent()
                container = None
                if parent:
                    if parent.has_attr('class') and 'accordion-container' in parent['class']: container = parent
                    else: container = parent.find('div', class_='accordion-container')
                    if not container: container = parent.find_next_sibling('div', class_='accordion-container')
                if not container: container = details_h.find_next_sibling('div', class_='accordion-container')
                if container:
                    content = container.find('div', class_='accordion-content')
                    if content:
                         scroll = content.find('div', class_='h-scrollable')
                         target = scroll if scroll else content
                         if target: details_table = target.find('table')
                elif details_h: details_table = details_h.find_next('table')

                if details_table:
                    print("  計算式テーブル発見。処理開始...")
                    rows = details_table.find_all('tr')
                    current_item_name = None; current_item_type = None; current_target_data = None
                    extracted_ability_name = pokemon_data.get('Ability', {}).get('Name')
                    processed_count = 0

                    for row_index, row in enumerate(rows):
                        th = row.find('th', colspan='3')
                        if th: # ヘッダー行
                            header_text = clean_text(th.get_text(strip=True))
                            current_item_name = None; current_item_type = None; current_target_data = None
                            if "通常攻撃" in header_text:
                                current_item_name="BasicAttack"; current_item_type='basic_attack'
                                if 'BasicAttack' not in pokemon_data: pokemon_data['BasicAttack'] = {}
                                current_target_data = pokemon_data['BasicAttack']
                            elif extracted_ability_name and extracted_ability_name in header_text:
                                current_item_name="Ability"; current_item_type='ability'
                                if 'Ability' not in pokemon_data: pokemon_data['Ability'] = {}
                                current_target_data = pokemon_data['Ability']
                            continue

                        name_tag = row.find('strong')
                        cells = row.find_all('td', recursive=False)
                        is_name_row = (len(cells) >= 2 and cells[0].find('img') and cells[1].find('strong') and not row.find('td', colspan='2'))
                        if is_name_row: # 名前行
                            name = clean_text(name_tag.get_text(strip=True))
                            if extracted_ability_name and name == extracted_ability_name:
                                current_item_name="Ability"; current_item_type='ability'
                                if 'Ability' not in pokemon_data: pokemon_data['Ability'] = {}
                                current_target_data = pokemon_data['Ability']
                            elif current_item_type != 'basic_attack':
                                current_item_name=name; current_item_type='move'
                                current_target_data = next((m for m in pokemon_data.get('Moves', []) if m.get('Name') == name), None)
                                if not current_target_data:
                                     print(f"    警告: 技名 '{name}' がリストにないため計算式を紐付けられません。")
                                     current_item_name=None; current_item_type=None
                            continue

                        # 計算式セル処理
                        if current_item_name and current_target_data:
                            formula_cell = row.find('td', colspan='2')
                            if formula_cell:
                                # --- 行分割 & HTMLタグ除去 ---
                                current_line_parts = []
                                processed_lines_for_pattern_matching = []

                                for content_node in formula_cell.contents: # tdタグの直下の子ノードをイテレート
                                    if isinstance(content_node, Tag): # タグの場合 (例: <span ...>, <br ...>)
                                        if content_node.name == 'br': # <br> タグなら、それまでのパーツを1行として処理
                                            if current_line_parts:
                                                processed_lines_for_pattern_matching.append(" ".join(current_line_parts).strip())
                                                current_line_parts = []
                                        elif content_node.name == 'span': # <span> タグなら、そのテキスト内容を追加
                                            current_line_parts.append(clean_text(content_node.get_text(strip=True)))
                                        # 他のタグも必要に応じて処理 (例: divタグなど特別なものがあれば)
                                    else: # テキストノードの場合
                                        text_part = clean_text(str(content_node).strip())
                                        if text_part: # 空でなければ追加
                                            current_line_parts.append(text_part)

                                # ループ終了後、残っているパーツがあれば最後の行として処理
                                if current_line_parts:
                                  processed_lines_for_pattern_matching.append(" ".join(current_line_parts).strip())

                                is_after_upgrade = False
                                for line in processed_lines_for_pattern_matching:
                                    # print(f"  DEBUG line: {line}") # 必要なら行内容デバッグ解除
                                    if line.strip().lower() == 'アップグレード後':
                                        is_after_upgrade = True; continue

                                    found_match_in_line = False
                                    for p_info in formula_patterns:
                                        if current_item_type not in p_info['types'] and 'common' not in p_info['types']: continue

                                        match = re.match(p_info['pattern'], line)
                                        if match:
                                            # マッチしたグループ(計算式部分)を取得
                                            # ★★★ HTMLタグ除去は clean_text で行われる前提 ★★★
                                            value_str = clean_text(match.group(1).strip())

                                            key = None; base_key = None
                                            if current_item_type == 'ability': base_key = p_info.get('key_ability', p_info.get('key_base'))
                                            elif current_item_type == 'basic_attack': base_key = p_info.get('key_base')
                                            elif current_item_type == 'move': base_key = p_info.get('key_base')

                                            if base_key:
                                                if is_after_upgrade:
                                                    key = p_info.get('key_upgrade')
                                                    if not key and 'Formula_' in base_key: key = base_key + '_Upgraded'
                                                    elif not key: key = base_key
                                                else: key = base_key

                                            if key and value_str:
                                                # print(f"    -> 格納: {current_item_name} [{key}] = '{value_str}'") # デバッグ用
                                                current_target_data[key] = value_str
                                                processed_count += 1
                                                found_match_in_line = True
                                                break # マッチしたらこの行は処理完了

                                    # if not found_match_in_line and line: print(f"    情報: 計算式でない行?: '{line}' (対象: {current_item_name})") # 必要なら表示

                    # --- row ループ終了 ---
                    print(f"--- 計算式抽出 完了 ({processed_count}個) ---")
                else: print("警告: 計算式テーブルが見つかりませんでした。")
            else: print("警告: 「わざや特性の仕様と詳細」見出しが見つかりませんでした。")
        except Exception as e: print(f"計算式抽出中にエラー: {e}\n{traceback.format_exc()}")



        # 5. レベル別ステータス抽出
        print("\n--- レベル別ステータス抽出 開始 ---")
        pokemon_data['LevelStats'] = []
        try:
            stats_header = None
            h_tags = soup.find_all(re.compile(r'^h[34]$'))
            for h in h_tags:
                if 'レベル別ステータス表' in h.get_text(strip=True): stats_header = h; break

            stats_table = None
            if stats_header:
                # テーブル特定ロジック (アコーディオン考慮) - 計算式テーブルと同様
                parent = stats_header.find_parent()
                container = None
                if parent:
                    if parent.has_attr('class') and 'accordion-container' in parent['class']: container = parent
                    else: container = parent.find('div', class_='accordion-container')
                    if not container: container = parent.find_next_sibling('div', class_='accordion-container')
                if not container: container = stats_header.find_next_sibling('div', class_='accordion-container')
                if container:
                    content = container.find('div', class_='accordion-content')
                    if content:
                         scroll = content.find('div', class_='h-scrollable')
                         target = scroll if scroll else content
                         if target: stats_table = target.find('table')
                elif stats_header: stats_table = stats_header.find_next('table')

            if not stats_table: # フォールバック
                all_tables = soup.find_all('table')
                for table in all_tables:
                    thead = table.find('thead')
                    if thead and 'レベル' in thead.get_text() and 'HP' in thead.get_text():
                         stats_table = table; break

            if stats_table:
                print("  レベル別ステータステーブル発見。データ抽出を開始...")
                headers = []; header_map = {}
                thead = stats_table.find('thead')
                if thead:
                    header_cells = thead.find_all('td')
                    valid_col_index = 0
                    for original_index, cell in enumerate(header_cells):
                        style = cell.get('style', '')
                        if 'width:5px' in style.replace(' ',''): continue
                        header_text = clean_text(cell.get_text(separator=' ', strip=True))
                        key = header_text
                        # キー名変換
                        if header_text == "レベル": key = "Level"
                        elif header_text == "HP": key = "HP"
                        elif header_text == "攻撃": key = "Attack"
                        elif header_text == "防御": key = "Defense"
                        elif header_text == "特攻": key = "SpAttack"
                        elif header_text == "特防": key = "SpDefense"
                        elif header_text == "移動速度": key = "MoveSpeed"
                        elif "通常攻撃" in header_text and "速度" in header_text: key = "AttackSpeed"
                        elif "急所率" in header_text: key = "CritRate"
                        elif "ライフ" in header_text and "スティール" in header_text: key = "Lifesteal"
                        elif header_text == "CDR": key = "CDR"
                        elif "被妨害" in header_text or "時間短縮" in header_text: key = "Tenacity"
                        headers.append(key)
                        header_map[original_index] = key
                        valid_col_index += 1
                    print(f"  検出ヘッダー: {headers}")
                else: print("警告: theadが見つかりません。"); raise ValueError("thead not found")

                tbody = stats_table.find('tbody')
                if tbody:
                    data_rows = tbody.find_all('tr')
                    extracted_count = 0
                    for row in data_rows:
                        cells = row.find_all('td')
                        level_data = {}
                        valid_row = True
                        for original_index, key in header_map.items():
                            if original_index < len(cells):
                                cell_text = cells[original_index].get_text(strip=True)
                                try:
                                    value = None
                                    if '%' in cell_text: value = float(cell_text.replace('%', ''))
                                    elif cell_text.isdigit(): value = int(cell_text)
                                    elif re.match(r'^-?\d+(?:\.\d+)?$', cell_text): value = float(cell_text)
                                    else: value = cell_text # 数値以外は文字列
                                    level_data[key] = value
                                except ValueError: level_data[key] = None # エラー時はNone
                            else: level_data[key] = None; valid_row = False

                        if valid_row and 'Level' in level_data and level_data['Level'] is not None:
                            pokemon_data['LevelStats'].append(level_data)
                            extracted_count += 1
                    print(f"  抽出完了 ({extracted_count} レベル分)")
                else: print("警告: tbodyが見つかりません。"); pokemon_data['LevelStats'] = "取得失敗(tbodyなし)"
            else: print("警告: レベル別ステータステーブルが見つかりませんでした。"); pokemon_data['LevelStats'] = "取得失敗(テーブルなし)"
        except Exception as e:
            print(f"レベル別ステータス抽出中にエラー: {e}")
            print(traceback.format_exc())
            pokemon_data['LevelStats'] = "取得エラー"
        print(f"--- レベル別ステータス抽出 完了 ({len(pokemon_data.get('LevelStats',[]))}レベル分) ---")


        end_time = time.time()
        print(f"--- データ抽出完了 ({end_time - start_time:.2f}秒) ---")
        return pokemon_data

    except Exception as e:
        print(f"！！！全体的なエラー発生 ({url})！！！: {e}")
        print(traceback.format_exc())
        return None # エラー時はNoneを返す

    finally:
        pass


# --- メイン処理 ---
if __name__ == "__main__":
    target_urls = []
    
    # pokemon_urls.json から読み込み
    if os.path.exists(url_list_file):
        try:
            with open(url_list_file, 'r', encoding='utf-8') as f:
                target_urls = json.load(f)
            print(f"ファイルから {len(target_urls)} 件のURLを読み込みました。")
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            target_urls = []
    else:
        print(f"ファイルが見つかりません: {url_list_file}")

    if not target_urls:
        print("処理対象のURLがありません。pokemon_urls.json を確認してください。")
    else:
        print("\n--- ブラウザ起動中 ---")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless') # 画面を表示しない
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.binary_location = "/usr/bin/chromium"

        try:
            service = ChromeService() 
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(5)
            all_data = []
            print(f"\n--- 処理開始: 対象 {len(target_urls)} 件 ---")

            for i, url in enumerate(target_urls):
                print(f"\n[{i+1}/{len(target_urls)}] 処理中...")
                
                data = scrape_pokemon_data(driver, url)
                
                if data:
                    all_data.append(data)
                    # ... (保存処理はそのまま) ...
                    try:
                        p_name = data.get('Name', url.split('/')[-1])
                        safe_name = re.sub(r'[\\/*?:"<>|]', '', p_name)
                        fname = os.path.join(output_dir, f"{safe_name}_data.json")
                        with open(fname, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                    except: pass
                else:
                    print(f"スキップ: {url}")

        except Exception as e:
            print(f"予期せぬエラー: {e}")
        
        finally:
            print("ブラウザを閉じます。")
            if 'driver' in locals():
                driver.quit()
            
        print("完了")