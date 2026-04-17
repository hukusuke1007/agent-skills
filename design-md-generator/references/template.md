# Design System: {{ProjectName}}
**Source:** {{SourceURLOrInputType}}

> AIコーディングエージェントが {{ProjectName}} と一貫したUIを生成するためのデザインシステム仕様書。
> getdesign.md / awesome-design-md 準拠の9セクション構成。

---

## 1. Visual Theme & Atmosphere

(Description of the mood, density, and aesthetic philosophy.)

**{{Theme一行ステートメント}}**

- {{特徴1: 背景色とテキストの関係}}
- {{特徴2: 主役にする要素（写真・タイポ等）}}
- {{特徴3: 角丸・形状の方針}}
- {{特徴4: ブランドメッセージ・トーン（Brand Voiceもここに集約）}}
- {{特徴5: グラデーションや装飾の方針}}

**業界ポジション**: {{業界・ターゲット顧客層}}

---

## 2. Color Palette & Roles

(List colors by Descriptive Name + Hex Code + Functional Role.)

### Primary Brand

| 名前 | HEX | Role |
|---|---|---|
| {{Primary Name}} | `{{#xxxxxx}}` | {{用途・役割}} |
| {{Secondary Name}} | `{{#xxxxxx}}` | {{用途・役割}} |

### Surface & Neutrals

| 名前 | HEX | Role |
|---|---|---|
| {{Background}} | `{{#xxxxxx}}` | {{用途}} |
| {{Surface}} | `{{#xxxxxx}}` | {{用途}} |
| {{Border}} | `{{#xxxxxx}}` | {{用途}} |
| {{Muted}} | `{{#xxxxxx}}` | {{用途}} |

### Text

| 名前 | HEX | Role |
|---|---|---|
| {{Primary Text}} | `{{#xxxxxx}}` | {{用途}} |
| {{Secondary Text}} | `{{#xxxxxx}}` | {{用途}} |

### Accent

| 名前 | HEX | Role |
|---|---|---|
| {{Accent1}} | `{{#xxxxxx}}` | {{ポイント使い限定の用途}} |
| {{Accent2}} | `{{#xxxxxx}}` | {{用途}} |

---

## 3. Typography Rules

(Description of font family, weight usage for headers vs. body, and letter-spacing character.)

### Font Family

```css
/* メイン */
font-family: {{PrimaryFontStack}};

/* 和文（必要な場合） */
font-family: {{JapaneseFontStack}};
```

- **{{PrimaryFontName}}** … {{用途}}
- **{{JapaneseFontName}}** … {{用途}}

### Hierarchy

| Role | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|
| Display / Hero | `{{size}}` | {{weight}} | {{lh}} | {{ls}} |
| Section Heading (H2) | `{{size}}` | {{weight}} | {{lh}} | {{ls}} |
| Sub Heading (H3) | `{{size}}` | {{weight}} | {{lh}} | {{ls}} |
| Body | `{{size}}` | {{weight}} | {{lh}} | {{ls}} |
| Caption / Meta | `{{size}}` | {{weight}} | {{lh}} | {{ls}} |

### Principles

- {{原則1: ウェイトの使い方}}
- {{原則2: letter-spacing の方針}}
- {{原則3: 和欧混植の扱い（必要なら）}}

---

## 4. Component Stylings

(Buttons, cards, inputs, navigation, with states.)

### Buttons

**Primary**
- 背景: `{{color}}`
- 文字: `{{color}}`
- 角丸: `{{radius}}`
- パディング: `{{padding}}`
- ホバー: {{behavior}}
- フォーカス: {{behavior}}

**Secondary**
- 背景: `{{color}}`
- 文字: `{{color}}`
- ボーダー: `{{border}}`
- 角丸: `{{radius}}`

### Cards / Containers

- 背景: `{{color}}`
- 角丸: `{{radius}}`
- 影: `{{box-shadow}}`
- パディング: `{{padding}}`
- ホバー時: {{behavior}}

### Inputs / Forms

- 背景: `{{color}}`
- ボーダー: `{{border}}`
- 角丸: `{{radius}}`
- フォーカス: {{behavior}}

### Navigation

- レイアウト: {{構造}}
- 項目例: {{メニュー項目}}
- モバイル: {{挙動}}
- アクティブ表示: {{behavior}}

### Image / Iconography

- アイコンの方針: {{線画 / フィル / 太さ}}
- 写真の扱い: {{雰囲気 / 加工 / アスペクト比}}
- 装飾要素の方針: {{有無・程度}}

### Microinteractions

```css
transition: {{value}}; /* 標準ホバー */
transition: {{value}}; /* フェード */
```

- {{動作1: ホバー時の挙動}}
- {{動作2: スクロール連動}}
- {{動作3: アニメーション名と用途}}

---

## 5. Layout Principles

(Description of whitespace strategy, margins, and grid alignment.)

### Spacing System

- 基本単位: `{{base unit}}`
- スケール: {{2/4/8/16/24/32...}}
- セクション間: {{px}}（PC）/ {{px}}（SP）
- カード間: {{px}} のグリッドギャップ

### Container

- メイン最大幅: `{{max-width}}`
- 内側パディング: `{{padding}}`

### Grid

- {{レイアウトパターン: カラム数・崩し方}}

### Whitespace Philosophy

- {{余白の哲学: 詰める/開ける/写真ファースト等}}

---

## 6. Depth & Elevation

(Shadow system, surface hierarchy.)

### Shadow Scale

| Level | 値 | 用途 |
|---|---|---|
| Flat | `none` | テキストブロック、背景 |
| Card | `{{box-shadow}}` | カード・パネル |
| Hover | `{{box-shadow}}` | ホバー強調 |
| Modal / Featured | `{{box-shadow}}` | モーダル・最前面 |

**Shadow Philosophy**: {{シャドウの方針一行}}

### Border Radius Scale

| 値 | 用途 |
|---|---|
| `{{radius}}` | {{用途}} |
| `{{radius}}` | {{用途}} |
| `{{radius}}` | {{用途}} |

→ {{角丸の方針一行}}

---

## 7. Do's and Don'ts

(Design guardrails and anti-patterns.)

### ✅ Do

- {{推奨1}}
- {{推奨2}}
- {{推奨3}}
- {{推奨4}}

### ❌ Don't

- {{禁止1}}
- {{禁止2}}
- {{禁止3}}
- {{禁止4}}

---

## 8. Responsive Behavior

(Breakpoints, touch targets, collapsing strategy.)

### Breakpoints

| Name | Width | Key Changes |
|---|---|---|
| Mobile | {{px}} | {{挙動}} |
| Tablet | {{px}} | {{挙動}} |
| Desktop | {{px}} | {{挙動}} |
| Wide | {{px}} | {{挙動}} |

### Touch Targets

- {{タップ領域の最小サイズ}}
- {{モバイル時の操作性ルール}}

### Collapsing Strategy

- {{グリッド縮約: 4 → 2 → 1}}
- {{ナビ縮約: ハンバーガー化等}}
- {{画像の挙動}}

---

## 9. Agent Prompt Guide

(Quick color reference, ready-to-use prompts.)

### Quick Reference

```text
背景: {{color}}
本文: {{color}} / 補助 {{color}}
ブランドアクセント: {{color}}
フォント: {{font}}
ベースサイズ: {{size}}
セクション余白: {{spacing}}
カード角丸: {{radius}}
カード影: {{shadow}}
```

### Component Prompts (例)

- **ボタン作成**: "Primary ボタンを作って。背景 `{{color}}`、文字 `{{color}}`、パディング `{{padding}}`、角丸 `{{radius}}`、フォント {{font}}、ホバーで {{behavior}}"
- **カード作成**: "カードを作って。背景 `{{color}}`、角丸 `{{radius}}`、影 `{{shadow}}`、パディング `{{padding}}`"
- **ヒーロー作成**: "{{ヒーロー指針一行}}"

### Iteration Guide

1. {{使い始めの一手}}
2. {{2手目: 重要なルール}}
3. {{3手目: アクセントの使い方}}
4. {{4手目: 余白・角丸の確認}}

---

**Source**: {{SourceURLOrInputType}} ({{抽出方法}}, {{日付}})
**Format**: getdesign.md / awesome-design-md 準拠の9セクション構成
**Generated for**: AIコーディングエージェント（Claude Code / Cursor / Stitch / v0 等）
**Maintainer**: {{Owner}}
