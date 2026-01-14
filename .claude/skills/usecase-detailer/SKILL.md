---
name: usecase-detailer
description: ユースケースの詳細化スキル。漠然とした要求メモから作成されたユースケースを、API設計に十分な詳細レベルに引き上げる。CRUD操作の補完、エラーケースの定義、検証ルールの抽出を行う。Use when: (1) ユースケースが抽象的で検索条件・エラーケース・バリデーションが未定義, (2) データモデリング前にAPI設計の詳細を明確化したい, (3) Phase 0完了後にPhase 0.5として実行, (4) `/usecase-detailer` コマンドで明示的に実行
---

# Usecase Detailer Skill

このスキルは、漠然としたユースケースを**API設計に十分な詳細レベル**に引き上げる。

## 目的

Phase 0（要求メモ→ユースケース変換）で生成された抽象的なユースケースに対して：

1. **CRUD操作の補完** - Create/Read/Update/Delete操作の明確化
2. **エラーケースの定義** - バリデーションエラー、ビジネスルール違反、外部依存エラー
3. **検証ルールの抽出** - 必須項目、値の範囲・形式制約、一意性制約
4. **APIマッピング** - HTTPメソッド、エンドポイント、リクエスト/レスポンス形式

## ワークフロー

### Step 1: プロジェクト検証

必須ファイルの確認:
- `artifacts/{project}/usecase.md` - 入力ユースケース（必須）
- `artifacts/{project}/entities_classified.json` - エンティティ情報（オプション、利用可能なら活用）

プロジェクト名の取得:
- ユーザーから明示的に指定される場合: `/usecase-detailer {project-name}`
- または既存ユースケースファイルから自動検出

### Step 2: ユースケース分析

既存の `usecase.md` を読み込み、各ユースケースに対して:

1. **アクター抽出** - どの役割のユーザーが操作するか
2. **基本フロー識別** - 正常系の手順
3. **代替フロー識別** - 例外処理、エラーハンドリング
4. **エンティティ操作推測** - Create/Read/Update/Delete のどの操作が発生するか

### Step 3: 対話的詳細化

各ユースケースに対して、以下の質問を対話的に行う:

#### 3.1 CRUD操作の確認

```
このユースケースでは、どのエンティティを作成/更新しますか？

例:
- Create: PROJECT レコードを新規作成
- Read: CUSTOMER を検索・選択
- Update: PERSON_ASSIGN の AssignedDate を更新
- Delete: PROJECT を論理削除
```

#### 3.2 検索条件の確認

```
○○を選択する際、どのような検索条件が必要ですか？

例:
- 顧客名（部分一致）
- 業界ID（完全一致）
- 登録日範囲（From-To）
- ソート順（顧客名昇順、登録日降順）
```

参照: `references/crud-patterns.md` - 典型的なCRUD操作パターン

#### 3.3 バリデーションルールの確認

```
プロジェクト名に制約はありますか？

例:
- 必須項目: プロジェクト名、予定開始日、契約金額
- 文字数制限: 1-200文字
- 値の範囲: 契約金額は0以上
- 日付制約: 予定開始日は今日以降
```

参照: `references/validation-rules.md` - 一般的な検証ルール

#### 3.4 エラーケースの確認

```
登録が失敗するのはどのような場合ですか？

例:
- 400 Bad Request: バリデーションエラー（必須項目未入力、文字数超過）
- 404 Not Found: 参照先エンティティが存在しない（顧客ID不正）
- 409 Conflict: 重複（同一顧客×同一プロジェクト名）
- 403 Forbidden: 権限不足（他部署のプロジェクトを編集）
```

参照: `references/error-cases.md` - 標準的なエラーケース

#### 3.5 APIマッピングの提案

CRUD操作に基づいてHTTPメソッドとエンドポイントを提案:

| 操作 | HTTPメソッド | エンドポイント例 |
|-----|------------|----------------|
| Create | POST | `/api/projects` |
| Read (一覧) | GET | `/api/projects?customerID={id}&projectName={name}` |
| Read (詳細) | GET | `/api/projects/{id}` |
| Update | PUT/PATCH | `/api/projects/{id}` |
| Delete | DELETE | `/api/projects/{id}` |
| アクション | POST | `/api/projects/{id}/start` |

### Step 4: 詳細ユースケース生成

対話で収集した情報を元に `artifacts/{project}/usecase_detailed.md` を生成。

テンプレート: `templates/detailed-usecase-template.md`

出力形式:

```markdown
## UC-{ID}: {ユースケース名}

### 概要
- アクター: {ロール}
- 目的: {目的の説明}

### 前提条件
- {前提条件1}
- {前提条件2}

### 基本フロー
1. **{ステップ名}**
   - UI操作: {操作内容}
   - 検索条件: {検索条件}（部分一致/完全一致/範囲）
   - ソート: {ソート順}
   - バリデーション:
     - {項目名}: {制約内容}
   - エラーケース:
     - {エラー内容} → {HTTPステータス} {メッセージ}

2. **{次のステップ}**
   - CRUD操作: Create {エンティティ名}
   - 必須項目: {項目1}, {項目2}
   - 任意項目: {項目3}
   - 重複チェック: {条件}
   - レスポンス: {HTTPステータス} + {返却データ}

### 代替フロー
- {代替フロー1}
- {代替フロー2}

### 事後条件
- {事後条件1}
- {事後条件2}

### API マッピング

**エンドポイント**: {HTTPメソッド} {パス}

**Request**:
```json
{
  "field1": "value1",
  "field2": 123
}
```

**Success Response** ({HTTPステータス}):
```json
{
  "id": 1,
  "field1": "value1"
}
```

**Error Responses**:
- 400 Bad Request: バリデーションエラー
- 404 Not Found: {エンティティ}が存在しない
- 409 Conflict: 重複
```

### Step 5: 確認とフィードバック

生成した詳細ユースケースをユーザーに提示し、確認を取る:

```
以下の内容で詳細ユースケースを生成しました。

[詳細ユースケースのプレビュー]

このまま artifacts/{project}/usecase_detailed.md に保存してよろしいですか？
1. はい、保存する
2. いいえ、修正したい

番号を入力してください:
```

修正が必要な場合は Step 3 に戻り、特定のユースケースを再詳細化。

### Step 6: ファイル出力

承認後、`artifacts/{project}/usecase_detailed.md` に書き込み。

```
✅ 詳細ユースケースを生成しました: artifacts/{project}/usecase_detailed.md

次のステップ:
- Phase 1（エンティティ抽出）に進む
- または `/data-modeler-skill {project}` でデータモデリング開始
```

## 推奨される使い方

### パターン1: Phase 0完了後に自動実行（推奨）

```
要求メモ → Phase 0 → usecase.md 生成
    ↓
ユーザー確認: 「ユースケースをさらに詳細化しますか？」
    ↓
YES → /usecase-detailer 自動実行
```

### パターン2: 明示的なコマンド実行

```bash
# プロジェクト名を指定
/usecase-detailer project-record-system

# または現在のプロジェクトで実行
/usecase-detailer
```

### パターン3: 既存ユースケースの再詳細化

```
既に usecase.md が存在するプロジェクトで:
/usecase-detailer {project}

→ 既存の usecase_detailed.md を上書き確認後、再生成
```

## トラブルシューティング

### ユースケースが見つからない

```
[エラー] usecase.md が見つかりません: artifacts/{project}/usecase.md

解決策:
1. プロジェクト名が正しいか確認
2. Phase 0（要求メモ→ユースケース変換）を先に実行
3. 手動でユースケースファイルを作成
```

### エンティティ情報がない

`entities_classified.json` がない場合でも実行可能。ただし、CRUD操作の提案精度が低下する。

推奨: Phase 1-2を先に実行してからusecase-detailerを実行。

### 対話が長すぎる

デフォルト値の自動推測を使用:

```
全てのユースケースに対して標準的なバリデーションルールを適用しますか？
1. はい、デフォルト値を使用（推奨、高速）
2. いいえ、各ユースケースで個別に確認

番号を入力してください:
```

## 制限事項

1. **対話的入力が必要**: 完全自動ではなく、ユーザーの判断が必要
2. **日本語/英語混在**: ユースケースは日本語、APIマッピングは英語
3. **複雑なビジネスロジック**: 単純なCRUD以外の複雑なロジックは手動修正が必要

## 参照

- `references/crud-patterns.md` - CRUD操作の典型パターン
- `references/validation-rules.md` - 一般的な検証ルール
- `references/error-cases.md` - 標準的なエラーケース
- `templates/detailed-usecase-template.md` - 出力テンプレート

## 次のフェーズ

詳細ユースケース生成後:

1. **Phase 1: Entity Extraction** - エンティティ抽出
2. **Phase 2-6: Data Modeling** - データモデリング
3. **Phase 7: OpenAPI Generation** - OpenAPI仕様書生成（usecase_detailed.mdを活用）

---

**Note**: このスキルはPhase 0とPhase 1の間（Phase 0.5）に位置し、API設計とデータモデリングの橋渡しを行う。
