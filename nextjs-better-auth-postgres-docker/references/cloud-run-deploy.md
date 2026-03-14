# Cloud Run デプロイ手順

Next.js アプリを Google Cloud Run へデプロイするための手順です。
データベースには Cloud SQL for PostgreSQL を使い、シークレットは Secret Manager で管理します。

## 前提

- アプリは `Dockerfile` でコンテナ化済み
- ローカルでは `docker compose` で動作確認済み
- `gcloud` CLI がインストール・認証済み
- PostgreSQL は Cloud Run に同梱せず、Cloud SQL for PostgreSQL を使う

## 全体の流れ

```
1. GCP プロジェクトと API を準備する
2. Cloud SQL for PostgreSQL を作成する
3. 本番用の環境変数を決める
4. Secret Manager に secret を登録する
5. Cloud Run のサービスアカウントに Secret Accessor 権限を付与する
6. Cloud SQL にマイグレーションを流す
7. GitHub リポジトリから継続デプロイする（コンソール）  ← 推奨
8. Artifact Registry + Docker コンテナでデプロイする（CLI） ← 手動運用向け
9. 動作確認する
```

---

## ステップ 1: GCP プロジェクトと API を準備する

変数を設定する（プロジェクトに合わせて変更する）:

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="your-service-name"
export REPOSITORY_NAME="cloud-run-apps"
export DB_INSTANCE_NAME="todo-postgres"
export DB_NAME="todo_app"
export DB_USER="todo_user"
export IMAGE_NAME="your-image-name"
```

プロジェクト設定:

```bash
gcloud config set project "$PROJECT_ID"
```

必要な API を有効化:

```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

## ステップ 2: Cloud SQL for PostgreSQL を作成する

インスタンス作成:

```bash
gcloud sql instances create "$DB_INSTANCE_NAME" \
  --database-version=POSTGRES_16 \
  --cpu=1 \
  --memory=3840MiB \
  --edition=ENTERPRISE \
  --region="$REGION"
```

DB 作成:

```bash
gcloud sql databases create "$DB_NAME" \
  --instance="$DB_INSTANCE_NAME"
```

ユーザー作成:

```bash
gcloud sql users create "$DB_USER" \
  --instance="$DB_INSTANCE_NAME" \
  --password="replace-with-a-strong-password"
```

Cloud SQL 接続名を取得（後で使う）:

```bash
gcloud sql instances describe "$DB_INSTANCE_NAME" \
  --format='value(connectionName)'
# 出力例: your-project-id:us-central1:todo-postgres
```

---

## ステップ 3: 本番用の環境変数を決める

必要な変数:

| 変数名                  | 説明                                              |
| ----------------------- | ------------------------------------------------- |
| `DATABASE_URL`          | Cloud SQL Unix socket 経由の接続文字列            |
| `BETTER_AUTH_SECRET`    | 認証シークレット（長いランダム文字列）            |
| `BETTER_AUTH_URL`       | Cloud Run の公開 URL                              |
| `INTERNAL_API_BASE_URL` | SSR 用の内部 URL（Cloud Run では公開 URL と同じ） |

`BETTER_AUTH_SECRET` 生成:

```bash
openssl rand -base64 32
```

`DATABASE_URL` の形式（Cloud SQL Unix socket 経由）:

```
postgres://DB_USER:DB_PASSWORD@/DB_NAME?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

`BETTER_AUTH_URL` と `INTERNAL_API_BASE_URL` は Cloud Run デプロイ後に確定するので、後で更新する。

---

## ステップ 4: Secret Manager に secret を登録する

`DATABASE_URL` を登録:

```bash
printf '%s' 'postgres://todo_user:YOUR_PASSWORD@/todo_app?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME' | \
  gcloud secrets create database-url --data-file=-
```

`BETTER_AUTH_SECRET` を登録:

```bash
printf '%s' 'your-generated-secret' | \
  gcloud secrets create better-auth-secret --data-file=-
```

既存の secret を更新する場合（新バージョン追加）:

```bash
printf '%s' 'new-value' | \
  gcloud secrets versions add database-url --data-file=-

printf '%s' 'new-value' | \
  gcloud secrets versions add better-auth-secret --data-file=-
```

---

## ステップ 5: Cloud Run のサービスアカウントに権限を付与する

Cloud Run が Secret Manager を読むには `roles/secretmanager.secretAccessor` が必要。

サービスアカウントを確認する（通常は `PROJECT_NUMBER-compute@developer.gserviceaccount.com`）:

```bash
gcloud iam service-accounts list
```

プロジェクト単位で権限付与:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

特定の secret にだけ付与する場合:

```bash
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding better-auth-secret \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## ステップ 6: Cloud SQL にマイグレーションを流す

Cloud SQL Auth Proxy を使ってローカルから流す方法が最もシンプル。

### 6-1. ADC を設定する

```bash
gcloud auth application-default login
```

### 6-2. Cloud SQL Auth Proxy を起動する（別ターミナルで）

参考: <https://docs.cloud.google.com/sql/docs/mysql/connect-auth-proxy>

```bash
./cloud-sql-proxy PROJECT_ID:REGION:INSTANCE_NAME --port 5432
```

成功すると:

```
Listening on 127.0.0.1:5432
The proxy has started successfully and is ready for new connections!
```

### 6-3. Better Auth のテーブルを作成する

```bash
DATABASE_URL='postgres://todo_user:YOUR_PASSWORD@127.0.0.1:5432/todo_app' pnpm dlx @better-auth/cli migrate
```

### 6-4. アプリ固有テーブルを作成する

```bash
PGPASSWORD='YOUR_PASSWORD' psql \
  "host=127.0.0.1 port=5432 dbname=todo_app user=todo_user sslmode=disable" \
  -f sql/init/001_create_todos.sql
```

### 6-5. テーブルを確認する

```bash
PGPASSWORD='YOUR_PASSWORD' psql \
  "host=127.0.0.1 port=5432 dbname=todo_app user=todo_user sslmode=disable" \
  -c '\dt'
```

---

## ステップ 7: GitHub リポジトリから継続デプロイする（コンソール）

GitHub リポジトリと Cloud Run を連携して、push のたびに自動デプロイする方法です。
Artifact Registry を手動で操作せずに済むため、CI/CD として運用する場合はこちらが便利です。

Cloud Run コンソールで以下を設定:

1. `Cloud Run` → `サービスを作成`
2. `ソース リポジトリから新しいリビジョンを継続的にデプロイする` を選ぶ
3. `GitHub` を選び、アカウントを認可する
4. 対象リポジトリとデプロイブランチを選ぶ
5. ビルドタイプ: `Dockerfile`
6. サービス名、リージョン、コンテナポート (`3000`) を設定
7. `未認証の呼び出しを許可` を必要に応じて有効化する
8. 追加設定:
   - Cloud SQL 接続: `PROJECT_ID:REGION:INSTANCE_NAME`
   - 環境変数: `BETTER_AUTH_URL`, `INTERNAL_API_BASE_URL`
   - Secret Manager: `DATABASE_URL=database-url:latest`, `BETTER_AUTH_SECRET=better-auth-secret:latest`

この方式では、GitHub へ push するたびに Cloud Build 経由で Cloud Run へ自動デプロイされます。

---

## ステップ 8: Artifact Registry + Docker コンテナでデプロイする

Artifact Registry にイメージを push して Cloud Run へデプロイする方法です。
GitHub 連携なしで手動でデプロイしたい場合や CLI から操作したい場合はこちらを使います。

### 8-1. Artifact Registry を作成する

```bash
gcloud artifacts repositories create "$REPOSITORY_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker repository for Cloud Run apps"
```

Docker 認証:

```bash
gcloud auth configure-docker "$REGION-docker.pkg.dev"
```

### 8-2. Docker イメージを build / push する

イメージ URI を設定:

```bash
export IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/$IMAGE_NAME:latest"
```

build:

```bash
docker build -t "$IMAGE_URI" .
```

push:

```bash
docker push "$IMAGE_URI"
```

### 8-3. Cloud Run にデプロイする

Cloud SQL 接続名を変数化:

```bash
export INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe "$DB_INSTANCE_NAME" --format='value(connectionName)')"
```

デプロイ:

```bash
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances="$INSTANCE_CONNECTION_NAME" \
  --set-secrets="DATABASE_URL=database-url:latest,BETTER_AUTH_SECRET=better-auth-secret:latest"
```

### 8-4. Cloud Run の URL を取得して env を更新する

サービス URL を取得:

```bash
export SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --format='value(status.url)')"
echo "$SERVICE_URL"
```

`BETTER_AUTH_URL` と `INTERNAL_API_BASE_URL` を更新:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region="$REGION" \
  --update-env-vars="BETTER_AUTH_URL=$SERVICE_URL,INTERNAL_API_BASE_URL=$SERVICE_URL"
```

### 8-5. コード変更後の更新デプロイ

```bash
docker build -t "$IMAGE_URI" .
docker push "$IMAGE_URI"
gcloud run deploy "$SERVICE_NAME" \
  --image="$IMAGE_URI" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated
```

---

## ステップ 9: 動作確認する

確認項目:

- `/sign-up` でユーザー登録できる
- `/sign-in` でログインできる
- `/todos` が表示できる
- Todo の追加・更新・削除ができる
- ログアウトできる

ログ確認:

```bash
gcloud run services logs read "$SERVICE_NAME" --region="$REGION"
```

---

## コスト管理: 一時停止・削除

### 一時停止（課金を抑えたい場合）

Cloud Run サービスを削除（アイドル時の課金は少ないが不要なら削除）:

```bash
gcloud run services delete "$SERVICE_NAME" --region="$REGION"
```

Cloud SQL を停止:

```bash
gcloud sql instances patch "$DB_INSTANCE_NAME" --activation-policy=NEVER
```

Cloud SQL を再開:

```bash
gcloud sql instances patch "$DB_INSTANCE_NAME" --activation-policy=ALWAYS
```

### 完全削除

```bash
# Cloud Run サービス削除
gcloud run services delete "$SERVICE_NAME" --region="$REGION"

# Cloud SQL インスタンス削除（データも消える）
gcloud sql instances delete "$DB_INSTANCE_NAME"

# Artifact Registry のイメージ削除
gcloud artifacts docker images delete "$IMAGE_URI" --delete-tags

# Secret 削除
gcloud secrets delete database-url
gcloud secrets delete better-auth-secret

# Artifact Registry リポジトリ削除
gcloud artifacts repositories delete "$REPOSITORY_NAME" --location="$REGION"
```

---

## よくあるエラーと対処

| エラー                                       | 原因                      | 対処                                  |
| -------------------------------------------- | ------------------------- | ------------------------------------- |
| `Permission denied on secret ...`            | Secret Accessor 権限なし  | ステップ 5 を実行する                 |
| `connect ENOENT /cloudsql/.../.s.PGSQL.5432` | Cloud SQL 接続未設定      | `--add-cloudsql-instances` を追加する |
| `BETTER_AUTH_URL` が不正                     | デプロイ前に URL が未確定 | ステップ 10 で URL 更新する           |

---

## 参考

- Cloud Run deploy: <https://cloud.google.com/run/docs/deploying>
- Cloud SQL から Cloud Run 接続: <https://docs.cloud.google.com/sql/docs/postgres/connect-run>
- Artifact Registry Docker: <https://docs.cloud.google.com/artifact-registry/docs/docker/store-docker-container-images>
- Cloud Run custom domains: <https://docs.cloud.google.com/run/docs/mapping-custom-domains>
