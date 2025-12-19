# Python 3.13 をベースにする
FROM python:3.13-slim

# 作業ディレクトリを作成
WORKDIR /app

# ライブラリ一覧をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードを全てコピー
COPY . .

# ボットを起動
CMD ["python", "main.py"]