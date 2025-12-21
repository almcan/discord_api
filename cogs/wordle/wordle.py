import re
# import psycopg2
# from dotenv import load_dotenv
# import os

async def makewordlist(pool, mode=5):
    cmd = "SELECT name FROM pokedex;"
    
    # 接続プールから1つ回線を借りる
    async with pool.acquire() as conn:
        # SQL実行 (fetchで全件取得)
        rows = await conn.fetch(cmd)
        
        # データの整形 (asyncpgの行データは辞書のように扱えます)
        # rows はリストなので、カーソル枯渇の心配はありません
        words_ = [re.sub(r'\(.*\)', '', x['name']) for x in rows]
    
    words = []
    if (mode > 0):
        for x in words_:
            if (x == 'イエッサン♀' or x == 'ニャオニクス♀'):
                continue
            elif(x == 'イエッサン♂'):
                x = 'イエッサン'
            elif(x == 'ニャオニクス♂'):
                x = 'ニャオニクス'
            if (len(x) == mode):
                words.append(x)

    else: #イエッサンとニャオニクスを統合
        for x in words_:
            if (x == 'イエッサン♀' or x == 'ニャオニクス♀'):
                continue
            elif(x == 'イエッサン♂'):
                x = 'イエッサン'
            elif(x == 'ニャオニクス♂'):
                x = 'ニャオニクス'
            words.append(x)

    return list(set(words))

async def is_correctpokename(pool, pokename):
    cmd="SELECT name FROM pokedex;"

    async with pool.acquire() as conn:
        rows = await conn.fetch(cmd)
        # asyncpgの結果は辞書型のようにアクセスします (x[0] ではなく x['name'])
        word = [re.sub(r'\(.*\)', '', x['name']) for x in rows]
    word.remove('イエッサン♂')
    word.remove('ニャオニクス♂')
    word.remove('イエッサン♀')
    word.remove('ニャオニクス♀')
    word.append('イエッサン')
    word.append('ニャオニクス')
    return pokename in word