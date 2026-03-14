---
name: nextjs-better-auth-postgres-docker
description: Next.js + Better Auth + PostgreSQL を Docker で構築し、Cloud Run へデプロイするスキル。ローカル開発環境のセットアップから Docker Compose、Dockerfile 作成、Cloud Run + Cloud SQL + Secret Manager を使った本番デプロイまでをカバーする。「Next.js と Better Auth でアプリを作りたい」「Docker で PostgreSQL を使いたい」「Docker で構築したい」「Docker Compose を使いたい」「アプリを Docker 化したい」「Dockerfile を書きたい」「Cloud Run にデプロイしたい」「Cloud SQL や Secret Manager を使いたい」ときに使う。
license: "MIT"
metadata:
  author: "shohei"
  version: "1.0.0"
---

# Next.js + Better Auth + PostgreSQL + Docker

Next.js App Router + Better Auth + PostgreSQL を Docker で構築し、Cloud Run へデプロイするためのスキルです。

## 対象スタック

- **フレームワーク**: Next.js (App Router, TypeScript)
- **認証**: Better Auth
- **DB**: PostgreSQL 16
- **パッケージマネージャ**: pnpm
- **インフラ**: Docker / Docker Compose、Google Cloud Run、Cloud SQL、Secret Manager

## 参照ドキュメント

詳細な手順は以下の reference ファイルに分けています。

| ファイル                         | 内容                                                            |
| -------------------------------- | --------------------------------------------------------------- |
| `references/local-setup.md`      | ローカル開発環境の構築（Docker Compose + アプリ Docker 化まで） |
| `references/cloud-run-deploy.md` | Cloud Run へのデプロイ（Cloud SQL + Secret Manager 使用）       |

## どちらを参照するか

- **ローカル環境を構築したい** → `references/local-setup.md` を読む
- **Cloud Run にデプロイしたい** → `references/cloud-run-deploy.md` を読む
- **両方やりたい** → `local-setup.md` を完了してから `cloud-run-deploy.md` に進む

## 環境変数の切り替えまとめ

実行環境によって値が変わる変数を把握しておく。

| 変数名                  | ローカル直実行          | Docker Compose (app コンテナ) | Cloud Run              |
| ----------------------- | ----------------------- | ----------------------------- | ---------------------- |
| `DATABASE_URL` のホスト | `localhost`             | `db`                          | Cloud SQL Unix socket  |
| `BETTER_AUTH_URL`       | `http://localhost:3000` | `http://localhost:3000`       | Cloud Run サービス URL |
| `INTERNAL_API_BASE_URL` | `http://localhost:3000` | `http://app:3000`             | Cloud Run サービス URL |
