# ローカル環境構築手順

Next.js App Router + Better Auth + PostgreSQL を Docker を使って構築するための手順です。

## 推奨する進め方

いきなり全部 Docker に入れず、最初は `db` だけ Docker 化して、アプリはローカルで動かす方が切り分けしやすい。

```
1. Next.js プロジェクト作成
2. PostgreSQL を Docker Compose で起動
3. Better Auth を組み込む
4. Todo テーブルと CRUD を作る
5. アプリ本体を Docker 化する
```

---

## ステップ 1: Next.js プロジェクトを作成する

```bash
pnpm create next-app@latest . --ts --eslint --app --src-dir --import-alias "@/*"
```

---

## ステップ 2: PostgreSQL を Docker Compose で起動する

`docker-compose.yaml` を作成する:

```yaml
services:
  db:
    image: postgres:16
    container_name: todo-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: todo_app
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: todo_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

起動・確認・停止コマンド:

```bash
# 起動
docker compose up -d

# 確認
docker compose ps

# 停止・削除
docker compose down

# ボリューム削除（データリセット）
docker volume rm postgres_data
```

---

## ステップ 3: Better Auth と PostgreSQL クライアントを追加する

```bash
pnpm add better-auth pg
pnpm add @types/pg -D
```

---

## ステップ 4: 環境変数を設定する

`.env.local` を作成する（`env.sample` をコピーして編集）:

```env
DATABASE_URL=postgres://todo_user:todo_pass@localhost:5432/todo_app
BETTER_AUTH_SECRET=replace-with-a-long-random-string
BETTER_AUTH_URL=http://localhost:3000
INTERNAL_API_BASE_URL=http://localhost:3000
```

**注意点:**
- `DATABASE_URL` のホスト名はローカル実行時は `localhost`、Compose 内の app コンテナからは `db`
- `BETTER_AUTH_SECRET` は `openssl rand -base64 32` で生成した値を使う
- `INTERNAL_API_BASE_URL` は SSR で Next.js の API を呼ぶための絶対 URL（SSR はサーバー上で動くため相対 URL 不可）

---

## ステップ 5: DB 接続と Better Auth のサーバー設定を作る

`src/lib/db.ts`:

```ts
import { Pool } from "pg";

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});
```

`src/lib/auth.ts`:

```ts
import { betterAuth } from "better-auth";

import { pool } from "@/lib/db";

export const auth = betterAuth({
  database: pool,
  emailAndPassword: {
    enabled: true,
  },
});
```

`src/lib/session.ts`（サーバー側でセッションを取得するユーティリティ）:

```ts
import { headers } from "next/headers";

import { auth } from "@/lib/auth";

export async function getCurrentSession(requestHeaders?: Headers) {
  return auth.api.getSession({
    headers: requestHeaders ?? (await headers()),
  });
}
```

---

## ステップ 6: Better Auth の API ルートを追加する

`src/app/api/auth/[...all]/route.ts`:

```ts
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";

export const { GET, POST } = toNextJsHandler(auth);
```

---

## ステップ 7: Better Auth のテーブルを作成する

```bash
pnpm dlx @better-auth/cli migrate
```

実行前に PostgreSQL コンテナが起動していることを確認する。

テーブル確認:

```bash
docker compose exec db psql -U todo_user -d todo_app -c '\dt'
```

---

## ステップ 8: クライアント側の認証ユーティリティを作る

`src/lib/auth-client.ts`:

```ts
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient();
export const { signIn, signOut, signUp, useSession, getSession } = authClient;
```

---

## ステップ 9: Todo テーブルを追加する

`sql/init/001_create_todos.sql` を作成して管理する:

```sql
create extension if not exists pgcrypto;

create table todos (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  title text not null,
  completed boolean not null default false,
  created_at timestamptz not null default now()
);
```

実行:

```bash
docker compose exec -T db psql -U todo_user -d todo_app < sql/init/001_create_todos.sql
```

確認:

```bash
docker compose exec db psql -U todo_user -d todo_app -c '\dt'
docker compose exec db psql -U todo_user -d todo_app -c '\d todos'
```

---

## ステップ 10: ディレクトリ構成

```
src/
  app/
    sign-in/
    sign-up/
    todos/
    api/
      auth/[...all]/
      todos/
        [id]/
        _lib/
          todos.ts     # CRUD ロジック（requireCurrentUserId 等）
  components/
    auth-form.tsx
    sign-out-button.tsx
    todo-app.tsx
  lib/
    auth.ts
    auth-client.ts
    db.ts
    session.ts         # getCurrentSession ユーティリティ
sql/
  init/
    001_create_todos.sql
```

`src/app/api/todos/_lib/todos.ts` に CRUD ロジックをまとめる例:

```ts
import { pool } from "@/lib/db";
import { getCurrentSession } from "@/lib/session";

export async function requireCurrentUserId() {
  const session = await getCurrentSession();
  if (!session?.user) throw new Error("Unauthorized");
  return session.user.id;
}

export async function listTodosForCurrentUser() {
  const userId = await requireCurrentUserId();
  const { rows } = await pool.query(
    `select id, user_id, title, completed, created_at
     from todos where user_id = $1 order by created_at desc`,
    [userId],
  );
  return rows;
}
```

---

## ステップ 11: アプリを Docker 化する

認証と CRUD が動いてから Dockerfile を作る。

`next.config.ts`:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

`Dockerfile`:

```dockerfile
FROM node:22-alpine AS base
WORKDIR /app
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

---

## ステップ 12: 本番想定の Compose を作る

`docker-compose.yaml` に `app` サービスを追加する:

```yaml
services:
  app:
    build:
      context: .
    container_name: todo-app
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://todo_user:todo_pass@db:5432/todo_app
      BETTER_AUTH_SECRET: replace-with-a-long-random-string
      BETTER_AUTH_URL: http://localhost:3000
      INTERNAL_API_BASE_URL: http://app:3000
    ports:
      - "3000:3000"

  db:
    image: postgres:16
    container_name: todo-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: todo_app
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: todo_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todo_user -d todo_app"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
```

起動:

```bash
docker compose up --build
```

ブラウザで確認: `http://localhost:3000`

---

## 開発時のクイックスタート

```bash
docker compose up -d db              # PostgreSQL だけ起動
pnpm install
pnpm dlx @better-auth/cli migrate    # Better Auth テーブル作成
pnpm dev                             # 開発サーバー起動（package.json の dev スクリプトに TZ=Etc/UTC が設定済み）
```

app + db をまとめて起動する場合:

```bash
docker compose up --build
```

---

## 参考

- Better Auth Installation: https://better-auth.com/docs/installation
- Better Auth Next.js Integration: https://better-auth.com/docs/integrations/next
- Better Auth PostgreSQL: https://better-auth.com/docs/adapters/postgresql
- Next.js Docker Docs: https://nextjs.org/docs/app/building-your-application/deploying#docker-image
- Next.js `output: "standalone"`: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
