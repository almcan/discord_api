-- ==========================================
-- 1. ポケモン図鑑 (Pokedex)
-- ==========================================
CREATE TABLE pokedex (
    id NUMERIC(5, 1) PRIMARY KEY,
    no INTEGER,
    name VARCHAR(50),
    eng VARCHAR(50),
    type1 VARCHAR(20),
    type2 VARCHAR(20),
    ability1 VARCHAR(30),
    ability2 VARCHAR(30),
    ability3 VARCHAR(30),
    h INTEGER,
    a INTEGER,
    b INTEGER,
    c INTEGER,
    d INTEGER,
    s INTEGER,
    icon TEXT
);
-- データインポート
COPY pokedex FROM '/data/pokedex.csv' DELIMITER ',' CSV HEADER;


-- ==========================================
-- 2. タイプ相性表 (Type Chart) ← ここに追記
-- ==========================================
CREATE TABLE type_chart (
    attacker_type VARCHAR(20) PRIMARY KEY,
    dummy_col INTEGER,
    normal NUMERIC(3, 1),
    fire NUMERIC(3, 1),
    water NUMERIC(3, 1),
    electric NUMERIC(3, 1),
    grass NUMERIC(3, 1),
    ice NUMERIC(3, 1),
    fighting NUMERIC(3, 1),
    poison NUMERIC(3, 1),
    ground NUMERIC(3, 1),
    flying NUMERIC(3, 1),
    psychic NUMERIC(3, 1),
    bug NUMERIC(3, 1),
    rock NUMERIC(3, 1),
    ghost NUMERIC(3, 1),
    dragon NUMERIC(3, 1),
    dark NUMERIC(3, 1),
    steel NUMERIC(3, 1),
    fairy NUMERIC(3, 1)
);
-- データインポート
COPY type_chart FROM '/data/typetable.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 3. 技データ (Moves)
-- ==========================================
CREATE TABLE moves (
    name VARCHAR(50) PRIMARY KEY,  -- 技名
    type VARCHAR(20),              -- CSVヘッダー: attribute (タイプ)
    category VARCHAR(20),          -- 分類 (物理/特殊/変化)
    power INTEGER,                 -- 威力 (ハイフンはNULLになる)
    accuracy INTEGER,              -- 命中 (ハイフンはNULLになる)
    pp INTEGER,                    -- PP
    direct VARCHAR(10),            -- 直接攻撃かどうか (直○/直×)
    protect VARCHAR(10),           -- まもるが効くか (守○/守×)
    target VARCHAR(30),            -- 対象 (1体選択など)
    description TEXT               -- 説明文
);

-- データをインポート
COPY moves FROM '/data/move.csv' DELIMITER ',' CSV HEADER NULL '-';
-- ==========================================
-- 4. 言語データ (Language)
-- ==========================================
CREATE TABLE lang (
    id NUMERIC(5, 1) PRIMARY KEY,
    jpn VARCHAR(50),
    eng VARCHAR(50),
    ger VARCHAR(50),
    fra VARCHAR(50),
    kor VARCHAR(50),
    cs VARCHAR(50),
    ct VARCHAR(50)
);

-- データインポート
COPY lang FROM '/data/lang_name.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 5. シングル使用率データ (Singles Usage)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_pokerank_single (
    rank INTEGER PRIMARY KEY,
    form_id INTEGER NOT NULL,
    pokemon VARCHAR(255) NOT NULL
);
COPY home_pokerank_single FROM '/data/pokemon_ranking_single.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 6. ダブル使用率データ (Doubles Usage)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_pokerank_double (
    rank INTEGER PRIMARY KEY,
    form_id INTEGER NOT NULL,
    pokemon VARCHAR(255) NOT NULL
);
COPY home_pokerank_double FROM '/data/pokemon_ranking_double.csv' DELIMITER ',' CSV HEADER;
-- ==========================================
-- 7. シングル特性データ (Singles Abilities)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_ability_single (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    ability VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank) 
);
COPY home_ability_single FROM '/data/ability_single.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 8. ダブル特性データ (Doubles Abilities)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_ability_double (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    ability VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank) 
);
COPY home_ability_double FROM '/data/ability_double.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 9. シングル技データ (Singles Moves)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_move_single (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    move VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_move_single FROM '/data/move_single.csv' DELIMITER ',' CSV HEADER;
-- ==========================================
-- 10. ダブル技データ (Doubles Moves)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_move_double (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    move VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_move_double FROM '/data/move_double.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 11. シングルテラスタイプデータ (Singles Terastal Types)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_terastype_single (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    terastype VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_terastype_single FROM '/data/terastype_single.csv' DELIMITER ',' CSV HEADER;
-- ==========================================
-- 12. ダブルテラスタイプデータ (Doubles Terastal Types)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_terastype_double (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    terastype VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_terastype_double FROM '/data/terastype_double.csv' DELIMITER ',' CSV HEADER;

-- ==========================================
-- 13. アイテムデータ　シングル (Singles Items)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_item_single (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    item VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_item_single FROM '/data/item_single.csv' DELIMITER ',' CSV HEADER;
-- ==========================================
-- 14. アイテムデータ　ダブル (Doubles Items)
-- ==========================================
CREATE TABLE IF NOT EXISTS home_item_double (
    pokemon VARCHAR(255) NOT NULL,
    id INTEGER NOT NULL,
    form INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    item VARCHAR(255) NOT NULL,
    raito NUMERIC(5, 1),
    PRIMARY KEY (id, form, rank)
);
COPY home_item_double FROM '/data/item_double.csv' DELIMITER ',' CSV HEADER;