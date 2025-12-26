import datetime
import zoneinfo
import os
import sys
import pandas as pd
import psycopg2
import requests
import lxml.html
from dotenv import load_dotenv
from monthdelta import monthmod

# 同じフォルダにある pokemon_home.py をインポート
# (パスエラーを防ぐため、このファイルの場所をシステムパスに追加)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
import pokemon_home

def main():
    # 1. 時間取得
    now = datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Tokyo'))
    d = now.strftime('%y/%m/%d %H:%M:%S')
    print(d)
    print("Pokemon HOMEの情報の更新を開始します...")

    # 2. 環境変数の読み込み (.envは一つ上の階層にあるためパスを指定)
    dotenv_path = os.path.join(current_dir, '../.env')
    load_dotenv(dotenv_path)
    
    db_url = os.environ.get("DSN")
    if not db_url:
        print("エラー: .envファイルが見つからないか、DSNが設定されていません。")
        return

    # 3. シーズン計算
    dt1 = datetime.datetime(2022, 12, 1, 9, 0, 0, 0)
    dt2 = datetime.datetime.now()
    mmod = monthmod(dt1, dt2)
    season_num = mmod[0].months + 1  # シーズン番号
    
    rules = ["single", "double"]
    
    # 4. パス設定
    output_dir = os.path.join(current_dir, "../output")
    asset_dir = os.path.join(current_dir, "../asset/")

    # 出力フォルダがなければ作成
    os.makedirs(output_dir, exist_ok=True)

    for rule in rules:
        print(f"--- Processing Season {season_num} : Rule {rule} ---")
        
        # pokemon_homeクラスの初期化
        # assetフォルダのパスを渡す
        home = pokemon_home.pokemon_home(asset_dir)
        
        rule_id = 0 if rule == "single" else 1
        
        # データ取得
        try:
            home.request_parameters_from_season_info(season_num, rule_id)
            pokemon_ranking = home.output_pokemon_ranking()
            move, ability, nature, item, pokemon, terastype = home.output_pokemon_detail()
        except Exception as e:
            print(f"データ取得中にエラーが発生しました: {e}")
            continue

        # DataFrame作成
        df_pokemon_ranking = pd.DataFrame(pokemon_ranking, columns=['id', 'form_id', 'pokemon'])
        df_move = pd.DataFrame(move, columns=["pokemon", "id", "form", "rank", "move", "raito"])
        df_nature = pd.DataFrame(nature, columns=["pokemon", "id", "form", "rank", "nature", "raito"])
        df_ability = pd.DataFrame(ability, columns=["pokemon", "id", "form", "rank", "ability", "raito"])
        df_pokemon = pd.DataFrame(pokemon, columns=["pokemon", "id", "form", "rank", "pokeid"])
        df_item = pd.DataFrame(item, columns=["pokemon", "id", "form", "rank", "item", "raito"])
        df_teratype = pd.DataFrame(terastype, columns=["pokemon", "id", "form", "rank", "terastype", "raito"])

        # CSV保存
        print(f"CSVを保存中: {output_dir}")
        df_pokemon_ranking.to_csv(os.path.join(output_dir, f"pokemon_ranking_{rule}.csv"), encoding="shift-jis", index=False)
        df_move.to_csv(os.path.join(output_dir, f"move_{rule}.csv"), encoding="shift-jis", index=False)
        df_ability.to_csv(os.path.join(output_dir, f"ability_{rule}.csv"), encoding="shift-jis", index=False)
        df_item.to_csv(os.path.join(output_dir, f"item_{rule}.csv"), encoding="shift-jis", index=False)
        df_teratype.to_csv(os.path.join(output_dir, f"terastype_{rule}.csv"), encoding="shift-jis", index=False)

        # ID/Form データの作成と保存
        data = pd.read_csv(os.path.join(output_dir, f"move_{rule}.csv"), encoding="shift-jis")
        df_id_form = data[["id", "form", "pokemon"]].drop_duplicates().copy()
        df_id_form.to_csv(os.path.join(output_dir, f"id_form_{rule}.csv"), encoding="cp932", index=False)

        # --- データ加工処理 ---
        mkid = lambda x: x/10 if x < 10 else x/100
        mkkey = lambda df: df["id"].astype(str).str.cat(df["rank"].astype(str), sep='.')

        # idとform&nameの関連付け
        home_id_form = pd.DataFrame(columns=["id", "form", "name"])
        home_id_form["form"] = df_id_form["form"] + 1
        home_id_form["id"] = df_id_form["id"] + home_id_form["form"].apply(mkid)
        home_id_form["name"] = df_id_form["pokemon"]

        # 共通の加工関数
        def process_df(df_target, rename_map, columns_to_keep):
            df_cp = df_target.copy()
            df_cp = df_cp.rename(columns=rename_map)
            df_cp["form"] = df_cp["form"].apply(lambda x: int(x) + 1)
            # マージ
            df_merged = pd.merge(df_cp, home_id_form, on=["name", "form"])
            # キー生成（ranking以外）
            if "rank" in df_merged.columns and "pokeid" not in df_merged.columns and "id_y" not in df_merged.columns: 
                 # ランキング用にはkeyがないので分岐するか、ここでは簡易的に処理
                 pass
            
            # rankingは構造が違うため個別処理推奨ですが、元のロジックを簡略化して書きます
            return df_merged

        # ランキングの加工
        home_pokemon_ranking = df_pokemon_ranking.copy()
        home_pokemon_ranking = home_pokemon_ranking.rename(columns={"id": "rank", "form_id": "form", "pokemon": "name"})
        home_pokemon_ranking["form"] += 1
        home_pokemon_ranking = pd.merge(home_pokemon_ranking, home_id_form, on=["form", "name"])
        home_pokemon_ranking = home_pokemon_ranking[["id", "rank"]]

        # その他のテーブル加工
        def make_table_data(original_df, rename_dict, output_cols):
            df_cp = original_df.copy()
            df_cp = df_cp.rename(columns=rename_dict)
            df_cp["form"] = df_cp["form"].apply(lambda x: int(x) + 1)
            df_cp = pd.merge(df_cp, home_id_form, on=["name", "form"])
            df_cp["key"] = mkkey(df_cp)
            return df_cp[output_cols]

        home_move = make_table_data(df_move, {"pokemon": "name", "id": "no"}, ["key", "id", "rank", "move", "raito"])
        home_ability = make_table_data(df_ability, {"pokemon": "name", "id": "no"}, ["key", "id", "rank", "ability", "raito"])
        home_nature = make_table_data(df_nature, {"pokemon": "name", "id": "no"}, ["key", "id", "rank", "nature", "raito"])
        home_item = make_table_data(df_item, {"pokemon": "name", "id": "no"}, ["key", "id", "rank", "item", "raito"])
        home_terastype = make_table_data(df_teratype, {"pokemon": "name", "id": "no", "tarastype": "terastype"}, ["key", "id", "rank", "terastype", "raito"])
        
        # ポケモン（パーティ）はカラム名が少し違う
        home_pokemon = df_pokemon.copy()
        home_pokemon = home_pokemon.rename(columns={"pokemon": "name", "id": "no"})
        home_pokemon["form"] = home_pokemon["form"].apply(lambda x: int(x) + 1)
        home_pokemon = pd.merge(home_pokemon, home_id_form, on=["name", "form"])
        home_pokemon["key"] = mkkey(home_pokemon)
        home_pokemon = home_pokemon[["key", "id", "rank", "pokeid"]]

        # --- DB更新 ---
        print("DBへの保存を開始します...")
        
        tbdict = {
            "pokemon_ranking": home_pokemon_ranking.to_numpy().tolist(),
            "move": home_move.to_numpy().tolist(),
            "ability": home_ability.to_numpy().tolist(),
            "nature": home_nature.to_numpy().tolist(),
            "item": home_item.to_numpy().tolist(),
            "pokemon": home_pokemon.to_numpy().tolist(),
            "terastype": home_terastype.to_numpy().tolist()
        }
        
        tbnames = ["pokemon_ranking", "move", "ability", "nature", "item", "pokemon", "terastype"]
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                for tbname in tbnames:
                    vals = tbdict[tbname]
                    if not vals:
                        continue
                        
                    if tbname == "pokemon_ranking":
                        sql = f"insert into home_pokerank_{rule} values (%s,%s) on conflict(id) do update set rank=excluded.rank"
                    elif tbname == "pokemon":
                        sql = f"insert into home_party_{rule} values (%s,%s,%s,%s) on conflict(key) do update set id=excluded.id, rank=excluded.rank, pokeid=excluded.pokeid"
                    else:
                        sql = f"insert into home_{tbname}_{rule} values (%s,%s,%s,%s,%s) on conflict(key) do update set id=excluded.id, rank=excluded.rank, {tbname}=excluded.{tbname}, raito=excluded.raito"
                    
                    cur.executemany(sql, vals)
            conn.commit()
        print(f"{rule} ルールのDB更新完了")

    print("全ての更新が完了しました!")

if __name__ == '__main__':
    main()