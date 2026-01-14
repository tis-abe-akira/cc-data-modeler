# Error Cases Reference

API設計における標準的なエラーケースとレスポンス形式のリファレンス。

## Table of Contents

1. [HTTP Status Codes](#http-status-codes)
2. [RFC 7807 Problem Details](#rfc-7807-problem-details)
3. [Client Errors (4xx)](#client-errors-4xx)
4. [Server Errors (5xx)](#server-errors-5xx)
5. [Business Rule Errors](#business-rule-errors)
6. [External Dependency Errors](#external-dependency-errors)

---

## HTTP Status Codes

### Success Codes (2xx)

| コード | 名称 | 用途 |
|-------|------|------|
| 200 | OK | 取得成功、更新成功 |
| 201 | Created | 作成成功 |
| 204 | No Content | 削除成功（レスポンスボディなし） |

### Client Error Codes (4xx)

| コード | 名称 | 用途 |
|-------|------|------|
| 400 | Bad Request | バリデーションエラー、リクエスト形式不正 |
| 401 | Unauthorized | 認証エラー（ログイン必須） |
| 403 | Forbidden | 権限エラー（アクセス不可） |
| 404 | Not Found | リソースが存在しない |
| 409 | Conflict | 重複、競合状態 |
| 422 | Unprocessable Entity | ビジネスルール違反 |
| 429 | Too Many Requests | レート制限超過 |

### Server Error Codes (5xx)

| コード | 名称 | 用途 |
|-------|------|------|
| 500 | Internal Server Error | サーバー内部エラー |
| 502 | Bad Gateway | 外部APIエラー |
| 503 | Service Unavailable | サービス一時停止 |
| 504 | Gateway Timeout | 外部APIタイムアウト |

---

## RFC 7807 Problem Details

すべてのエラーレスポンスは RFC 7807 形式を使用。

### 基本構造

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "プロジェクト名は必須です",
  "instance": "/api/projects",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### 必須フィールド

| フィールド | 型 | 説明 |
|----------|---|------|
| type | string (URI) | エラー種別を示す一意のURI |
| title | string | エラーの概要（人間が読める） |
| status | integer | HTTPステータスコード |

### 任意フィールド

| フィールド | 型 | 説明 |
|----------|---|------|
| detail | string | エラーの詳細説明 |
| instance | string (URI) | エラーが発生したエンドポイント |
| timestamp | string (ISO 8601) | エラー発生日時 |
| errors | array | 詳細なバリデーションエラー（複数項目） |

---

## Client Errors (4xx)

### 400 Bad Request

#### Use Case 1: 必須項目欠損

**シナリオ**: プロジェクト名を入力せずに登録

**Request**:
```
POST /api/projects
Content-Type: application/json

{
  "customerID": 123,
  "contractAmount": 1000000
}
```

**Response** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "必須項目が不足しています",
  "instance": "/api/projects",
  "timestamp": "2026-01-11T10:00:00Z",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は必須です",
      "value": null
    },
    {
      "field": "plannedStartDate",
      "message": "予定開始日は必須です",
      "value": null
    }
  ]
}
```

#### Use Case 2: 型不正

**シナリオ**: 契約金額に文字列を指定

**Request**:
```
POST /api/projects
Content-Type: application/json

{
  "projectName": "新システム開発",
  "contractAmount": "百万円"
}
```

**Response** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "データ型が不正です",
  "errors": [
    {
      "field": "contractAmount",
      "message": "契約金額は数値で指定してください",
      "value": "百万円",
      "expectedType": "number"
    }
  ]
}
```

#### Use Case 3: フォーマット不正

**シナリオ**: 日付形式エラー

**Request**:
```
POST /api/projects
Content-Type: application/json

{
  "projectName": "新システム開発",
  "plannedStartDate": "2026/01/11"
}
```

**Response** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "日付形式が不正です",
  "errors": [
    {
      "field": "plannedStartDate",
      "message": "日付はYYYY-MM-DD形式で指定してください",
      "value": "2026/01/11",
      "expectedFormat": "YYYY-MM-DD"
    }
  ]
}
```

#### Use Case 4: 範囲外の値

**シナリオ**: 進捗率が100を超える

**Request**:
```
PATCH /api/projects/456
Content-Type: application/json

{
  "progressRate": 150
}
```

**Response** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "値が許容範囲外です",
  "errors": [
    {
      "field": "progressRate",
      "message": "進捗率は0-100の範囲で指定してください",
      "value": 150,
      "min": 0,
      "max": 100
    }
  ]
}
```

### 401 Unauthorized

#### Use Case 1: 認証トークン未提供

**シナリオ**: Authorization ヘッダーなしでAPIリクエスト

**Request**:
```
GET /api/projects
```

**Response** (401 Unauthorized):
```json
{
  "type": "https://api.example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "認証が必要です。Authorization ヘッダーを含めてください",
  "instance": "/api/projects"
}
```

#### Use Case 2: 認証トークン無効

**シナリオ**: 期限切れトークン

**Request**:
```
GET /api/projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (401 Unauthorized):
```json
{
  "type": "https://api.example.com/errors/token-expired",
  "title": "Token Expired",
  "status": 401,
  "detail": "認証トークンの有効期限が切れています",
  "expiredAt": "2026-01-10T12:00:00Z"
}
```

### 403 Forbidden

#### Use Case 1: 権限不足

**シナリオ**: エンジニアがプロジェクトを削除しようとする（PM権限が必要）

**Request**:
```
DELETE /api/projects/456
Authorization: Bearer <engineer-token>
```

**Response** (403 Forbidden):
```json
{
  "type": "https://api.example.com/errors/insufficient-permissions",
  "title": "Insufficient Permissions",
  "status": 403,
  "detail": "この操作にはプロジェクトマネージャー権限が必要です",
  "instance": "/api/projects/456",
  "requiredRole": "PM",
  "userRole": "Engineer"
}
```

#### Use Case 2: 他部署のリソースにアクセス

**シナリオ**: 営業部のユーザーが開発部のプロジェクトを参照

**Request**:
```
GET /api/projects/456
Authorization: Bearer <sales-user-token>
```

**Response** (403 Forbidden):
```json
{
  "type": "https://api.example.com/errors/access-denied",
  "title": "Access Denied",
  "status": 403,
  "detail": "このリソースへのアクセス権限がありません",
  "instance": "/api/projects/456",
  "projectDepartment": "Development",
  "userDepartment": "Sales"
}
```

### 404 Not Found

#### Use Case 1: 存在しないリソース

**シナリオ**: 無効なプロジェクトIDを指定

**Request**:
```
GET /api/projects/999
```

**Response** (404 Not Found):
```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "指定されたプロジェクトが見つかりません",
  "instance": "/api/projects/999",
  "resourceType": "Project",
  "resourceID": 999
}
```

#### Use Case 2: 削除済みリソース

**シナリオ**: 論理削除されたプロジェクトにアクセス

**Request**:
```
GET /api/projects/456
```

**Response** (404 Not Found):
```json
{
  "type": "https://api.example.com/errors/resource-deleted",
  "title": "Resource Deleted",
  "status": 404,
  "detail": "指定されたプロジェクトは削除されています",
  "instance": "/api/projects/456",
  "deletedAt": "2026-01-10T15:00:00Z"
}
```

#### Use Case 3: 外部キー参照エラー

**シナリオ**: 存在しない顧客IDを指定してプロジェクト作成

**Request**:
```
POST /api/projects
Content-Type: application/json

{
  "projectName": "新システム開発",
  "customerID": 999
}
```

**Response** (404 Not Found):
```json
{
  "type": "https://api.example.com/errors/foreign-key-not-found",
  "title": "Foreign Key Not Found",
  "status": 404,
  "detail": "指定された顧客が存在しません",
  "instance": "/api/projects",
  "field": "customerID",
  "value": 999,
  "referencedResource": "Customer"
}
```

### 409 Conflict

#### Use Case 1: 重複エラー（単一キー）

**シナリオ**: 既存のメールアドレスで登録

**Request**:
```
POST /api/persons
Content-Type: application/json

{
  "personName": "山田太郎",
  "email": "existing@example.com"
}
```

**Response** (409 Conflict):
```json
{
  "type": "https://api.example.com/errors/duplicate-resource",
  "title": "Duplicate Resource",
  "status": 409,
  "detail": "このメールアドレスは既に使用されています",
  "instance": "/api/persons",
  "field": "email",
  "value": "existing@example.com",
  "existingResourceID": 123
}
```

#### Use Case 2: 重複エラー（複合キー）

**シナリオ**: 同一顧客で同じプロジェクト名

**Request**:
```
POST /api/projects
Content-Type: application/json

{
  "projectName": "既存プロジェクト",
  "customerID": 123
}
```

**Response** (409 Conflict):
```json
{
  "type": "https://api.example.com/errors/duplicate-resource",
  "title": "Duplicate Resource",
  "status": 409,
  "detail": "この顧客には既に同名のプロジェクトが存在します",
  "instance": "/api/projects",
  "fields": ["customerID", "projectName"],
  "values": [123, "既存プロジェクト"],
  "existingResourceID": 456
}
```

#### Use Case 3: 競合状態（Optimistic Locking）

**シナリオ**: 同時更新により競合

**Request**:
```
PUT /api/projects/456
Content-Type: application/json
If-Match: "etag-version-1"

{
  "projectName": "更新後プロジェクト名"
}
```

**Response** (409 Conflict):
```json
{
  "type": "https://api.example.com/errors/concurrent-modification",
  "title": "Concurrent Modification",
  "status": 409,
  "detail": "リソースが別のユーザーによって更新されています。最新の状態を取得してから再試行してください",
  "instance": "/api/projects/456",
  "currentETag": "etag-version-2",
  "providedETag": "etag-version-1"
}
```

### 422 Unprocessable Entity

#### Use Case 1: 無効なステータス遷移

**シナリオ**: 完了したプロジェクトを企画中に戻す

**Request**:
```
PATCH /api/projects/456
Content-Type: application/json

{
  "status": "PLANNING"
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/invalid-state-transition",
  "title": "Invalid State Transition",
  "status": 422,
  "detail": "COMPLETED から PLANNING への遷移は許可されていません",
  "instance": "/api/projects/456",
  "currentStatus": "COMPLETED",
  "requestedStatus": "PLANNING",
  "allowedTransitions": []
}
```

#### Use Case 2: ビジネスルール違反

**シナリオ**: プロジェクト開始後に契約金額を変更

**Request**:
```
PATCH /api/projects/456
Content-Type: application/json

{
  "contractAmount": 2000000
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/business-rule-violation",
  "title": "Business Rule Violation",
  "status": 422,
  "detail": "プロジェクト開始後は契約金額を変更できません",
  "instance": "/api/projects/456",
  "projectStatus": "IN_PROGRESS",
  "startedAt": "2026-01-05T09:00:00Z"
}
```

#### Use Case 3: 容量制限超過

**シナリオ**: プロジェクトメンバー数が上限に達している

**Request**:
```
POST /api/projects/456/members
Content-Type: application/json

{
  "personID": 10,
  "role": "Engineer"
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/capacity-exceeded",
  "title": "Capacity Exceeded",
  "status": 422,
  "detail": "プロジェクトの最大メンバー数（20人）に達しています",
  "instance": "/api/projects/456/members",
  "currentMemberCount": 20,
  "maxCapacity": 20
}
```

### 429 Too Many Requests

#### Use Case: レート制限超過

**シナリオ**: 1分間に100回以上のリクエスト

**Request**:
```
GET /api/projects
```

**Response** (429 Too Many Requests):
```json
{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "レート制限を超過しました。しばらく待ってから再試行してください",
  "instance": "/api/projects",
  "retryAfter": 60,
  "limit": 100,
  "window": "1 minute"
}
```

**Response Headers**:
```
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-01-11T10:01:00Z
```

---

## Server Errors (5xx)

### 500 Internal Server Error

#### Use Case: 予期しないサーバーエラー

**Request**:
```
POST /api/projects
```

**Response** (500 Internal Server Error):
```json
{
  "type": "https://api.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "サーバー内部エラーが発生しました。しばらく待ってから再試行してください",
  "instance": "/api/projects",
  "errorID": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

**注意**: エラーの詳細（スタックトレースなど）はクライアントに返さない（セキュリティ上の理由）

### 502 Bad Gateway

#### Use Case: 外部API呼び出しエラー

**シナリオ**: 外部決済APIがエラーを返す

**Request**:
```
POST /api/payments
```

**Response** (502 Bad Gateway):
```json
{
  "type": "https://api.example.com/errors/external-service-error",
  "title": "External Service Error",
  "status": 502,
  "detail": "外部決済サービスでエラーが発生しました",
  "instance": "/api/payments",
  "externalService": "PaymentGateway",
  "externalErrorCode": "INSUFFICIENT_FUNDS"
}
```

### 503 Service Unavailable

#### Use Case: メンテナンス中

**Request**:
```
GET /api/projects
```

**Response** (503 Service Unavailable):
```json
{
  "type": "https://api.example.com/errors/maintenance",
  "title": "Service Unavailable",
  "status": 503,
  "detail": "メンテナンス中です。しばらく待ってから再試行してください",
  "instance": "/api/projects",
  "estimatedRecovery": "2026-01-11T12:00:00Z"
}
```

**Response Headers**:
```
Retry-After: 3600
```

### 504 Gateway Timeout

#### Use Case: 外部APIタイムアウト

**シナリオ**: 外部APIが応答しない

**Request**:
```
POST /api/external-sync
```

**Response** (504 Gateway Timeout):
```json
{
  "type": "https://api.example.com/errors/gateway-timeout",
  "title": "Gateway Timeout",
  "status": 504,
  "detail": "外部サービスが応答しませんでした",
  "instance": "/api/external-sync",
  "externalService": "ThirdPartyAPI",
  "timeout": "30s"
}
```

---

## Business Rule Errors

### Pattern 1: 相互排他制約

**シナリオ**: 同じ人を同じプロジェクトに重複してアサイン

**Response** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/duplicate-assignment",
  "title": "Duplicate Assignment",
  "status": 422,
  "detail": "この人は既にプロジェクトにアサインされています",
  "personID": 5,
  "projectID": 456,
  "existingAssignmentID": 10
}
```

### Pattern 2: 前提条件未満足

**シナリオ**: プロジェクト開始前にメンバーをアサイン

**Response** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/precondition-not-met",
  "title": "Precondition Not Met",
  "status": 422,
  "detail": "プロジェクトが開始されていないため、メンバーをアサインできません",
  "projectID": 456,
  "projectStatus": "PLANNING",
  "requiredStatus": "IN_PROGRESS"
}
```

---

## External Dependency Errors

### Pattern 1: データベース接続エラー

**Response** (503 Service Unavailable):
```json
{
  "type": "https://api.example.com/errors/database-unavailable",
  "title": "Database Unavailable",
  "status": 503,
  "detail": "データベース接続エラー。しばらく待ってから再試行してください"
}
```

### Pattern 2: 外部API認証エラー

**Response** (502 Bad Gateway):
```json
{
  "type": "https://api.example.com/errors/external-auth-failed",
  "title": "External Authentication Failed",
  "status": 502,
  "detail": "外部サービスの認証に失敗しました",
  "externalService": "ThirdPartyAPI"
}
```

---

## Best Practices

### 1. 一貫したエラー形式

すべてのエラーレスポンスでRFC 7807形式を使用:

```json
{
  "type": "https://api.example.com/errors/{error-type}",
  "title": "Human-Readable Title",
  "status": 400,
  "detail": "Detailed error message"
}
```

### 2. 詳細なバリデーションエラー

複数のフィールドエラーをまとめて返す:

```json
{
  "errors": [
    {"field": "projectName", "message": "..."},
    {"field": "contractAmount", "message": "..."}
  ]
}
```

### 3. エラーID

デバッグ用にエラーIDを含める:

```json
{
  "errorID": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### 4. セキュリティ考慮

内部実装の詳細を漏らさない:

```json
// ❌ Bad
{"error": "SQL Error: SELECT * FROM users WHERE id = 'invalid'"}

// ✅ Good
{"error": "Invalid user ID"}
```

### 5. ローカライゼーション

多言語対応:

```
Accept-Language: ja

{
  "detail": "プロジェクト名は必須です"
}
```

---

## Error Response Template

```json
{
  "type": "https://api.example.com/errors/{error-type}",
  "title": "{Error Title}",
  "status": {http-status-code},
  "detail": "{Detailed error message}",
  "instance": "{request-path}",
  "timestamp": "2026-01-11T10:00:00Z",
  "errorID": "{uuid}",
  "errors": [
    {
      "field": "{field-name}",
      "message": "{field-specific-error}",
      "value": "{provided-value}"
    }
  ]
}
```
