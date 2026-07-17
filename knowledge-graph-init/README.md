# knowledge-graph-init

アーキテクチャ知識グラフを memory MCP（[@modelcontextprotocol/server-memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)）で管理するためのスキル。スキル本体の手順は [SKILL.md](./SKILL.md) を参照。

このスキルを使うには、事前に server-memory の MCP サーバーをプロジェクトに追加しておく必要がある。

## server-memory MCP の追加手順（Claude Code）

### 1. `.mcp.json` に設定を追加

プロジェクトルートの `.mcp.json` に以下を記載する。

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/absolute/path/to/project/memory.jsonl"
      }
    }
  }
}
```

注意点:

- `env` は各サーバー定義（`memory`）の中に書く。`mcpServers` 直下に置くと無効になる。
- `MEMORY_FILE_PATH` は**絶対パス**で指定する。相対パスは npm パッケージのインストールディレクトリ基準で解決されるため、プロジェクト内のファイルを指せない。
- `MEMORY_FILE_PATH` を指定しない場合、パッケージ内部の `memory.json` に保存されてしまうため必ず指定する。
- このプロジェクトでは AGENTS.md の運用ルールに従い、保存先を `memory.jsonl` とする。

CLI で追加する場合は以下でも同じ設定になる。

```sh
claude mcp add memory --scope project \
  --env MEMORY_FILE_PATH=/absolute/path/to/project/memory.jsonl \
  -- npx -y @modelcontextprotocol/server-memory
```

#### 補足: local スコープで手早く試す場合

以下の形でも登録できる。

```sh
claude mcp add --transport stdio memory -- npx -y @modelcontextprotocol/server-memory
```

- `--transport stdio` は「ローカルでプロセスを起動し標準入出力で通信する」方式の指定。stdio はデフォルトなので省略可（リモートサーバー用の `--transport http` / `--transport sse` と区別するためのフラグ）。
- `--` 以降がサーバーの起動コマンドになる。
- ただし、この形はプロジェクト運用とは2点差分がある。
  - `--scope` 未指定のデフォルトは `local` で、設定は `~/.claude.json`（自分のユーザー設定）に保存され、リポジトリの `.mcp.json` には書かれない。チームで共有するには `--scope project` が必要。
  - `MEMORY_FILE_PATH` 未指定のため、保存先が npm パッケージ内部のデフォルト `memory.json` になり、`memory.jsonl` に保存されない。

自分のマシンだけでデフォルト保存先のまま動作を試す用途に向く。このプロジェクトの運用に組み込む場合は前述の `--scope project` + `--env` 付きの形を使うこと。

### 2. Claude Code で接続を確認

Claude Code を再起動（または新しいセッションを開始）すると、プロジェクトスコープの `.mcp.json` の初回読み込み時に承認プロンプトが表示されるので承認する。

`/mcp` コマンドで `memory` サーバーが connected になっていることを確認する。

### 3. 動作確認

セッション内で `read_graph` ツールを呼び出し、エラーなく応答が返る（初回は空のグラフ）ことを確認する。

## server-memory MCP の追加手順（Codex）

Codex CLI は MCP サーバーを `~/.codex/config.toml` で管理する。Claude Code の `.mcp.json` のようなプロジェクトスコープの設定はなく、**グローバル設定**になる点に注意。

### 1. `~/.codex/config.toml` に設定を追加

```toml
[mcp_servers.memory]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-memory"]

[mcp_servers.memory.env]
MEMORY_FILE_PATH = "/absolute/path/to/project/memory.jsonl"
```

CLI で追加する場合は以下でも同じ設定になる。

```sh
codex mcp add memory \
  --env MEMORY_FILE_PATH=/absolute/path/to/project/memory.jsonl \
  -- npx -y @modelcontextprotocol/server-memory
```

注意点:

- `MEMORY_FILE_PATH` は Claude Code と同様に**絶対パス**で指定し、Claude Code と同じ `memory.jsonl` を指せば両エージェントで同一の知識グラフを共有できる。
- 設定がグローバルのため、`MEMORY_FILE_PATH` は特定プロジェクトのパスに固定される。複数プロジェクトで使い分ける場合は、起動時に `codex -c 'mcp_servers.memory.env.MEMORY_FILE_PATH="/path/to/other/memory.jsonl"'` のように設定を上書きするか、プロジェクトごとに `config.toml` を書き換える。

### 2. 接続と動作を確認

以下で `memory` サーバーが登録されていることを確認する。

```sh
codex mcp list
codex mcp get memory
```

セッション内では `/mcp` コマンドで接続状態を確認し、`read_graph` ツールを呼び出してエラーなく応答が返る（初回は空のグラフ）ことを確認する。

## 提供されるツール

| ツール                                     | 用途                                 |
| ------------------------------------------ | ------------------------------------ |
| `create_entities` / `delete_entities`      | エンティティの登録・削除             |
| `create_relations` / `delete_relations`    | 依存関係の登録・削除                 |
| `add_observations` / `delete_observations` | エンティティへの補足情報の追加・削除 |
| `read_graph`                               | グラフ全体の取得                     |
| `search_nodes` / `open_nodes`              | エンティティの検索・参照             |

## セットアップ後

「知識グラフを初期化して」と依頼すると、[SKILL.md](./SKILL.md) の手順に従ってコードベースを調査し、モジュール構成と依存関係がグラフに登録される。
