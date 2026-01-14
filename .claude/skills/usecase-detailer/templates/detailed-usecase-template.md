# Detailed Use Cases

このファイルは、漠然としたユースケースをAPI設計に十分な詳細レベルに引き上げたものです。

**生成日**: {timestamp}
**プロジェクト**: {project-name}
**元ファイル**: artifacts/{project-name}/usecase.md

---

## UC-{ID}: {ユースケース名}

### 概要

- **アクター**: {ロール} (例: プロジェクトマネージャー、エンジニア)
- **目的**: {ユースケースの目的の簡潔な説明}
- **トリガー**: {このユースケースが開始される条件}

### 前提条件

1. {前提条件1} (例: ユーザーがログイン済み)
2. {前提条件2} (例: プロジェクトが企画中ステータス)
3. {前提条件3}

### 基本フロー

#### Step 1: {ステップ名} (例: 顧客選択)

**UI操作**:
- {操作内容の説明} (例: 顧客一覧から対象顧客を検索・選択)

**検索条件**:
| 項目 | 種別 | 説明 |
|-----|------|------|
| {項目名1} | 部分一致 | {説明} (例: 顧客名の部分一致検索) |
| {項目名2} | 完全一致 | {説明} (例: 業界IDでフィルタ) |
| {項目名3} | 範囲 | {説明} (例: 登録日の範囲指定) |

**ソート**:
- デフォルト: {ソート項目} {昇順/降順} (例: 顧客名昇順)
- 変更可能: {ソート項目リスト}

**バリデーション**:
- {検証ルール1} (例: 検索条件は少なくとも1つ必須)
- {検証ルール2}

**エラーケース**:
| エラー内容 | HTTPステータス | メッセージ |
|----------|--------------|-----------|
| {エラー1} | 404 Not Found | {メッセージ} (例: 該当する顧客が見つかりません) |
| {エラー2} | 400 Bad Request | {メッセージ} |

**CRUD操作**:
```
Read: {エンティティ名} (検索・フィルタ)
例: Read: CUSTOMER (customerName, industryID でフィルタ)
```

---

#### Step 2: {ステップ名} (例: プロジェクト情報入力)

**UI操作**:
- {操作内容の説明} (例: プロジェクト情報をフォームに入力)

**入力項目**:
| 項目名（日本語） | 項目名（英語） | 必須 | 型 | 制約 | デフォルト値 |
|---------------|--------------|-----|---|------|----------|
| {項目1} | {field1} | ✓ | VARCHAR | 1-200文字 | - |
| {項目2} | {field2} | ✓ | INT | 0以上 | - |
| {項目3} | {field3} | | DATE | 今日以降 | 今日 |
| {項目4} | {field4} | | TEXT | 0-500文字 | - |

**バリデーション**:
- **必須項目**: {項目リスト} (例: projectName, plannedStartDate, contractAmount)
- **文字数制限**: {項目名}: {範囲} (例: projectName: 1-200文字)
- **値の範囲**: {項目名}: {範囲} (例: contractAmount: 0以上)
- **日付制約**: {項目名}: {制約} (例: plannedStartDate: 今日以降)
- **条件付き必須**: {条件} の場合、{項目名} が必須

**エラーケース**:
| エラー内容 | HTTPステータス | メッセージ | フィールド |
|----------|--------------|-----------|----------|
| 必須項目欠損 | 400 Bad Request | {項目名}は必須です | {fieldName} |
| 文字数超過 | 400 Bad Request | 1-200文字で入力してください | projectName |
| 値の範囲外 | 400 Bad Request | 契約金額は0以上である必要があります | contractAmount |
| 日付制約違反 | 400 Bad Request | 予定開始日は今日以降である必要があります | plannedStartDate |

**CRUD操作**:
```
(まだ保存しない - Step 3で保存)
```

---

#### Step 3: {ステップ名} (例: 登録実行)

**UI操作**:
- {操作内容の説明} (例: 「登録」ボタンをクリック)

**CRUD操作**:
```
Create: {エンティティ名}
例: Create: PROJECT
```

**重複チェック**:
- **条件**: {重複チェック条件} (例: 同一顧客×同一プロジェクト名)
- **エラー**: 409 Conflict

**トランザクション**:
```
BEGIN TRANSACTION
1. Create PROJECT
2. [関連操作があれば記述]
COMMIT
```

**成功レスポンス**:
- **HTTPステータス**: 201 Created
- **返却データ**: {返却内容} (例: 生成されたProjectID、createdAt)

**エラーケース**:
| エラー内容 | HTTPステータス | メッセージ |
|----------|--------------|-----------|
| 顧客が存在しない | 404 Not Found | 指定された顧客が見つかりません |
| 重複 | 409 Conflict | 同じ顧客・プロジェクト名が既に存在します |
| トランザクションエラー | 500 Internal Server Error | サーバー内部エラーが発生しました |

---

### 代替フロー

#### Alt-1: {代替フロー名} (例: 顧客が見つからない場合)

**条件**: {代替フローに入る条件}

**処理**:
1. {ステップ1}
2. {ステップ2}

**復帰**: {復帰先ステップ} (例: Step 1に戻る、または終了)

---

#### Alt-2: {代替フロー名}

**条件**: {代替フローに入る条件}

**処理**:
1. {ステップ1}
2. {ステップ2}

---

### 例外フロー

#### Exc-1: {例外フロー名} (例: ネットワークエラー)

**条件**: {例外条件}

**処理**:
- {エラーハンドリング処理}
- {ユーザーへの通知内容}

---

### 事後条件

1. {事後条件1} (例: PROJECTレコードが作成される)
2. {事後条件2} (例: ステータスが「企画中」になる)
3. {事後条件3}

---

### API マッピング

#### Endpoint 1: {操作名}

**Method & Path**:
```
{HTTPメソッド} {エンドポイント}
例: GET /api/customers?customerName=サンプル&industryID=1
```

**Description**: {エンドポイントの説明}

**Query Parameters**:
| パラメータ名 | 型 | 必須 | 説明 | 例 |
|-----------|---|-----|------|---|
| {param1} | string | | {説明} | "サンプル" |
| {param2} | integer | | {説明} | 1 |
| limit | integer | | 取得件数 | 50 |
| offset | integer | | スキップ件数 | 0 |
| sort | string | | ソート順 | "customerName" |

**Success Response** (200 OK):
```json
{
  "total": 10,
  "limit": 50,
  "offset": 0,
  "customers": [
    {
      "customerID": 123,
      "customerName": "株式会社サンプル",
      "industryID": 1,
      "industryName": "製造業"
    }
  ]
}
```

**Error Responses**:
- **400 Bad Request**: バリデーションエラー
- **404 Not Found**: 該当データなし

---

#### Endpoint 2: {操作名}

**Method & Path**:
```
{HTTPメソッド} {エンドポイント}
例: POST /api/projects
```

**Description**: {エンドポイントの説明}

**Headers**:
```
Content-Type: application/json
Authorization: Bearer {token}
Idempotency-Key: {uuid} (POST/PUT操作の場合)
```

**Request Body**:
```json
{
  "projectName": "新システム開発",
  "customerID": 123,
  "plannedStartDate": "2026-02-01",
  "contractAmount": 10000000,
  "description": "新規システムの開発プロジェクト",
  "developmentTypeID": 1
}
```

**Required Fields**:
- projectName
- customerID
- plannedStartDate
- contractAmount

**Success Response** (201 Created):
```json
{
  "projectID": 456,
  "projectName": "新システム開発",
  "customerID": 123,
  "plannedStartDate": "2026-02-01",
  "contractAmount": 10000000,
  "status": "PLANNING",
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**Error Responses**:
- **400 Bad Request**: バリデーションエラー
  ```json
  {
    "type": "https://api.example.com/errors/validation-error",
    "title": "Validation Error",
    "status": 400,
    "errors": [
      {
        "field": "projectName",
        "message": "1-200文字で入力してください",
        "value": ""
      }
    ]
  }
  ```

- **404 Not Found**: 顧客が存在しない
  ```json
  {
    "type": "https://api.example.com/errors/not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "指定された顧客が見つかりません",
    "field": "customerID",
    "value": 123
  }
  ```

- **409 Conflict**: 重複
  ```json
  {
    "type": "https://api.example.com/errors/conflict",
    "title": "Resource Conflict",
    "status": 409,
    "detail": "この顧客には既に同名のプロジェクトが存在します",
    "fields": ["customerID", "projectName"],
    "values": [123, "新システム開発"]
  }
  ```

---

### パフォーマンス要件

- **検索レスポンス**: {要件} (例: 1秒以内)
- **登録処理**: {要件} (例: 2秒以内)
- **同時実行**: {要件} (例: 100リクエスト/秒)

---

### セキュリティ考慮事項

- **認証**: {認証方式} (例: JWT Bearer Token)
- **認可**: {認可要件} (例: プロジェクトマネージャーロールが必要)
- **入力サニタイゼーション**: {対策} (例: XSS対策、SQLインジェクション対策)
- **レート制限**: {制限} (例: 100リクエスト/分)

---

### テストケース

#### TC-1: {テストケース名} (例: 正常系 - プロジェクト登録成功)

**前提条件**:
- {前提条件}

**入力データ**:
```json
{
  "projectName": "テストプロジェクト",
  "customerID": 123
}
```

**期待結果**:
- HTTPステータス: 201 Created
- projectID が生成される
- createdAt が現在時刻

---

#### TC-2: {テストケース名} (例: 異常系 - 必須項目欠損)

**前提条件**:
- {前提条件}

**入力データ**:
```json
{
  "customerID": 123
}
```

**期待結果**:
- HTTPステータス: 400 Bad Request
- エラーメッセージ: "プロジェクト名は必須です"

---

### 備考

- {追加の説明や注意事項}
- {関連するユースケースへの参照}
- {将来の拡張案}

---

## テンプレートの使い方

### 必須セクション

以下のセクションは必ず含めること:

1. **概要** - アクター、目的、トリガー
2. **基本フロー** - 各ステップの詳細
3. **事後条件** - ユースケース完了後の状態
4. **API マッピング** - エンドポイント定義

### 任意セクション

以下は必要に応じて含める:

- 代替フロー
- 例外フロー
- パフォーマンス要件
- セキュリティ考慮事項
- テストケース

### プレースホルダー

`{...}` で囲まれた部分は実際の値に置き換えること。

---

*このテンプレートは usecase-detailer スキルによって生成されました*
