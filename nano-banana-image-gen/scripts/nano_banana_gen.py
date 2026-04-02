#!/usr/bin/env python
"""
Nano Banana 2 (gemini-3.1-flash-image-preview) 画像生成スクリプト
使い方: python nano_banana_gen.py "プロンプトテキスト"
"""

import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# .env を読み込む（ルートから実行することを前提）
project_root = Path.cwd()
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = os.getenv("GENERATED_IMAGE_OUTPUT_PATH", "0_images/generated")

if not GEMINI_API_KEY:
    print("エラー: GEMINI_API_KEY が .env に設定されていません", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("使い方: python nano_banana_gen.py \"プロンプトテキスト\"", file=sys.stderr)
    sys.exit(1)

prompt = sys.argv[1]

# 出力ディレクトリを作成（プロジェクトルート基準）
output_dir = project_root / OUTPUT_DIR
output_dir.mkdir(parents=True, exist_ok=True)

# タイムスタンプ付きファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = output_dir / f"{timestamp}.png"

# Gemini クライアント初期化
client = genai.Client(api_key=GEMINI_API_KEY)

print(f"生成中: {prompt}")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
)

# 画像を保存
saved = False
for part in response.candidates[0].content.parts:
    if part.inline_data:
        img = Image.open(BytesIO(part.inline_data.data))
        img.save(output_path)
        print(f"保存完了: {output_path}")
        saved = True
        break

if not saved:
    print("エラー: 画像データが返されませんでした", file=sys.stderr)
    sys.exit(1)
