---
name: knowledge-graph-init
description: "アーキテクチャ知識グラフ(memory MCP / .claude/memory.jsonl)の初期作成。「知識グラフを初期化して」「memory グラフを作って」「アーキテクチャグラフを登録して」といった依頼、またはプロジェクト初期構築完了後の仕上げとして使用する。コードベースを調査し、モジュール構成と依存関係を entities / relations として登録する。"
license: MIT
author: shohei
version: 1.2.0
---

# knowledge-graph-init

AGENTS.md の運用ルールに従い、memory MCP（server-memory、保存先 `.claude/memory.jsonl`）へアーキテクチャ知識グラフを初期作成する。

## 手順

1. **既存確認**: `read_graph` で既存グラフを確認する。既にエンティティが存在する場合は上書きせず、不足分の追加に留める（必要ならユーザーに確認）。
2. **調査**: コードベースを読み、次の観点でモジュールを洗い出す。粒度はプロジェクトの構成に合わせる。
   - リポジトリ全体（モノレポなら 1 エンティティ。サブディレクトリ構成を observations に）
   - ビルド・パッケージ定義から分かる単位（Xcode ターゲット、npm workspace、Gradle モジュール等。使用フレームワーク・外部依存を observations に）
   - ソースディレクトリの主要モジュール（共通基盤・ドメイン層・機能単位など、プロジェクトのレイヤ構成に沿って）
   - エントリポイント（main 関数、App 構造体、サーバ起動スクリプト等）
   - インフラ・運用まわり（IaC、CI/CD、デプロイ設定、リリース自動化等）
3. **登録**: `create_entities` でエンティティを、`create_relations` で依存関係を登録する。
   - entityType の例: `monorepo`, `build target`, `entry point`, `core module`, `feature`, `infra`
   - relation の例: `depends on`, `contains`, `injects`, `configures`, `deploys`
   - observations には「何をするか」だけでなく、構成上の注意点（ビルド設定の例外、環境・モック切替の仕組み等）と調査日付を含める。
4. **検証**: `read_graph` で登録結果を確認し、主要モジュールの登録漏れがないかコードのディレクトリ一覧と突き合わせる。
5. **運用ルール追記**: `AGENTS.md`（または `CLAUDE.md`）に以下のセクションがなければ追加する。既に同等のルールがある場合は重複して追加しない。

   ```markdown
   ## アーキテクチャ知識グラフ

   モジュール構成・依存関係の知識グラフを memory MCP(server-memory、保存先 `.claude/memory.jsonl`)で管理している。

   - 実装・調査の前に `search_nodes` や `open_nodes` で関係するモジュールの entities / relations を参照し、既存の構成・依存関係に沿って作業すること(全体像が必要なら `read_graph`)。
   - モジュールの追加・削除や依存関係の変更を行ったら、`create_entities` / `create_relations` / `add_observations` 等でグラフも更新すること。
   ```

## 注意

- グラフはコードから導出できる「構成・依存関係」を記録する場所。タスク管理や TODO は書かない。
- 以後の実装・調査では `search_nodes` / `open_nodes` を先に参照し、モジュールの追加・変更時にグラフも更新する（AGENTS.md 参照）。
