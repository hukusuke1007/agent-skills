---
name: media-transcriber
description: 動画/音声ファイルをタイムスタンプ付きで文字起こしし、要約まで行うスキル。「動画を文字起こしして」「この音声を要約して」「会議の録画をまとめて」「mp4を文字起こしして要約して」「インタビュー音声から議事録作って」などのリクエストで使用する。OpenAI Whisper（ローカル）でタイムスタンプ付き全文mdを生成し、Claude自身がその全文を読んで要約mdを別ファイルで書き出す。出力先はプロジェクトルート直下（`TRANSCRIPT_OUTPUT_PATH` で変更可）。
license: MIT
author: shohei
version: 1.1.0
---

# 動画/音声 文字起こし + 要約

動画 or 音声ファイルを OpenAI Whisper (ローカル) で文字起こしし、全文md と 要約md の 2ファイルを出力するスキル。

対応拡張子: mp3 / m4a / wav / ogg / flac / mp4 / mov / mkv / webm / avi など（whisper が内部で ffmpeg を呼ぶため動画もそのまま渡せる）。

## 実行手順

1. ユーザーが指定したファイルパスを確定する（ドラッグ&ドロップ時は引用符で囲む）
2. 以下のコマンドで文字起こしを実行:

基本（推奨デフォルト: `turbo` = large-v3-turbo + Whisper自然分割）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --language ja
```

最高精度（固有名詞多い議事録・重要案件）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --model large-v3 --language ja
```

軽量・高速（下書き用途）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --model base --language ja
```

N秒ごとに強制区切り（約5秒刻みで拾いたい）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --language ja --segment-seconds 5
```

文（センテンス）単位で区切る（句読点検出＋最大60秒cap）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --language ja --sentence
```

単語ごと（発話タイミング分析用、行数が大量に増えるので注意）:

```bash
python .claude/skills/media-transcriber/scripts/transcribe.py "入力ファイル" --language ja --word-level
```

1. 出力された全文md (`<プロジェクトルート>/YYYYMMDD_HHMMSS_{basename}.md`) を `Read` で読む
2. 全文の内容を踏まえて、Claude自身が **要約md を `Write` で作成する**。ファイル名は `YYYYMMDD_HHMMSS_{basename}_summary.md`（全文mdと同じタイムスタンプ・同じディレクトリ）。要約の構成は下記「要約mdテンプレ」を既定とし、ユーザー指示があればそれに従う
3. 全文mdと要約mdの両パスをユーザーに報告する

## 引数

| 引数                     | 説明                                                                                    | デフォルト  |
| ------------------------ | --------------------------------------------------------------------------------------- | ----------- |
| `file`                   | 入力音声/動画ファイルパス（必須）                                                       | —           |
| `--model`                | whisperモデル名 (`tiny` / `base` / `small` / `medium` / `large-v3` / `turbo`)           | `turbo`     |
| `--language`             | 言語コード（例: `ja`, `en`）。未指定時は自動検出                                        | auto-detect |
| `--output-format`        | 出力フォーマット (`md` / `json`)                                                        | `md`        |
| `--segment-seconds`      | N秒ごとに行を区切る                                                                     | 未指定      |
| `--sentence`             | 文（センテンス）単位で区切る。句読点検出＋上限秒capで再チャンク                         | false       |
| `--word-level`           | 単語ごとに1行出力。最優先                                                               | false       |
| `--sentence-max-seconds` | `--sentence` 時のフォールバック上限秒。句読点が無い音声で1文が長大化しないよう強制flush | `60.0`      |

**分割粒度の優先順位（上が強い）**: `--word-level` > `--segment-seconds` > `--sentence` > **Whisper自然分割（デフォルト）**

## 設定

プロジェクトルートの `.env` に以下の環境変数を設定する（任意。未設定時はプロジェクトルート直下に出力）:

```text
# 例: transcripts/ 配下に出したい場合
TRANSCRIPT_OUTPUT_PATH=transcripts
```

| 変数名                   | 説明                                                           |
| ------------------------ | -------------------------------------------------------------- |
| `TRANSCRIPT_OUTPUT_PATH` | 出力先ディレクトリ（デフォルト: `.` = プロジェクトルート直下） |

## 出力

### 全文md の例

```markdown
# 文字起こし: meeting_20260421.mp4

- 元ファイル: /path/to/meeting_20260421.mp4
- モデル: medium
- 言語: ja (auto-detected)
- 実行日時: 2026-04-21 14:30:00
- 総尺: 00:45:12

## 全文

[00:00:00] 今日は四半期の振り返りから始めましょう。
[00:00:12] まず売上の件ですが、前年同月比で...
```

- ファイル名: `YYYYMMDD_HHMMSS_{basename}.md`（`basename` は入力ファイルの拡張子を除いた名前）
- 保存先: プロジェクトルート直下（デフォルト）。`.env` の `TRANSCRIPT_OUTPUT_PATH` で上書き可

### 要約md のテンプレ

Claude がこのテンプレを既定の骨格として書き出す:

```markdown
# 要約: meeting_20260421.mp4

- 元ファイル: /path/to/meeting_20260421.mp4
- 総尺: 00:45:12
- 文字起こし: 20260421_143000_meeting_20260421.md

## 概要

3〜5行で全体像

## キーポイント

- 箇条書き5〜8個

## トピック別まとめ

### トピック1

...

## 次のアクション

- 担当 / 期限 / 内容
```

- ファイル名: `YYYYMMDD_HHMMSS_{basename}_summary.md`（全文mdと同じタイムスタンプ）
- 保存先: 全文mdと同じディレクトリ

### 要約の注意点

クライアント会議録にも使うため、CLAUDE.md のトーンルールに従う:

- 「全滅」「即停止」「劣後」「死蔵」「失敗」等のネガティブ断定語は**使わない**
- 数値での事実提示はOK。事実に対する評価表現で相手を否定しない
- ユーザーから別のトーン指示があればそれを優先する

## モデル選択の目安

| モデル     | サイズ | 速度   | 日本語精度  | 用途                               |
| ---------- | ------ | ------ | ----------- | ---------------------------------- |
| `tiny`     | ~75MB  | 超高速 | 低          | 下書き・英語短尺                   |
| `base`     | ~150MB | 高速   | 中の下      | 英語短尺・スピード優先             |
| `small`    | ~500MB | 中速   | 中          | 簡易な日本語                       |
| `medium`   | ~1.5GB | やや遅 | 高          | 旧定番（turboで置き換え可）        |
| `turbo`    | ~1.5GB | 高速   | 高 (v2相当) | **推奨デフォルト**（日本語・汎用） |
| `large-v3` | ~3GB   | 遅い   | 最高        | 固有名詞多め・重要な議事録         |

**2025年の実測比較**では日本語用途で `turbo` (large-v3-turbo) が speed/accuracy のバランス最優秀。`medium` とメモリ・速度が同等で精度は同等以上なので、通常 `turbo` を第一選択に。最高精度が必要なときのみ `large-v3`。

初回実行時はモデルが `~/.cache/whisper/` にダウンロードされる（1回だけ）。`turbo` は約1.5GB。

## 依存パッケージ確認

初回エラー時は以下でインストール:

```bash
pip install -U openai-whisper python-dotenv
```

ffmpeg が別途必要（whisper が内部で呼ぶ）:

```bash
brew install ffmpeg
```
