# Python 3.11 をベースにする
FROM python:3.11-slim

# 作業ディレクトリを作成
WORKDIR /app

# ログをリアルタイムで出す設定
ENV PYTHONUNBUFFERED=1

# 必要なパッケージ（Chromium含む）をインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    chromium \
    chromium-driver \
    fonts-noto-cjk \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# ライブラリ一覧をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# フォントフォルダをコピー（念のためローカルのも入れる）
COPY fonts /app/fonts

# 画像フォルダをコピー
COPY images /app/images

# ソースコードを全てコピー
COPY . .

# ボットを起動
CMD ["python", "main.py"]