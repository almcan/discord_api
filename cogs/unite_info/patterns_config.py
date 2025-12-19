# -*- coding: utf-8 -*-

# 処理順序が重要（より具体的なパターンを先に記述）
# label: 識別のためのラベル
# pattern: re.match用正規表現
# types: 適用対象タイプリスト
# key_base: 基本キー
# key_upgrade(Option): UGキー

formula_patterns = [
    # --- Basic Attack Specific ---
    {'label': '通常攻撃(通常)',   'pattern': r"ダメージ・通常\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal'},
    {'label': '通常攻撃(強化)',   'pattern': r"ダメージ・強化\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted'},
    {'label': '強化攻撃追加ダメージ', 'pattern': r"強化攻撃の追加ダメージ\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Additional'},
    {'label': '通常攻撃追加ダメージ', 'pattern': r"通常攻撃追加ダメージ\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal_Additional'},
    {'label': '追加ダメージ(KO後通常)', 'pattern': r"追加ダメージ・KO後通常\s*[:：]\s*(.*)", 'types': ['basic_attack', 'move'], 'key_base': 'DamageFormula_Additional_AfterKO', 'key_upgrade': 'DamageFormula_Additional_AfterKO_Upgraded'},
    {'label': 'ダメージ・通常(共通)', 'pattern': r"ダメージ・通常\(共通\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal_Common'},
    {'label': 'ダメージ・通常(近)', 'pattern': r"ダメージ・通常\(近\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal_Melee'},
    {'label': 'ダメージ・通常(遠)', 'pattern': r"ダメージ・通常\(遠\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal_Ranged'},
    {'label': 'ダメージ・通常(メガ)', 'pattern': r"ダメージ・通常（メガ）\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Normal_Mega'}, # 全角括弧
    {'label': 'ダメージ・強化(イーブイ)', 'pattern': r"ダメージ・強化\(イーブイ\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Eevee'},
    {'label': 'ダメージ・強化(グレイシア)', 'pattern': r"ダメージ・強化\(グレイシア\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Glaceon'},
    {'label': 'ダメージ・強化(ダクマ)', 'pattern': r"ダメージ・強化\(ダクマ\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Kubfu'},
    {'label': 'ダメージ・強化(一撃)', 'pattern': r"ダメージ・強化\(一撃\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_UrshifuSingle'},
    {'label': 'ダメージ・強化(連撃)', 'pattern': r"ダメージ・強化\(連撃\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_UrshifuRapid'},
    {'label': 'ダメージ・強化(ブレード)', 'pattern': r"ダメージ・強化\(ブレード\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Blade'},
    {'label': 'ダメージ・強化(シールド)', 'pattern': r"ダメージ・強化\(シールド\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Shield'},
    {'label': 'ダメージ・強化(共通)', 'pattern': r"ダメージ・強化\(共通\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Common'},
    {'label': 'ダメージ・強化(近)', 'pattern': r"ダメージ・強化\(近\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Melee'},
    {'label': 'ダメージ・強化(遠)', 'pattern': r"ダメージ・強化\(遠\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Ranged'},
    {'label': 'ダメージ・強化（メガ）', 'pattern': r"ダメージ・強化（メガ）\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Mega'}, # 全角括弧
    {'label': 'ダメージ・ダッシュ強化', 'pattern': r"ダメージ・ダッシュ強化\s*[:：]\s*(.*)", 'types': ['move', 'basic_attack'], 'key_base': 'DamageFormula_Dash_Boosted', 'key_upgrade': 'DamageFormula_Dash_Boosted_Upgraded'},
    {'label': 'ダメージ・強化攻撃', 'pattern': r"ダメージ・強化攻撃\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_BoostedAttackLabel'}, # 特殊ラベル
    {'label': '通常攻撃ダメージ(通常)', 'pattern': r"通常攻撃ダメージ・通常\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_NormalAttack_Normal'},


    # --- Multi-Hit / Staged Damage ---
    {'label': 'ダメージ(一段目)', 'pattern': r"ダメージ・一段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage1', 'key_upgrade': 'DamageFormula_Stage1_Upgraded'},
    {'label': 'ダメージ(二段目)', 'pattern': r"ダメージ・二段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2', 'key_upgrade': 'DamageFormula_Stage2_Upgraded'},
    {'label': 'ダメージ(2段目(内側))', 'pattern': r"ダメージ・2段目\(内側\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Inner', 'key_upgrade': 'DamageFormula_Stage2_Inner_Upgraded'},
    {'label': 'ダメージ(2段目(中間))', 'pattern': r"ダメージ・2段目\(中間\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Mid', 'key_upgrade': 'DamageFormula_Stage2_Mid_Upgraded'},
    {'label': 'ダメージ(2段目(外側))', 'pattern': r"ダメージ・2段目\(外側\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Outer', 'key_upgrade': 'DamageFormula_Stage2_Outer_Upgraded'},
    {'label': 'ダメージ(2段目(ねむり))', 'pattern': r"ダメージ・2段目（ねむり）\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Sleep', 'key_upgrade': 'DamageFormula_Stage2_Sleep_Upgraded'}, # 全角括弧対応
    {'label': 'ダメージ(2段目溜め)', 'pattern': r"ダメージ・2段目溜め\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Charged', 'key_upgrade': 'DamageFormula_Stage2_Charged_Upgraded'},
    {'label': 'ダメージ(2撃目)', 'pattern': r"ダメージ・2撃目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SecondStrike', 'key_upgrade': 'DamageFormula_SecondStrike_Upgraded'},
    {'label': 'ダメージ(3段目)', 'pattern': r"ダメージ・3段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage3', 'key_upgrade': 'DamageFormula_Stage3_Upgraded'},
    {'label': 'ダメージ(4段目)', 'pattern': r"ダメージ・4段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage4', 'key_upgrade': 'DamageFormula_Stage4_Upgraded'},
    {'label': 'ダメージ(5段目)', 'pattern': r"ダメージ・5段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage5', 'key_upgrade': 'DamageFormula_Stage5_Upgraded'},
    {'label': 'ダメージ(最終段)', 'pattern': r"ダメージ・最終段\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_FinalHit', 'key_upgrade': 'DamageFormula_FinalHit_Upgraded'},
    {'label': 'ダメージ(5-10Hit)', 'pattern': r"ダメージ・5～10Hit目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_MultiHit_5_10', 'key_upgrade': 'DamageFormula_MultiHit_5_10_Upgraded'},
    {'label': 'ダメージ(3-4Hit)',  'pattern': r"ダメージ・3～4Hit目\s*[:：]\s*(.*)",  'types': ['move'], 'key_base': 'DamageFormula_MultiHit_3_4', 'key_upgrade': 'DamageFormula_MultiHit_3_4_Upgraded'},
    {'label': 'ダメージ(1-2Hit)',  'pattern': r"ダメージ・1～2Hit目\s*[:：]\s*(.*)",  'types': ['move'], 'key_base': 'DamageFormula_MultiHit_1_2', 'key_upgrade': 'DamageFormula_MultiHit_1_2_Upgraded'},
    {'label': 'ダメージ(1-3段目)', 'pattern': r"ダメージ・1～3段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage1_3', 'key_upgrade': 'DamageFormula_Stage1_3_Upgraded'},
    {'label': 'ダメージ(2,3段目)', 'pattern': r"ダメージ・2,3段目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_3', 'key_upgrade': 'DamageFormula_Stage2_3_Upgraded'},
    {'label': 'ダメージ(1-6Hit)', 'pattern': r"ダメージ・1～6Hit目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_MultiHit_1_6', 'key_upgrade': 'DamageFormula_MultiHit_1_6_Upgraded'},
    {'label': 'ダメージ(7Hit)',   'pattern': r"ダメージ・7Hit目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_MultiHit_7', 'key_upgrade': 'DamageFormula_MultiHit_7_Upgraded'},
    {'label': 'ダメージ(1発目)', 'pattern': r"ダメージ・1発目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Hit1', 'key_upgrade': 'DamageFormula_Hit1_Upgraded'},
    {'label': 'ダメージ(2発目以後)', 'pattern': r"ダメージ・2発目以後\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Hit2Onward', 'key_upgrade': 'DamageFormula_Hit2Onward_Upgraded'},
    {'label': 'ダメージ(2段目以降)', 'pattern': r"ダメージ・2段目以降\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2Onward', 'key_upgrade': 'DamageFormula_Stage2Onward_Upgraded'},
    {'label': 'ダメージ(1Hit)', 'pattern': r"ダメージ\(1Hit\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_PerHit', 'key_upgrade': 'DamageFormula_PerHit_Upgraded'},
    {'label': 'ダメージ(ラッシュ)', 'pattern': r"ダメージ・ラッシュ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Rush', 'key_upgrade': 'DamageFormula_Rush_Upgraded'},
    {'label': 'ダメージ(ラッシュ〆)', 'pattern': r"ダメージ・ラッシュ〆\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Rush_Finisher', 'key_upgrade': 'DamageFormula_Rush_Finisher_Upgraded'},

    # --- Specific Damage Types / Conditions ---
    {'label': 'ダメージ(着弾)',   'pattern': r"ダメージ・着弾\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Landing', 'key_upgrade': 'DamageFormula_Landing_Upgraded'},
    {'label': 'ダメージ(着地_Alt)', 'pattern': r"ダメージ・着地\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Landing_Alt', 'key_upgrade': 'DamageFormula_Landing_Alt_Upgraded'},
    {'label': 'ダメージ(こおり)', 'pattern': r"ダメージ・こおり状態\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Frozen'},
    {'label': '凍結ダメージ', 'pattern': r"凍結ダメージ\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DamageFormula_Freeze', 'key_upgrade': 'DamageFormula_Freeze_Upgraded'}, # Frozenと統合可能か？
    {'label': '追加ダメージ(こおり状態)', 'pattern': r"追加ダメージ\(こおり状態\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_Frozen', 'key_upgrade': 'DamageFormula_Additional_Frozen_Upgraded'},
    {'label': 'ダメージ(近)',   'pattern': r"ダメージ・近\s*[:：]\s*(.*)",   'types': ['move'], 'key_base': 'DamageFormula_Near', 'key_upgrade': 'DamageFormula_Near_Upgraded'},
    {'label': 'ダメージ(中)',   'pattern': r"ダメージ・中\s*[:：]\s*(.*)",   'types': ['move'], 'key_base': 'DamageFormula_Mid', 'key_upgrade': 'DamageFormula_Mid_Upgraded'},
    {'label': 'ダメージ(遠)',   'pattern': r"ダメージ・遠\s*[:：]\s*(.*)",   'types': ['move'], 'key_base': 'DamageFormula_Far', 'key_upgrade': 'DamageFormula_Far_Upgraded'},
    {'label': '追加ダメージ',       'pattern': r"追加ダメージ\s*[:：]\s*(.*)",       'types': ['move', 'ability'], 'key_base': 'DamageFormula_Additional', 'key_upgrade': 'DamageFormula_Additional_Upgraded'},
    {'label': '追加ダメージ(1Hit)', 'pattern': r"追加ダメージ\(1Hit\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_PerHit', 'key_upgrade': 'DamageFormula_Additional_PerHit_Upgraded'},
    {'label': '追加ダメージ(動けない相手)', 'pattern': r"追加ダメージ\(動けない相手\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_Hindered', 'key_upgrade': 'DamageFormula_Additional_Hindered_Upgraded'},
    {'label': '追加ダメージ・強化(近接)', 'pattern': r"追加ダメージ・強化\(近接\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Boosted_Melee_Additional'},
    {'label': '追加ダメージ(追加4回目)', 'pattern': r"ダメージ・追加4回目\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_4th', 'key_upgrade': 'DamageFormula_Additional_4th_Upgraded'}, # ラベル修正？
    {'label': '追加ダメージ(火傷時)', 'pattern': r"追加ダメージ\(火傷時\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_Burned', 'key_upgrade': 'DamageFormula_Additional_Burned_Upgraded'},
    {'label': '追加ダメージ(通常)', 'pattern': r"追加ダメージ・通常\s*[:：]\s*(.*)", 'types': ['basic_attack', 'move'], 'key_base': 'DamageFormula_Additional_Normal', 'key_upgrade': 'DamageFormula_Additional_Normal_Upgraded'},
    {'label': '追加ダメージ(強化)', 'pattern': r"追加ダメージ・強化\s*[:：]\s*(.*)", 'types': ['basic_attack', 'move'], 'key_base': 'DamageFormula_Additional_Boosted', 'key_upgrade': 'DamageFormula_Additional_Boosted_Upgraded'},
    {'label': '追加ダメージ(ブレード)', 'pattern': r"追加ダメージ\(ブレード\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'DamageFormula_Additional_Blade'},
    {'label': '追加ダメージ(壁衝突)', 'pattern': r"追加ダメージ・壁衝突\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_WallCollision', 'key_upgrade': 'DamageFormula_Additional_WallCollision_Upgraded'},
    {'label': '追加ダメージ(パワースワップ)', 'pattern': r"追加ダメージ・パワースワップ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_PowerSwap', 'key_upgrade': 'DamageFormula_Additional_PowerSwap_Upgraded'},
    {'label': '継続ダメージ',       'pattern': r"継続ダメージ\s*[:：]\s*(.*)",       'types': ['move', 'ability'], 'key_base': 'DamageFormula_DoT', 'key_upgrade': 'DamageFormula_DoT_Upgraded'},
    {'label': 'ダメージ・継続(1Hit)', 'pattern': r"ダメージ・継続\(1Hit\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_DoT_PerHit', 'key_upgrade': 'DamageFormula_DoT_PerHit_Upgraded'},
    {'label': '火傷ダメージ',       'pattern': r"火傷ダメージ\s*[:：]\s*(.*)",       'types': ['move', 'ability'], 'key_base': 'DamageFormula_Burn', 'key_upgrade': 'DamageFormula_Burn_Upgraded'},
    {'label': '毒ダメージ',       'pattern': r"毒ダメージ\s*[:：]\s*(.*)",       'types': ['move', 'ability'], 'key_base': 'DamageFormula_Poison', 'key_upgrade': 'DamageFormula_Poison_Upgraded'},
    {'label': 'エリア設置ダメージ', 'pattern': r"エリア設置ダメージ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Area', 'key_upgrade': 'DamageFormula_Area_Upgraded'},
    {'label': '「10万ボルト」使用時', 'pattern': r"「10万ボルト」使用時\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Synergy_VoltTackle'},
    {'label': 'ダメージ(「ひかりのかべ」強化)', 'pattern': r"ダメージ・「ひかりのかべ」強化\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Synergy_LightScreen'},
    {'label': 'ダメージ(亀裂)', 'pattern': r"ダメージ・亀裂\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Crack', 'key_upgrade': 'DamageFormula_Crack_Upgraded'},
    {'label': 'ダメージ(岩石設置)', 'pattern': r"ダメージ・岩石設置\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_RockSet', 'key_upgrade': 'DamageFormula_RockSet_Upgraded'},
    {'label': 'ダメージ(岩石解除)', 'pattern': r"ダメージ・岩石解除\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_RockRelease', 'key_upgrade': 'DamageFormula_RockRelease_Upgraded'},
    {'label': 'ダメージ(周囲)', 'pattern': r"ダメージ・周囲\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Surround', 'key_upgrade': 'DamageFormula_Surround_Upgraded'},
    {'label': 'ダメージ(範囲ヒット)', 'pattern': r"ダメージ・範囲\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_AreaHit', 'key_upgrade': 'DamageFormula_AreaHit_Upgraded'},
    {'label': 'ダメージ(反撃)', 'pattern': r"ダメージ・反撃\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DamageFormula_Counter', 'key_upgrade': 'DamageFormula_Counter_Upgraded'},
    {'label': 'ダメージ(共通)', 'pattern': r"ダメージ\(共通\)\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'DamageFormula_Common'},
    {'label': '自傷ダメージ',   'pattern': r"自傷ダメージ\s*[:：]\s*(.*)",   'types': ['move', 'ability', 'common'], 'key_base': 'DamageFormula_SelfInflicted'},
    {'label': '自傷ダメージ(毎秒)', 'pattern': r"自傷ダメージ\(毎秒\)\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'DamageFormula_SelfInflicted_PerSecond'},
    {'label': 'ダメージ(解放)',   'pattern': r"ダメージ・解放\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Release', 'key_upgrade': 'DamageFormula_Release_Upgraded'},
    {'label': 'ダメージ(先端)', 'pattern': r"ダメージ・先端\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Tip', 'key_upgrade': 'DamageFormula_Tip_Upgraded'},
    {'label': 'ダメージ・必中(エナジー0)', 'pattern': r"ダメージ・必中\(エナジー0\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SureHit_Energy0', 'key_upgrade': 'DamageFormula_SureHit_Energy0_Upgraded'},
    {'label': 'ダメージ・必中(エナジー1)', 'pattern': r"ダメージ・必中\(エナジー1\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SureHit_Energy1', 'key_upgrade': 'DamageFormula_SureHit_Energy1_Upgraded'},
    {'label': 'ダメージ・必中(エナジー2)', 'pattern': r"ダメージ・必中\(エナジー2\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SureHit_Energy2', 'key_upgrade': 'DamageFormula_SureHit_Energy2_Upgraded'},
    {'label': 'ダメージ・必中(エナジー3)', 'pattern': r"ダメージ・必中\(エナジー3\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SureHit_Energy3', 'key_upgrade': 'DamageFormula_SureHit_Energy3_Upgraded'},
    {'label': 'ダメージ(爆発)', 'pattern': r"ダメージ・爆発\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Explosion', 'key_upgrade': 'DamageFormula_Explosion_Upgraded'},
    {'label': 'ダメージ(拡散)', 'pattern': r"ダメージ・拡散\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Spread', 'key_upgrade': 'DamageFormula_Spread_Upgraded'},
    {'label': 'ダメージ(炎)', 'pattern': r"ダメージ・炎\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Flame', 'key_upgrade': 'DamageFormula_Flame_Upgraded'},
    {'label': 'ダメージ(つきとばし)', 'pattern': r"ダメージ・つきとばし\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Knockback', 'key_upgrade': 'DamageFormula_Knockback_Upgraded'},
    {'label': 'ダメージ(念波)',   'pattern': r"ダメージ・念波\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Psywave', 'key_upgrade': 'DamageFormula_Psywave_Upgraded'},
    {'label': 'ダメージ(溜め無)', 'pattern': r"ダメージ\(溜め無\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeNone', 'key_upgrade': 'DamageFormula_ChargeNone_Upgraded'},
    {'label': 'ダメージ(溜め弱)', 'pattern': r"ダメージ・溜め弱\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeWeak', 'key_upgrade': 'DamageFormula_ChargeWeak_Upgraded'}, # 溜め小と統合？
    {'label': 'ダメージ(溜め小)', 'pattern': r"ダメージ\(溜め小\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeSmall', 'key_upgrade': 'DamageFormula_ChargeSmall_Upgraded'},
    {'label': 'ダメージ(溜め中)', 'pattern': r"ダメージ\(溜め中\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeMedium', 'key_upgrade': 'DamageFormula_ChargeMedium_Upgraded'},
    {'label': 'ダメージ(溜め強)', 'pattern': r"ダメージ・溜め強\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeStrong', 'key_upgrade': 'DamageFormula_ChargeStrong_Upgraded'}, # 溜め大と統合？
    {'label': 'ダメージ(溜め大)', 'pattern': r"ダメージ\(溜め大\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeLarge', 'key_upgrade': 'DamageFormula_ChargeLarge_Upgraded'},
    {'label': 'ダメージ(溜め1)', 'pattern': r"ダメージ・溜め1\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Charge1', 'key_upgrade': 'DamageFormula_Charge1_Upgraded'},
    {'label': 'ダメージ(溜め2)', 'pattern': r"ダメージ・溜め2\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Charge2', 'key_upgrade': 'DamageFormula_Charge2_Upgraded'},
    {'label': 'ダメージ(溜め3)', 'pattern': r"ダメージ・溜め3\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Charge3', 'key_upgrade': 'DamageFormula_Charge3_Upgraded'},
    {'label': 'ダメージ(溜め4)', 'pattern': r"ダメージ\(溜め4\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Charge4', 'key_upgrade': 'DamageFormula_Charge4_Upgraded'},
    {'label': 'ダメージ(溜め5)', 'pattern': r"ダメージ\(溜め5\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Charge5', 'key_upgrade': 'DamageFormula_Charge5_Upgraded'},
    {'label': 'ダメージ(溜め最小)', 'pattern': r"ダメージ・溜め最小\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeMin', 'key_upgrade': 'DamageFormula_ChargeMin_Upgraded'},
    {'label': 'ダメージ(溜め最大)', 'pattern': r"ダメージ・溜め最大\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeMax', 'key_upgrade': 'DamageFormula_ChargeMax_Upgraded'},
    {'label': 'ダメージ(影)',   'pattern': r"ダメージ・影\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Shadow', 'key_upgrade': 'DamageFormula_Shadow_Upgraded'},
    {'label': 'ダメージ(非貫通)', 'pattern': r"ダメージ・非貫通\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_NonPierce', 'key_upgrade': 'DamageFormula_NonPierce_Upgraded'},
    {'label': 'ダメージ(貫通)',   'pattern': r"ダメージ・貫通\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Pierce', 'key_upgrade': 'DamageFormula_Pierce_Upgraded'},
    {'label': 'ダメージ(牙)',   'pattern': r"ダメージ・牙\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Fang', 'key_upgrade': 'DamageFormula_Fang_Upgraded'},
    {'label': 'ダメージ(叩きつけ)', 'pattern': r"ダメージ・叩きつけ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Slam', 'key_upgrade': 'DamageFormula_Slam_Upgraded'},
    {'label': 'ダメージ(踏みならし)', 'pattern': r"ダメージ・踏みならし\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stomp', 'key_upgrade': 'DamageFormula_Stomp_Upgraded'},
    {'label': 'ダメージ(ビーム)', 'pattern': r"ダメージ・ビーム\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Beam', 'key_upgrade': 'DamageFormula_Beam_Upgraded'},
    {'label': 'ダメージ(突進)', 'pattern': r"ダメージ・突進\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Dash', 'key_upgrade': 'DamageFormula_Dash_Upgraded'},
    {'label': 'ダメージ(ボム)', 'pattern': r"ダメージ・ボム\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Bomb', 'key_upgrade': 'DamageFormula_Bomb_Upgraded'},
    {'label': 'ダメージ(飛び蹴り)', 'pattern': r"ダメージ・飛び蹴り\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_JumpKick', 'key_upgrade': 'DamageFormula_JumpKick_Upgraded'},
    {'label': 'ダメージ(引き寄せ)', 'pattern': r"ダメージ・引き寄せ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Pull', 'key_upgrade': 'DamageFormula_Pull_Upgraded'},
    {'label': 'ダメージ(雷)', 'pattern': r"ダメージ・雷\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Thunder', 'key_upgrade': 'DamageFormula_Thunder_Upgraded'},
    {'label': 'ダメージ(息吹)', 'pattern': r"ダメージ・息吹\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Breath', 'key_upgrade': 'DamageFormula_Breath_Upgraded'},
    {'label': 'ダメージ(炸裂)', 'pattern': r"ダメージ・炸裂\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Burst', 'key_upgrade': 'DamageFormula_Burst_Upgraded'},
    {'label': 'ダメージ(斬り込み)', 'pattern': r"ダメージ・斬り込み\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_SlashIn', 'key_upgrade': 'DamageFormula_SlashIn_Upgraded'},
    {'label': 'ダメージ(アッパー)', 'pattern': r"ダメージ・アッパー\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Upper', 'key_upgrade': 'DamageFormula_Upper_Upgraded'},
    {'label': 'ダメージ(キャッチ)', 'pattern': r"ダメージ・キャッチ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Catch'}, # 値はテキスト
    {'label': 'ダメージ(レベル1)', 'pattern': r"ダメージ・レベル1\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ByLevel1'},
    {'label': 'ダメージ(レベル2)', 'pattern': r"ダメージ・レベル2\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ByLevel2'},
    {'label': 'ダメージ(レベル2継続)', 'pattern': r"ダメージ・レベル2継続\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ByLevel2_DoT'},
    {'label': 'ダメージ(レベル3)', 'pattern': r"ダメージ・レベル3\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ByLevel3'},

    # --- HP Recovery ---
    {'label': 'HP回復(毎秒)', 'pattern': r"HP回復\(毎秒\)\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'HPRecovery_PerSecond'}, # 値はテキスト
    {'label': 'HP回復(一発当たり)',   'pattern': r"HP回復・一発当たり\s*[:：]\s*(.*)",   'types': ['move'], 'key_base': 'HPRecovery_PerShot', 'key_upgrade': 'HPRecovery_PerShot_Upgraded'},
    {'label': 'HP回復(ダメージ依存)', 'pattern': r"HP回復\s*[:：]\s*ダメージ\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_BasedOnDamage', 'key_upgrade': 'HPRecovery_BasedOnDamage_Upgraded'},
    {'label': 'HP回復(追加4回目)',  'pattern': r"HP回復・追加4回目\s*[:：]\s*(.*)",  'types': ['move'], 'key_base': 'HPRecovery_Additional_4th', 'key_upgrade': 'HPRecovery_Additional_4th_Upgraded'}, # 値はテキスト
    {'label': 'HP回復(ぬめぬめアリ)', 'pattern': r"HP回復\(ぬめぬめアリ\)\s*[:：]\s*(.*)", 'types': ['ability'], 'key_base': 'HPRecovery_GoomyAlly'}, # 値はテキスト
    {'label': '回復(汎用)', 'pattern': r"回復\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'Recovery_Generic'}, # HP回復より先に置く、値はテキスト
    {'label': 'HP回復(1Hit)', 'pattern': r"HP回復\(1Hit\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_PerHit'}, # 値はテキスト
    {'label': 'HP回復(野生)', 'pattern': r"HP回復・野生\s*[:：]\s*(.*)", 'types': ['ability', 'move'], 'key_base': 'HPRecovery_Wild', 'key_upgrade': 'HPRecovery_Wild_Upgraded'},
    {'label': 'HP回復(強化(シールド))', 'pattern': r"HP回復・強化\(シールド\)\s*[:：]\s*(.*)", 'types': ['basic_attack'], 'key_base': 'HPRecovery_Boosted_Shield'},
    {'label': 'HP回復(継続)', 'pattern': r"HP回復・継続\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'HPRecovery_Continuous', 'key_upgrade': 'HPRecovery_Continuous_Upgraded'},
    {'label': 'HP回復(着弾)', 'pattern': r"HP回復・着弾\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_OnHit', 'key_upgrade': 'HPRecovery_OnHit_Upgraded'},
    {'label': 'HP回復(HoT)', 'pattern': r"HP回復・HoT\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_HoT', 'key_upgrade': 'HPRecovery_HoT_Upgraded'},
    {'label': 'HP回復(+)', 'pattern': r"HP回復\(\+\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_Plus'}, # 値はテキスト
    {'label': 'HP回復(1-2)', 'pattern': r"HP回復\(1~2\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_Hit_1_2', 'key_upgrade': 'HPRecovery_Hit_1_2_Upgraded'}, # 値はテキスト
    {'label': 'HP回復(3-4)', 'pattern': r"HP回復\(3~4\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_Hit_3_4', 'key_upgrade': 'HPRecovery_Hit_3_4_Upgraded'}, # 値はテキスト
    {'label': 'HP回復(5-6)', 'pattern': r"HP回復\(5~6\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_Hit_5_6', 'key_upgrade': 'HPRecovery_Hit_5_6_Upgraded'}, # 値はテキスト
    {'label': 'HP回復(7-8)', 'pattern': r"HP回復\(7~8\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_Hit_7_8', 'key_upgrade': 'HPRecovery_Hit_7_8_Upgraded'}, # 値はテキスト
    {'label': 'HP回復(最終段)', 'pattern': r"HP回復・最終段\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_FinalHit'}, # 値はテキスト
    {'label': 'HP回復(追加入力)', 'pattern': r"HP回復・追加入力\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_ExtraInput', 'key_upgrade': 'HPRecovery_ExtraInput_Upgraded'}, # 値はテキスト
    {'label': 'HP回復',           'pattern': r"HP回復\s*[:：]\s*(.*)", 'types': ['move','ability','common'], 'key_base': 'HPRecovery'}, # 一般的なHP回復

    # --- Shield / Buffs / Debuffs / Other ---
    {'label': 'シールド付与', 'pattern': r"シールド付与\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'ShieldAmountFormula', 'key_upgrade': 'ShieldAmountFormula_Upgraded'}, # 値はテキストの場合あり
    {'label': '追加シールド付与', 'pattern': r"追加シールド付与\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'ShieldAmountFormula_Additional', 'key_upgrade': 'ShieldAmountFormula_Additional_Upgraded'},
    {'label': 'シールド変換(基礎)', 'pattern': r"シールド変換・基礎\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'ShieldConversion_Base', 'key_upgrade': 'ShieldConversion_Base_Upgraded'},
    {'label': 'シールド変換(追加_花)', 'pattern': r"シールド変換・追加\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'ShieldConversion_Additional_Flower', 'key_upgrade': 'ShieldConversion_Additional_Flower_Upgraded'}, # 値はテキスト
    {'label': 'シールド変換', 'pattern': r"シールド変換\s*[:：]\s*(.*)", 'types': ['ability', 'move'], 'key_base': 'ShieldConversionFormula'}, # 値はテキスト
    {'label': 'シールド(一撃)', 'pattern': r"シールド\(一撃\)\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'ShieldFormula_UrshifuSingle'},
    {'label': 'シールド(溜め)', 'pattern': r"シールド・溜め\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'ShieldFormula_Charged'}, # 値はテキスト
    {'label': 'シールド(追加)', 'pattern': r"シールド・追加\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'ShieldFormula_Additional', 'key_upgrade': 'ShieldFormula_Additional_Upgraded'},
    {'label': 'シールド',         'pattern': r"シールド\s*[:：]\s*(.*)", 'types': ['move','ability','common'], 'key_base': 'ShieldFormula_Base', 'key_upgrade': 'ShieldFormula_Upgraded'}, # 一般的なシールド
    {'label': '防御・特防アップ', 'pattern': r"防御・特防アップ\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DefenseIncreaseFormula', 'key_upgrade': 'DefenseIncreaseFormula_Upgraded'},
    {'label': '防御・特防増加量(1スタック当たり)', 'pattern': r"防御・特防(?:増加量|上昇)\(1?スタック当たり\)\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'DefenseIncreaseFormula_PerStack'}, # ラベル揺れ対応
    {'label': '防御・特防上昇(per stack)', 'pattern': r"防御・特防上昇\(per stack\)\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DefenseIncreaseFormula_PerStack_Alt'}, # 英語ラベル用
    {'label': '攻撃上昇', 'pattern': r"攻撃上昇\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'AttackUpFormula', 'key_upgrade': 'AttackUpFormula_Upgraded'},
    {'label': '防御アップ', 'pattern': r"防御アップ\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DefenseUpFormula', 'key_upgrade': 'DefenseUpFormula_Upgraded'},
    {'label': '防御上昇', 'pattern': r"防御上昇\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DefenseUpFormula_Alt', 'key_upgrade': 'DefenseUpFormula_Alt_Upgraded'},
    {'label': '特防上昇', 'pattern': r"特防上昇\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'SpDefenseUpFormula', 'key_upgrade': 'SpDefenseUpFormula_Upgraded'},
    {'label': '攻撃速度アップ', 'pattern': r"攻撃速度アップ\s*[:：]\s*\[(.*?)\]%", 'types': ['move', 'ability', 'common'], 'key_base': 'AttackSpeedIncreaseFormula'}, # [...]% 形式
    {'label': '攻撃速度アップ(テキスト)', 'pattern': r"攻撃速度アップ\s*[:：]\s*(.*)", 'types': ['move', 'ability', 'common'], 'key_base': 'AttackSpeedIncreaseText'}, # テキスト形式
    {'label': '特防ダウン', 'pattern': r"特防ダウン\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'SpDefenseDownFormula', 'key_upgrade': 'SpDefenseDownFormula_Upgraded'},
    {'label': '防御ダウン', 'pattern': r"防御ダウン\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DefenseDownFormula', 'key_upgrade': 'DefenseDownFormula_Upgraded'},
    {'label': '防御貫通', 'pattern': r"防御貫通\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DefensePenetrationFormula', 'key_upgrade': 'DefensePenetrationFormula_Upgraded'},
    {'label': 'ダメージ上限(1hit)', 'pattern': r"ダメージ上限\(1hit\)\s*[:：]\s*(\d+)", 'types': ['move'], 'key_base': 'DamageCap_PerHit'},
    {'label': 'ダメージ上限', 'pattern': r"ダメージ上限\s*[:：]\s*(\d+)", 'types': ['move', 'common'], 'key_base': 'DamageCap'},
    {'label': '回復(per tick)', 'pattern': r"回復\(per tick\)\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'Recovery_PerTick'}, # 値はテキスト
    {'label': 'メロメロ時間', 'pattern': r"メロメロ状態・時間\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'CharmDurationFormula'}, # 値はテキスト
    # ゲージ満タン時の追加効果
    {'label': '追加ダメージ(ゲージ満タン)', 'pattern': r"追加ダメージ・ゲージ満タン\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Additional_FullGauge', 'key_upgrade': 'DamageFormula_Additional_FullGauge_Upgraded'},
    {'label': 'HP回復(ゲージ満タン)', 'pattern': r"HP回復・ゲージ満タン\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'HPRecovery_FullGauge', 'key_upgrade': 'HPRecovery_FullGauge_Upgraded'},

    # 新しいダメージタイプ
    {'label': 'ダメージ(円)', 'pattern': r"ダメージ・円\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Circle', 'key_upgrade': 'DamageFormula_Circle_Upgraded'},

    # 新しいステータス効果
    {'label': '最大HP増加', 'pattern': r"最大HP増加\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'MaxHPIncreaseFormula', 'key_upgrade': 'MaxHPIncreaseFormula_Upgraded'},

    {'label': 'ダメージ(念力の弾)', 'pattern': r"ダメージ・念力の弾\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_PsywaveBullet', 'key_upgrade': 'DamageFormula_PsywaveBullet_Upgraded'},
    {'label': 'ダメージ(切り付け)', 'pattern': r"ダメージ・切り付け\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Slash', 'key_upgrade': 'DamageFormula_Slash_Upgraded'},
    {'label': 'ダメージ(格闘)', 'pattern': r"ダメージ（格闘）\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Fighting', 'key_upgrade': 'DamageFormula_Fighting_Upgraded'},
    {'label': 'ダメージ(1段目・格闘)', 'pattern': r"ダメージ・1段目（格闘）\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage1_Fighting', 'key_upgrade': 'DamageFormula_Stage1_Fighting_Upgraded'},
    {'label': 'ダメージ(2段目・格闘)', 'pattern': r"ダメージ・2段目（格闘）\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_Stage2_Fighting', 'key_upgrade': 'DamageFormula_Stage2_Fighting_Upgraded'},
    {'label': 'ダメージ(溜めなし)', 'pattern': r"ダメージ\(溜めなし\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeNone', 'key_upgrade': 'DamageFormula_ChargeNone_Upgraded'},
    {'label': 'ダメージ(最大溜め)', 'pattern': r"ダメージ\(最大溜め\)\s*[:：]\s*(.*)", 'types': ['move'], 'key_base': 'DamageFormula_ChargeMax', 'key_upgrade': 'DamageFormula_ChargeMax_Upgraded'},
    {'label': 'HP回復(相手)', 'pattern': r"HP回復（相手チーム）\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'HPRecovery_Opponent', 'key_upgrade': 'HPRecovery_Opponent_Upgraded'},
    {'label': 'HP回復(野生_括弧)', 'pattern': r"HP回復（野生）\s*[:：]\s*(.*)", 'types': ['ability', 'move'], 'key_base': 'HPRecovery_Wild', 'key_upgrade': 'HPRecovery_Wild_Upgraded'},
    {'label': 'シールド(激流)', 'pattern': r"激流\s+シールド\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'ShieldFormula_Torrent', 'key_upgrade': 'ShieldFormula_Torrent_Upgraded'},
    {'label': 'ダメージ(激流)', 'pattern': r"激流\s+ダメージ\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DamageFormula_Torrent', 'key_upgrade': 'DamageFormula_Torrent_Upgraded'},
    {'label': 'ダメージ(激流・渦)', 'pattern': r"激流\s+ダメージ・渦\s*[:：]\s*(.*)", 'types': ['move', 'ability'], 'key_base': 'DamageFormula_Torrent_Vortex', 'key_upgrade': 'DamageFormula_Torrent_Vortex_Upgraded'},
    
    # --- 一般的なダメージ (他のすべてのダメージパターンより後に置く) ---
    {'label': 'ダメージ(一般)',   'pattern': r"ダメージ\s*[:：]\s*(.*)", 'types': ['ability','move','basic_attack'], 'key_base': 'DamageFormula_Base', 'key_upgrade': 'DamageFormula_Upgraded', 'key_ability': 'DamageFormula'},
]
