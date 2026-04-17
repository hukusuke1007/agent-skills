# Agent Skills

さまざまな開発タスクやワークフローで再利用できるエージェントスキル集です。

## インストール

このリポジトリのスキルをインストールするには、以下を実行します:

```bash
npx skills add hukusuke1007/agent-skills
```

## 更新

インストール済みのスキルを更新するには、以下を実行します:

```bash
npx skills update hukusuke1007/agent-skills
```

## 収録スキル一覧

| スキル                                                                                | 説明                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`flutter-riverpod-arch`](./flutter-riverpod-arch/SKILL.md)                           | Feature-First の Flutter アーキテクチャを、Riverpod（コード生成）・Flutter Hooks・レイヤー分割（UI → Use Case → Repository）・テストパターンで実装する。                                                                                                                                          |
| [`nextjs-better-auth-postgres-docker`](./nextjs-better-auth-postgres-docker/SKILL.md) | Next.js（App Router）+ Better Auth + PostgreSQL のアプリを Docker でローカル構築し、Google Cloud Run + Cloud SQL + Secret Manager にデプロイする。                                                                                                                                                |
| [`meti-ai-guideline`](./meti-ai-guideline/SKILL.md)                                   | 経済産業省・総務省「AI事業者ガイドライン」に基づいて、OK/NG判断・チェックリスト・ガイダンスを回答する。AI開発者・提供者・利用者の各立場に対応。                                                                                                                                                   |
| [`nano-banana-image-gen`](./nano-banana-image-gen/SKILL.md)                           | Google Gemini で画像を生成し、タイムスタンプ付きPNGを `0_images/generated/` に出力する。Gemini APIキーが必要。                                                                                                                                                                                    |
| [`image-compressor`](./image-compressor/SKILL.md)                                     | 複数の画像を Pillow で一括圧縮・リサイズする。デフォルトは長辺1920pxで、元のファイル名を維持（同名が存在する場合は自動で連番付与）。出力フォーマット（JPG/PNG）を指定可能。                                                                                                                       |
| [`claude-md-manager`](./claude-md-manager/SKILL.md)                                   | `AGENTS.md` / `CLAUDE.md` をモジュール化して分割管理するスキル。本体は50行以下を推奨し、詳細ルールは `rules/` ディレクトリに切り出して参照リンクのみ残す。実体を `AGENTS.md` に置き `CLAUDE.md` はシンボリックリンクにすることで、Claude Code・Codex など複数AIエージェント間で指示を共通化する。 |
| [`design-md-generator`](./design-md-generator/SKILL.md)                               | URL・画像・テキスト要件から AI コーディングエージェント向けの `DESIGN.md`（getdesign.md / awesome-design-md 準拠の9セクション構成）を生成する。CSS解析・画像目視抽出・要件生成の3パターンに対応し、Claude Code / Cursor / Stitch / v0 にそのまま渡せる。                                          |

## セットアップ手順

### meti-ai-guideline

`references/` ディレクトリは著作権の都合上、このリポジトリには **含まれていません**。経産省サイトからPDFをダウンロードして、手動でセットアップする必要があります。

1. [経済産業省のページ](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/20260331_report.html) から以下のPDFをダウンロードします:
   - AI事業者ガイドライン（本編）
   - AI事業者ガイドライン活用の手引き
   - AI事業者ガイドライン チェックリスト 別添7

2. `pdftotext` でテキストを抽出し、以下のように配置します:

   ```text
   meti-ai-guideline/references/
   ├── common_guidelines.md
   ├── ai_developer.md
   ├── ai_provider.md
   ├── ai_user.md
   ├── checklist.md
   └── usage_guide.md
   ```

3. 各ファイルの先頭に出典情報を追記します:

   ```text
   出典: AI事業者ガイドライン（第X.X版）総務省・経済産業省, YYYY年MM月DD日
   ```

### nano-banana-image-gen

Google Gemini APIキーが必要です。プロジェクトルートの `.env` に以下を追加してください:

```text
GEMINI_API_KEY=your_api_key_here
GENERATED_IMAGE_OUTPUT_PATH=images/generated
```

依存パッケージのインストール:

```bash
pip install google-genai pillow python-dotenv
```

#### セキュリティ注意: `.env` をAIから保護する

Claude Code や Cursor などのAIコーディングツールは、`.env` ファイルを自動的に読み込み、APIキーを含む内容をLLMプロバイダーに送信してしまう可能性があります。これを防ぐため、`settings.json` に以下を追加してください:

```json
// .claude/settings.json
{
  "permissions": {
    "deny": ["Read(.env)", "Read(.env.*)"]
  }
}
```

また、シークレットを誤ってコミットしないように `.gitignore` にも追加しましょう:

```text
# .gitignore
.env
.env.*
!.env.sample
```

### claude-md-manager

`AGENTS.md` / `CLAUDE.md` の肥大化を防ぐため、本体ファイルは **50行以下を推奨**（公式は200行以下）しています。それを超える詳細なルールや手順は `rules/` ディレクトリ配下に個別のMarkdownファイルとして切り出し、本体には `-` パス`— 目的` の1行だけを残す運用です。

```text
.
├── AGENTS.md            # 50行以下。パスと目的の参照のみ
├── CLAUDE.md -> AGENTS.md  # シンボリックリンク
└── rules/
    ├── writing_rules.md
    ├── post_patterns.md
    └── ...
```

`CLAUDE.md` は `AGENTS.md` へのシンボリックリンクとして作成します。これにより Claude Code・Codex など複数のAIエージェントが同じ指示内容を共通で参照できます。

```bash
ln -s AGENTS.md CLAUDE.md
```

### image-compressor

任意設定です。出力先ディレクトリをカスタマイズしたい場合は、プロジェクトルートの `.env` に以下を追加してください（デフォルトは `0_images/compressed`）:

```text
IMAGE_COMPRESS_OUTPUT_PATH=0_images/compressed
```

依存パッケージのインストール:

```bash
pip install pillow python-dotenv
```

### design-md-generator

URL モード（CSS解析）を使う場合のみ依存パッケージが必要です。画像モード・テキスト要件モードは Claude 側で完結するため、追加インストール不要です。

```bash
pip install requests
```

使い方は3パターン:

- URL: 「<https://example.com/> を DESIGN.md にして」
- 画像: サムネ・スクショを添付して「これを DESIGN.md 化して」
- テキスト: 「クールでポップな LP 用の DESIGN.md を作って」

出力例は [`design-md-generator/references/examples/neverjp_inc.md`](./design-md-generator/references/examples/neverjp_inc.md) を参照してください。

## 参考リンク

- [https://agentskills.io](https://agentskills.io)
- [https://github.com/anthropics/skills](https://github.com/anthropics/skills)
- [https://github.com/vercel-labs/skills](https://github.com/vercel-labs/skills)
- [https://github.com/flutter/skills](https://github.com/flutter/skills)
- [https://skills.sh](https://skills.sh)

## コントリビュート

新しいスキルの提案・改善・修正のIssueやPull Requestを歓迎します。

## ライセンス

このリポジトリは [MIT License](./LICENSE) の下で公開されています。
