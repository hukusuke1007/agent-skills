#!/usr/bin/env python
"""
動画/音声の文字起こしスクリプト (OpenAI Whisper ローカル版)
使い方:
  python transcribe.py 入力ファイル [--model turbo] [--language ja]
    [--segment-seconds N] [--word-level] [--sentence] [--sentence-max-seconds N]

分割粒度の優先順位（上から強い）:
  --word-level          単語ごとに1行
  --segment-seconds N   N秒ごとに行を区切る
  --sentence            文（センテンス）単位で区切る（句読点検出＋上限秒cap）
  （未指定）            Whisper自然分割（デフォルト、30秒ウィンドウ/VAD）

例:
  python transcribe.py meeting.mp4                         # 自然分割（デフォルト）
  python transcribe.py lecture.mp3 --segment-seconds 5     # 約5秒刻み
  python transcribe.py lecture.mp3 --word-level            # 単語ごと
  python transcribe.py meeting.mp4 --sentence              # 文単位
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

project_root = Path.cwd()
load_dotenv(dotenv_path=project_root / ".env")

OUTPUT_DIR = os.getenv("TRANSCRIPT_OUTPUT_PATH", ".")

parser = argparse.ArgumentParser(description="動画/音声の文字起こし (OpenAI Whisper)")
parser.add_argument("file", help="入力音声/動画ファイルパス")
parser.add_argument(
    "--model",
    default="turbo",
    help="whisperモデル（tiny/base/small/medium/large-v2/large-v3/turbo）デフォルト: turbo (large-v3-turbo)",
)
parser.add_argument(
    "--language",
    default=None,
    help="言語コード（例: ja, en）。未指定時はwhisperが自動検出",
)
parser.add_argument(
    "--output-format",
    choices=["md", "json"],
    default="md",
    help="出力フォーマット（md / json）デフォルト: md",
)
parser.add_argument(
    "--segment-seconds",
    type=float,
    default=None,
    help="N秒ごとに行を区切る（単語タイムスタンプから再チャンク）。指定時は文単位分割を上書き",
)
parser.add_argument(
    "--word-level",
    action="store_true",
    help="単語ごとに1行出力する。他の分割指定より優先",
)
parser.add_argument(
    "--sentence",
    action="store_true",
    help="文（センテンス）単位で区切る。句読点検出＋上限秒capで再チャンク",
)
parser.add_argument(
    "--sentence-max-seconds",
    type=float,
    default=60.0,
    help="--sentence 時のフォールバック上限秒数。句読点が無い音声で1文が長大化しないよう強制flushする（デフォルト: 60秒）",
)
args = parser.parse_args()

input_path = Path(args.file).expanduser()
if not input_path.is_absolute():
    input_path = (project_root / input_path).resolve()

if not input_path.exists():
    print(f"エラー: ファイルが見つかりません: {input_path}", file=sys.stderr)
    sys.exit(1)

try:
    import whisper
except ImportError:
    print(
        "エラー: openai-whisper がインストールされていません。\n"
        "  pip install -U openai-whisper\n"
        "また ffmpeg も必要です: brew install ffmpeg",
        file=sys.stderr,
    )
    sys.exit(1)


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


output_dir = project_root / OUTPUT_DIR
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
basename = input_path.stem
ext = "md" if args.output_format == "md" else "json"
output_path = output_dir / f"{timestamp}_{basename}.{ext}"

print(f"入力ファイル: {input_path}")
print(f"モデル読み込み中: {args.model} (初回はダウンロードで時間がかかります)")

model = whisper.load_model(args.model)

lang_label = args.language if args.language else "auto"
# word_timestamps はデフォルト(natural)では不要、それ以外の分割モードでは必要
need_word_timestamps = args.word_level or args.sentence or args.segment_seconds is not None
if args.word_level:
    granularity_label = "word-level"
elif args.segment_seconds is not None:
    granularity_label = f"{args.segment_seconds}s chunks"
elif args.sentence:
    granularity_label = f"sentence (max {args.sentence_max_seconds}s cap)"
else:
    granularity_label = "natural segments (whisper)"
print(f"文字起こし実行中 (language={lang_label}, granularity={granularity_label}) ...")

result = model.transcribe(
    str(input_path),
    language=args.language,
    verbose=False,
    word_timestamps=need_word_timestamps,
)

raw_segments = result.get("segments", [])
detected_language = result.get("language", "unknown")


def collect_words(segments_):
    words = []
    for seg in segments_:
        for w in seg.get("words", []) or []:
            text = w.get("word", "")
            start = w.get("start")
            end = w.get("end")
            if text and start is not None and end is not None:
                words.append({"text": text, "start": start, "end": end})
    return words


def chunk_by_seconds(words, interval):
    chunks = []
    if not words:
        return chunks
    current_start = words[0]["start"]
    current_text = []
    current_end = words[0]["end"]
    for w in words:
        # 現在チャンクの開始から interval を超えたら確定して次へ
        if w["end"] - current_start > interval and current_text:
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": "".join(current_text).strip(),
            })
            current_start = w["start"]
            current_text = [w["text"]]
            current_end = w["end"]
        else:
            current_text.append(w["text"])
            current_end = w["end"]
    if current_text:
        chunks.append({
            "start": current_start,
            "end": current_end,
            "text": "".join(current_text).strip(),
        })
    return chunks


SENTENCE_END = ("。", "？", "！", "?", "!", ".")


def chunk_by_sentence(words, max_seconds):
    chunks = []
    if not words:
        return chunks
    current_start = None
    current_text = []
    current_end = None
    for w in words:
        if current_start is None:
            current_start = w["start"]
        current_text.append(w["text"])
        current_end = w["end"]
        joined = "".join(current_text).rstrip()
        hit_sentence_end = joined.endswith(SENTENCE_END)
        hit_cap = (current_end - current_start) >= max_seconds
        if (hit_sentence_end or hit_cap) and joined:
            chunks.append({
                "start": current_start,
                "end": current_end,
                "text": joined.strip(),
            })
            current_start = None
            current_text = []
    if current_text:
        chunks.append({
            "start": current_start,
            "end": current_end,
            "text": "".join(current_text).strip(),
        })
    return chunks


if args.word_level:
    words = collect_words(raw_segments)
    segments = [
        {"start": w["start"], "end": w["end"], "text": w["text"].strip()}
        for w in words
    ]
elif args.segment_seconds is not None:
    words = collect_words(raw_segments)
    segments = chunk_by_seconds(words, args.segment_seconds)
elif args.sentence:
    words = collect_words(raw_segments)
    segments = chunk_by_sentence(words, args.sentence_max_seconds)
else:
    # デフォルト: Whisper自然分割
    segments = [
        {"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()}
        for seg in raw_segments
    ]

total_duration = segments[-1]["end"] if segments else 0.0

if args.output_format == "json":
    payload = {
        "file": str(input_path),
        "model": args.model,
        "language": detected_language,
        "language_explicit": args.language,
        "executed_at": datetime.now().isoformat(timespec="seconds"),
        "duration_seconds": total_duration,
        "text": result.get("text", ""),
        "granularity": granularity_label,
        "segments": [
            {
                "start": seg["start"],
                "end": seg["end"],
                "start_hms": format_timestamp(seg["start"]),
                "end_hms": format_timestamp(seg["end"]),
                "text": seg["text"].strip(),
            }
            for seg in segments
        ],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
else:
    language_line = (
        f"{detected_language} (auto-detected)"
        if args.language is None
        else f"{args.language}"
    )
    header = (
        f"# 文字起こし: {input_path.name}\n\n"
        f"- 元ファイル: {input_path}\n"
        f"- モデル: {args.model}\n"
        f"- 言語: {language_line}\n"
        f"- 分割粒度: {granularity_label}\n"
        f"- 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 総尺: {format_timestamp(total_duration)}\n\n"
        f"## 全文\n\n"
    )
    body_lines = [
        f"[{format_timestamp(seg['start'])}] {seg['text'].strip()}"
        for seg in segments
    ]
    output_path.write_text(header + "\n".join(body_lines) + "\n", encoding="utf-8")

print(f"保存完了: {output_path}")
print(f"総尺: {format_timestamp(total_duration)} / セグメント数: {len(segments)}")
