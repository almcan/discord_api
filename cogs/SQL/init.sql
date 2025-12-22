-- ==========================================
-- 1. ポケモン図鑑 (Pokedex)
-- ==========================================
CREATE TABLE pokedex (
    id NUMERIC(4, 1) PRIMARY KEY,
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