#!/usr/bin/env python
"""
画像圧縮・リサイズスクリプト
使い方:
  python compress_images.py 画像1 画像2 ... [--format jpg|png] [--max-size 1920] [--quality 85]
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

project_root = Path.cwd()
load_dotenv(dotenv_path=project_root / ".env")

OUTPUT_DIR = os.getenv("IMAGE_COMPRESS_OUTPUT_PATH", "")

parser = argparse.ArgumentParser(description="画像圧縮・リサイズ")
parser.add_argument("images", nargs="+", help="入力画像パス（複数指定可）")
parser.add_argument(
    "--format",
    choices=["jpg", "png"],
    default=None,
    help="出力フォーマット（省略時は元の拡張子を維持）",
)
parser.add_argument("--max-size", type=int, default=1920, help="長辺の最大ピクセル数（デフォルト: 1920）")
parser.add_argument("--quality", type=int, default=85, help="JPEG品質 1-100（デフォルト: 85）")
args = parser.parse_args()

output_dir = project_root / OUTPUT_DIR
output_dir.mkdir(parents=True, exist_ok=True)


def resolve_output_path(base_dir: Path, stem: str, ext: str) -> Path:
    candidate = base_dir / f"{stem}.{ext}"
    if not candidate.exists():
        return candidate
    counter = 1
    while True:
        candidate = base_dir / f"{stem}_{counter}.{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_ext(input_path: Path, format_arg: str | None) -> str:
    if format_arg == "jpg":
        return "jpg"
    if format_arg == "png":
        return "png"
    ext = input_path.suffix.lower().lstrip(".")
    if ext in ("jpeg", "jpg"):
        return "jpg"
    if ext == "png":
        return "png"
    # 未対応拡張子は JPG にフォールバック
    return "jpg"


def flatten_to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGB", img.size, (255, 255, 255))
        rgba = img.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


success_count = 0
failed = []

for index, image_path_str in enumerate(args.images, start=1):
    input_path = Path(image_path_str).expanduser()
    if not input_path.exists():
        print(f"エラー: ファイルが見つかりません: {input_path}", file=sys.stderr)
        failed.append(str(input_path))
        continue

    try:
        img = Image.open(input_path)
        img.load()
    except Exception as e:
        print(f"エラー: 画像を開けませんでした: {input_path} ({e})", file=sys.stderr)
        failed.append(str(input_path))
        continue

    original_size = input_path.stat().st_size
    original_dims = img.size

    if max(img.size) > args.max_size:
        img.thumbnail((args.max_size, args.max_size), Image.LANCZOS)

    ext = resolve_ext(input_path, args.format)
    output_path = resolve_output_path(output_dir, input_path.stem, ext)

    try:
        if ext == "jpg":
            rgb = flatten_to_rgb(img)
            rgb.save(output_path, format="JPEG", quality=args.quality, optimize=True, progressive=True)
        else:  # png
            img.save(output_path, format="PNG", optimize=True)
    except Exception as e:
        print(f"エラー: 保存に失敗: {input_path} ({e})", file=sys.stderr)
        failed.append(str(input_path))
        continue

    new_size = output_path.stat().st_size
    ratio = (1 - new_size / original_size) * 100 if original_size else 0.0
    print(
        f"[OK] {input_path.name} "
        f"{original_dims[0]}x{original_dims[1]} ({original_size/1024:.1f}KB) "
        f"-> {img.size[0]}x{img.size[1]} ({new_size/1024:.1f}KB, -{ratio:.1f}%) "
        f"=> {output_path}"
    )
    success_count += 1

print(f"\n完了: {success_count}/{len(args.images)} 件")
print(f"出力先: {output_dir}")
if failed:
    print(f"失敗: {len(failed)} 件", file=sys.stderr)
    sys.exit(1)
