# CRUD Operation Patterns Reference

CRUD操作の典型的なパターンとAPIマッピングのリファレンス。

## Table of Contents

1. [Create Operations](#create-operations)
2. [Read Operations](#read-operations)
3. [Update Operations](#update-operations)
4. [Delete Operations](#delete-operations)
5. [Batch Operations](#batch-operations)
6. [Action Operations](#action-operations)

---

## Create Operations

### Pattern 1: Simple Resource Creation

**ユースケース例**: 新規顧客登録

**CRUD操作**:
```
Create: CUSTOMER
```

**APIマッピング**:
```
POST /api/customers
```

**Request Body**:
```json
{
  "customerName": "株式会社サンプル",
  "industryID": 1,
  "address": "東京都千代田区..."
}
```

**Success Response** (201 Created):
```json
{
  "customerID": 123,
  "customerName": "株式会社サンプル",
  "industryID": 1,
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**検証ルール**:
- customerName: 必須、1-100文字
- industryID: 必須、存在する業界IDへの参照
- address: 任意、1-500文字

### Pattern 2: Nested Resource Creation

**ユースケース例**: プロジェクト登録と同時にメンバーアサイン

**CRUD操作**:
```
Create: PROJECT
Create: PERSON_ASSIGN (複数)
```

**APIマッピング**:
```
POST /api/projects
```

**Request Body**:
```json
{
  "projectName": "新システム開発",
  "customerID": 123,
  "plannedStartDate": "2026-02-01",
  "members": [
    {"personID": 1, "role": "PM"},
    {"personID": 2, "role": "Engineer"}
  ]
}
```

**Success Response** (201 Created):
```json
{
  "projectID": 456,
  "projectName": "新システム開発",
  "members": [
    {"assignmentID": 1, "personID": 1, "role": "PM"},
    {"assignmentID": 2, "personID": 2, "role": "Engineer"}
  ],
  "createdAt": "2026-01-11T10:00:00Z"
}
```

---

## Read Operations

### Pattern 1: List with Pagination

**ユースケース例**: プロジェクト一覧表示（ページング付き）

**CRUD操作**:
```
Read: PROJECT (複数件)
```

**APIマッピング**:
```
GET /api/projects?limit=50&offset=0&sort=-createdAt
```

**Query Parameters**:
- `limit`: 取得件数（デフォルト: 50、最大: 500）
- `offset`: スキップ件数（デフォルト: 0）
- `sort`: ソート順（`-`プレフィックスで降順）

**Success Response** (200 OK):
```json
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "projects": [
    {"projectID": 1, "projectName": "..."},
    {"projectID": 2, "projectName": "..."}
  ]
}
```

### Pattern 2: Filtered List

**ユースケース例**: 顧客選択（検索条件付き）

**CRUD操作**:
```
Read: CUSTOMER (検索・フィルタ)
```

**APIマッピング**:
```
GET /api/customers?customerName=サンプル&industryID=1
```

**Query Parameters**:
- `customerName`: 顧客名（部分一致）
- `industryID`: 業界ID（完全一致）
- `createdFrom`: 登録日範囲開始（YYYY-MM-DD）
- `createdTo`: 登録日範囲終了（YYYY-MM-DD）

**Success Response** (200 OK):
```json
{
  "total": 5,
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

### Pattern 3: Single Resource Retrieval

**ユースケース例**: プロジェクト詳細表示

**CRUD操作**:
```
Read: PROJECT (単一件)
Read: CUSTOMER (関連)
Read: PERSON_ASSIGN (複数件、関連)
```

**APIマッピング**:
```
GET /api/projects/456
```

**Success Response** (200 OK):
```json
{
  "projectID": 456,
  "projectName": "新システム開発",
  "customer": {
    "customerID": 123,
    "customerName": "株式会社サンプル"
  },
  "members": [
    {"personID": 1, "personName": "山田太郎", "role": "PM"},
    {"personID": 2, "personName": "佐藤花子", "role": "Engineer"}
  ],
  "createdAt": "2026-01-11T10:00:00Z"
}
```

### Pattern 4: Aggregated Summary

**ユースケース例**: ダッシュボードのサマリー表示

**CRUD操作**:
```
Read: PROJECT (集計)
Read: PERSON_ASSIGN (集計)
```

**APIマッピング**:
```
GET /api/dashboard/summary
```

**Success Response** (200 OK):
```json
{
  "totalProjects": 150,
  "activeProjects": 45,
  "completedProjects": 100,
  "totalMembers": 50,
  "averageProjectDuration": 120
}
```

---

## Update Operations

### Pattern 1: Full Update (PUT)

**ユースケース例**: プロジェクト情報の完全更新

**CRUD操作**:
```
Update: PROJECT (全属性)
```

**APIマッピング**:
```
PUT /api/projects/456
```

**Request Body** (全フィールド必須):
```json
{
  "projectName": "新システム開発（改）",
  "customerID": 123,
  "plannedStartDate": "2026-02-01",
  "contractAmount": 10000000,
  "description": "..."
}
```

**Success Response** (200 OK):
```json
{
  "projectID": 456,
  "projectName": "新システム開発（改）",
  "updatedAt": "2026-01-11T11:00:00Z"
}
```

### Pattern 2: Partial Update (PATCH)

**ユースケース例**: プロジェクト名のみ変更

**CRUD操作**:
```
Update: PROJECT (特定属性のみ)
```

**APIマッピング**:
```
PATCH /api/projects/456
```

**Request Body** (変更したいフィールドのみ):
```json
{
  "projectName": "新システム開発（最終版）"
}
```

**Success Response** (200 OK):
```json
{
  "projectID": 456,
  "projectName": "新システム開発（最終版）",
  "updatedAt": "2026-01-11T11:30:00Z"
}
```

### Pattern 3: Status Transition

**ユースケース例**: プロジェクトの状態遷移（企画中→進行中）

**CRUD操作**:
```
Update: PROJECT (Status属性)
```

**APIマッピング**:
```
PATCH /api/projects/456/status
```

**Request Body**:
```json
{
  "status": "IN_PROGRESS",
  "startedAt": "2026-01-11T12:00:00Z"
}
```

**Success Response** (200 OK):
```json
{
  "projectID": 456,
  "status": "IN_PROGRESS",
  "previousStatus": "PLANNING",
  "updatedAt": "2026-01-11T12:00:00Z"
}
```

---

## Delete Operations

### Pattern 1: Soft Delete (Logical)

**ユースケース例**: プロジェクトの削除（論理削除）

**CRUD操作**:
```
Update: PROJECT (DeletedAt属性をセット)
```

**APIマッピング**:
```
DELETE /api/projects/456
```

**Success Response** (204 No Content):
```
(レスポンスボディなし)
```

**実装詳細**:
- 実際にはDELETEではなく、`DeletedAt`フィールドに現在時刻をセット
- 一覧取得時には`WHERE DeletedAt IS NULL`でフィルタ

### Pattern 2: Hard Delete (Physical)

**ユースケース例**: テストデータの完全削除（管理者のみ）

**CRUD操作**:
```
Delete: PROJECT (物理削除)
```

**APIマッピング**:
```
DELETE /api/admin/projects/456?permanent=true
```

**Success Response** (204 No Content):
```
(レスポンスボディなし)
```

**注意**:
- 外部キー制約を考慮（関連レコードの削除が必要）
- 管理者権限が必要
- 取り消し不可

### Pattern 3: Cascade Delete

**ユースケース例**: プロジェクト削除時、関連するアサインも削除

**CRUD操作**:
```
Delete: PROJECT
Delete: PERSON_ASSIGN (関連レコード、カスケード)
```

**APIマッピング**:
```
DELETE /api/projects/456?cascade=true
```

**Success Response** (200 OK):
```json
{
  "deletedProjectID": 456,
  "deletedAssignments": 5,
  "message": "プロジェクトと関連する5件のアサインを削除しました"
}
```

---

## Batch Operations

### Pattern 1: Bulk Create

**ユースケース例**: CSV一括登録

**CRUD操作**:
```
Create: CUSTOMER (複数件)
```

**APIマッピング**:
```
POST /api/customers/batch
```

**Request Body**:
```json
{
  "customers": [
    {"customerName": "A社", "industryID": 1},
    {"customerName": "B社", "industryID": 2},
    {"customerName": "C社", "industryID": 1}
  ]
}
```

**Success Response** (201 Created):
```json
{
  "created": 3,
  "failed": 0,
  "customers": [
    {"customerID": 1, "customerName": "A社"},
    {"customerID": 2, "customerName": "B社"},
    {"customerID": 3, "customerName": "C社"}
  ]
}
```

### Pattern 2: Bulk Update

**ユースケース例**: 複数プロジェクトの担当者一括変更

**CRUD操作**:
```
Update: PROJECT (複数件)
```

**APIマッピング**:
```
PATCH /api/projects/batch
```

**Request Body**:
```json
{
  "projectIDs": [1, 2, 3],
  "updates": {
    "managerID": 5
  }
}
```

**Success Response** (200 OK):
```json
{
  "updated": 3,
  "failed": 0
}
```

---

## Action Operations

イミュータブルデータモデルでは、状態変更を「イベント」として記録する。

### Pattern 1: Event Recording (POST)

**ユースケース例**: プロジェクト開始

**CRUD操作**:
```
Create: PROJECT_START (イベント)
```

**APIマッピング**:
```
POST /api/projects/456/start
```

**Request Body**:
```json
{
  "startDateTime": "2026-02-01T09:00:00Z",
  "registeredBy": 1
}
```

**Success Response** (201 Created):
```json
{
  "eventID": 789,
  "projectID": 456,
  "startDateTime": "2026-02-01T09:00:00Z",
  "createdAt": "2026-01-11T14:00:00Z"
}
```

**重要**: Idempotency-Key ヘッダーを必須とする（重複防止）

### Pattern 2: Member Assignment

**ユースケース例**: メンバーをプロジェクトにアサイン

**CRUD操作**:
```
Create: PERSON_ASSIGN (イベント)
```

**APIマッピング**:
```
POST /api/projects/456/members
```

**Request Body**:
```json
{
  "personID": 3,
  "role": "Engineer",
  "assignedDate": "2026-02-01"
}
```

**Success Response** (201 Created):
```json
{
  "assignmentID": 10,
  "projectID": 456,
  "personID": 3,
  "role": "Engineer",
  "assignedDate": "2026-02-01",
  "createdAt": "2026-01-11T14:30:00Z"
}
```

### Pattern 3: Member Replacement

**ユースケース例**: メンバー交代

**CRUD操作**:
```
Create: PERSON_REPLACE (イベント)
```

**APIマッピング**:
```
PUT /api/projects/456/members/10/replace
```

**Request Body**:
```json
{
  "newPersonID": 5,
  "replacedDate": "2026-03-01",
  "reason": "プロジェクト異動"
}
```

**Success Response** (201 Created):
```json
{
  "replacementID": 20,
  "projectID": 456,
  "oldPersonID": 3,
  "newPersonID": 5,
  "replacedDate": "2026-03-01",
  "createdAt": "2026-01-11T15:00:00Z"
}
```

---

## Best Practices

### 1. 命名規則

- リソース名: 複数形（`/api/projects`）
- アクション: 動詞（`/api/projects/{id}/start`）
- ネストは2階層まで（`/api/projects/{id}/members/{memberId}`）

### 2. HTTPステータスコード

| コード | 用途 |
|-------|------|
| 200 OK | 取得成功、更新成功 |
| 201 Created | 作成成功 |
| 204 No Content | 削除成功 |
| 400 Bad Request | バリデーションエラー |
| 404 Not Found | リソースが存在しない |
| 409 Conflict | 重複、競合 |
| 422 Unprocessable Entity | ビジネスルール違反 |

### 3. Idempotency

POST/PUT操作には `Idempotency-Key` ヘッダーを必須とする:

```
POST /api/projects/456/start
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### 4. フィルタリング

クエリパラメータでフィルタ:

- String属性: 部分一致 (`?projectName=サンプル`)
- ID属性: 完全一致 (`?customerID=123`)
- Date属性: 範囲 (`?createdFrom=2026-01-01&createdTo=2026-01-31`)

### 5. ソート

`sort` パラメータで指定、`-`プレフィックスで降順:

```
GET /api/projects?sort=-createdAt,projectName
```

### 6. ページネーション

`limit` と `offset` を使用:

```
GET /api/projects?limit=50&offset=100
```

レスポンスに総件数を含める:

```json
{
  "total": 500,
  "limit": 50,
  "offset": 100,
  "projects": [...]
}
```

---

## Anti-Patterns（避けるべきパターン）

### ❌ Avoid: RPC-Style Endpoints

```
POST /api/updateProjectName
POST /api/deleteCustomer
```

**代わりに REST を使用**:

```
PATCH /api/projects/{id}
DELETE /api/customers/{id}
```

### ❌ Avoid: Deep Nesting

```
GET /api/customers/123/projects/456/members/789/skills/1
```

**代わりに直接アクセス**:

```
GET /api/skills/1
```

### ❌ Avoid: Actions in Query Parameters

```
GET /api/projects?action=delete&id=456
```

**代わりに適切なHTTPメソッド**:

```
DELETE /api/projects/456
```

### ❌ Avoid: Mixed Concerns

```
POST /api/projectsAndMembers
{
  "project": {...},
  "members": [...]
}
```

**代わりに明確に分離**:

```
POST /api/projects
POST /api/projects/{id}/members
```
