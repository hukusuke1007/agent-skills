---
name: nano-banana-image-gen
description: Nano Banana 2（Google Gemini gemini-3.1-flash-image-preview）を使って画像を生成するスキル。「画像を生成して」「〇〇のイラストを作って」「Nano Bananaで画像を作って」「グラレコ風の画像を生成して」などのリクエストで使用する。プロンプトを受け取りpythonスクリプトを実行、タイムスタンプ付きPNGを images/generated/ に出力する。
license: MIT
author: shohei
version: 1.0.0
---

# Nano Banana 画像生成

## 実行手順

1. ユーザーのリクエストから画像生成プロンプトを確定する
2. 以下のコマンドを実行する

```bash
python .claude/skills/nano-banana-image-gen/scripts/nano_banana_gen.py "プロンプトテキスト"
```

1. 出力パスを確認してユーザーに報告する

## 設定

プロジェクトルートの `.env` に以下の環境変数を設定する:

```
GEMINI_API_KEY=your_api_key_here
GENERATED_IMAGE_OUTPUT_PATH=images/generated
```

| 変数名                        | 説明                                                 |
| ----------------------------- | ---------------------------------------------------- |
| `GEMINI_API_KEY`              | Google Gemini APIキー（必須）                        |
| `GENERATED_IMAGE_OUTPUT_PATH` | 出力先ディレクトリ（デフォルト: `images/generated`） |

## 出力

- ファイル名: `YYYYMMDD_HHMMSS.png`
- 保存先: プロジェクトルートの `images/generated/`

## 依存パッケージ確認

初回エラー時は以下でインストール:

```bash
pip install google-genai pillow python-dotenv
```
