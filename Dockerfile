# Python 3.13 をベースにする
FROM python:3.13-slim

# 作業ディレクトリを作成
WORKDIR /app

# ライブラリ一覧をコピーしてインストール
COPY requirements.txt .
# ffmpeg が必要（音声再生のため）
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# ソースコードを全てコピー
COPY . .

# ボットを起動
CMD ["python", "main.py"]