#!/usr/bin/env python
"""
Nano Banana 2 (gemini-3.1-flash-image-preview) 画像生成スクリプト
使い方:
  テキストのみ: python nano_banana_gen.py "プロンプトテキスト"
  画像1枚: python nano_banana_gen.py "プロンプトテキスト" --image "画像パス"
  画像複数: python nano_banana_gen.py "プロンプトテキスト" --image "画像1" --image "画像2"
"""

import argparse
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
OUTPUT_DIR = os.getenv("GENERATED_IMAGE_OUTPUT_PATH", "images/generated")

if not GEMINI_API_KEY:
    print("エラー: GEMINI_API_KEY が .env に設定されていません", file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser(description="Nano Banana 2 画像生成")
parser.add_argument("prompt", help="画像生成プロンプト")
parser.add_argument("--image", help="入力画像パス（複数指定可）", action="append", default=[])
args = parser.parse_args()

# 出力ディレクトリを作成（プロジェクトルート基準）
output_dir = project_root / OUTPUT_DIR
output_dir.mkdir(parents=True, exist_ok=True)

# タイムスタンプ付きファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = output_dir / f"{timestamp}.png"

# Gemini クライアント初期化
client = genai.Client(api_key=GEMINI_API_KEY)

# コンテンツを組み立て
contents = []
for img_arg in args.image:
    image_path = Path(img_arg)
    if not image_path.is_absolute():
        image_path = project_root / image_path
    if not image_path.exists():
        print(f"エラー: 画像ファイルが見つかりません: {image_path}", file=sys.stderr)
        sys.exit(1)
    input_img = Image.open(image_path)
    contents.append(input_img)
    print(f"入力画像: {image_path}")

contents.append(args.prompt)
print(f"生成中: {args.prompt}")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=contents,
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
