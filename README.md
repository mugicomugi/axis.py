# axis.py

[AXIS](https://axis.prioris.jp/) リアルタイム情報配信サービス用のPythonクライアントライブラリです。

## 特徴

- **シンプルなデコレータAPI** — `@client.on("channel")` でメッセージハンドラを登録
- **自動再接続** — Exponential Backoff アルゴリズムによる再接続
- **型付きメッセージモデル** — 各チャンネルのメッセージを `dataclass` で型定義
- **トークン管理** — トークンリフレッシュAPIに対応

## 対応チャンネル

| チャンネル | 説明 | モデル |
|---|---|---|
| `eew` | 緊急地震速報 (beta) | `EEWMessage` |
| `quake-one` | 地震概要・震度情報 | `QuakeOneMessage` |
| `breaking-news` | ニュース速報 (beta) | `BreakingNewsMessage` |
| `jmx-seismology` | 気象庁電文（地震） | `JMXSeismologyMessage` |
| `jmx-meteorology` | 気象庁電文（気象） | `JMXMeteorologyMessage` |
| `jmx-volcanology` | 気象庁電文（火山） | `JMXVolcanologyMessage` |

## インストール

```bash
pip install axis-prioris
```

## 使い方

### 基本

```python
from axis import AxisClient

client = AxisClient(token="YOUR_TOKEN")

@client.on("eew")
def on_eew(message):
    print(f"緊急地震速報: M{message.Magnitude} {message.Hypocenter.Name}")

@client.on("quake-one")
def on_quake(message):
    print(f"地震情報: {message.headline}")

@client.on("breaking-news")
def on_news(message):
    print(f"速報: {message.Title}")
    for line in message.Text:
        print(f"  {line}")

client.start()  # ブロッキング接続
```

### 全チャンネルの受信

```python
@client.on_all
def on_any(channel, message):
    print(f"[{channel}] {message}")
```

### 非ブロッキング接続

```python
thread = client.start_async()

# ... 他の処理 ...

client.stop()
thread.join()
```

### 接続イベント

```python
@client.on_connect
def connected():
    print("AXIS に接続しました")

@client.on_error
def error(err):
    print(f"エラー: {err}")

@client.on_close
def closed(code, msg):
    print(f"切断 (code={code})")
```

### トークンリフレッシュ

```python
try:
    new_token = client.refresh_token()
    print(f"トークンを更新しました")
except AxisTokenExpiredError:
    print("契約が期限切れです。Webサイトで再発行してください。")
```

## 設定オプション

```python
client = AxisClient(
    token="YOUR_TOKEN",
    auto_reconnect=True,   # 自動再接続 (デフォルト: True)
    max_retries=10,        # 最大再接続回数 (デフォルト: 10)
    ping_interval=60,      # Heartbeat間隔 秒 (デフォルト: 60)
)
```

## ログ

標準の `logging` モジュールを使用しています:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## ライセンス

MIT
