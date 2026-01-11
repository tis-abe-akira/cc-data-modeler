# RFC 7807 Problem Details Reference

RFC 7807「HTTP APIのための問題詳細」に準拠したエラーレスポンス設計のリファレンス。

## Table of Contents

1. [RFC 7807 概要](#rfc-7807-概要)
2. [Problem Details の基本構造](#problem-details-の基本構造)
3. [標準HTTPステータスコード](#標準httpステータスコード)
4. [400 Bad Request](#400-bad-request)
5. [401 Unauthorized](#401-unauthorized)
6. [403 Forbidden](#403-forbidden)
7. [404 Not Found](#404-not-found)
8. [409 Conflict](#409-conflict)
9. [422 Unprocessable Entity](#422-unprocessable-entity)
10. [429 Too Many Requests](#429-too-many-requests)
11. [500 Internal Server Error](#500-internal-server-error)
12. [503 Service Unavailable](#503-service-unavailable)
13. [OpenAPI での定義](#openapi-での定義)
14. [ベストプラクティス](#ベストプラクティス)

---

## RFC 7807 概要

### 目的

RFC 7807 は、HTTP API のエラーレスポンスを標準化するための仕様。

**問題点**:
```json
❌ 統一性のないエラーレスポンス
{"error": "Invalid input"}
{"message": "Bad request", "code": 400}
{"errors": ["Name is required"]}
```

**解決策**:
```json
✅ RFC 7807 準拠のエラーレスポンス
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "入力値にエラーがあります",
  "instance": "/api/projects"
}
```

### 利点

1. **標準化**: 全APIで一貫したエラーフォーマット
2. **機械可読性**: `type` URIでエラー種別を明確に識別
3. **人間可読性**: `title`, `detail` で詳細説明
4. **拡張性**: カスタムフィールドを追加可能
5. **国際化対応**: 多言語エラーメッセージに対応可能

### 仕様リンク

- [RFC 7807 公式仕様](https://tools.ietf.org/html/rfc7807)
- [MDN Web Docs - HTTP Problem Details](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

---

## Problem Details の基本構造

### 必須フィールド

#### `type` (string, URI)

**説明**: エラー種別を示すURI

**例**:
```json
"type": "https://api.example.com/errors/validation-error"
```

**ルール**:
- 絶対URI または 相対URI
- デフォルト: `about:blank`（HTTPステータスコードのみで十分な場合）
- 人間が読むドキュメントにリンクすることを推奨

#### `title` (string)

**説明**: エラーの簡潔な概要（人間可読）

**例**:
```json
"title": "Validation Error"
```

**ルール**:
- 同じ `type` のエラーでは常に同じ `title` を使用
- 多言語対応の場合、Accept-Language ヘッダーに応じて変更可能

#### `status` (integer)

**説明**: HTTPステータスコード

**例**:
```json
"status": 400
```

**ルール**:
- 実際のHTTPレスポンスステータスと一致させる
- クライアントが複数の問題詳細を一度に受け取る場合に便利

### 任意フィールド

#### `detail` (string)

**説明**: エラーの詳細説明（人間可読、インスタンス固有）

**例**:
```json
"detail": "プロジェクト名は1-200文字で入力してください"
```

**ルール**:
- `title` とは異なり、インスタンス固有の詳細を含む
- ユーザーに表示する具体的なメッセージ

#### `instance` (string, URI)

**説明**: エラーが発生した具体的なリクエストURI

**例**:
```json
"instance": "/api/projects/456"
```

**ルール**:
- 相対URIまたは絶対URI
- デバッグに役立つ

### 拡張フィールド

カスタムフィールドを追加可能:

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "入力値にエラーがあります",
  "instance": "/api/projects",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は必須です",
      "value": null
    }
  ],
  "requestId": "req-12345",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### Content-Type

RFC 7807 準拠のレスポンスは以下のContent-Typeを使用:

```
Content-Type: application/problem+json
```

または

```
Content-Type: application/problem+xml
```

---

## 標準HTTPステータスコード

### エラーコード一覧

| コード | 名称 | 用途 |
|-------|------|------|
| 400 | Bad Request | バリデーションエラー |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | 認可エラー（権限不足） |
| 404 | Not Found | リソースが存在しない |
| 409 | Conflict | リソースの競合・重複 |
| 422 | Unprocessable Entity | ビジネスルール違反 |
| 429 | Too Many Requests | レート制限超過 |
| 500 | Internal Server Error | サーバー内部エラー |
| 503 | Service Unavailable | サービス一時停止 |

---

## 400 Bad Request

### 用途

クライアントからのリクエストにバリデーションエラーがある場合。

### 典型的なケース

- 必須パラメータの欠落
- 不正な型（stringを期待しているがintegerが送られた）
- 値の範囲外（0-100を期待しているが200が送られた）
- 不正なフォーマット（日付形式が間違っている）

### OpenAPI 定義

```yaml
components:
  responses:
    BadRequest:
      description: バリデーションエラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            validationError:
              summary: 必須項目欠損
              value:
                type: https://api.example.com/errors/validation-error
                title: Validation Error
                status: 400
                detail: 必須項目が不足しています
                instance: /api/projects
                errors:
                  - field: projectName
                    message: プロジェクト名は必須です
                    value: null
            invalidFormat:
              summary: 不正なフォーマット
              value:
                type: https://api.example.com/errors/validation-error
                title: Validation Error
                status: 400
                detail: 日付フォーマットが不正です
                instance: /api/projects
                errors:
                  - field: plannedStartDate
                    message: YYYY-MM-DD 形式で入力してください
                    value: "2026/01/01"
```

### レスポンス例1: 必須項目欠損

```json
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "必須項目が不足しています",
  "instance": "/api/projects",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は必須です",
      "value": null
    },
    {
      "field": "customerID",
      "message": "顧客IDは必須です",
      "value": null
    }
  ]
}
```

### レスポンス例2: 文字数制限違反

```json
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "文字数制限を超えています",
  "instance": "/api/projects",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は1-200文字で入力してください",
      "value": "このプロジェクト名は200文字を超える非常に長い名前で...(省略)",
      "constraint": {
        "minLength": 1,
        "maxLength": 200,
        "actualLength": 250
      }
    }
  ]
}
```

### レスポンス例3: 値の範囲外

```json
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "値が許容範囲外です",
  "instance": "/api/projects",
  "errors": [
    {
      "field": "contractAmount",
      "message": "契約金額は0以上である必要があります",
      "value": -1000000,
      "constraint": {
        "minimum": 0
      }
    }
  ]
}
```

---

## 401 Unauthorized

### 用途

認証が必要だが、認証情報が提供されていないか、無効な場合。

### OpenAPI 定義

```yaml
components:
  responses:
    Unauthorized:
      description: 認証エラー
      headers:
        WWW-Authenticate:
          schema:
            type: string
          description: 認証方式（Bearer）
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            missingToken:
              summary: トークン未提供
              value:
                type: https://api.example.com/errors/unauthorized
                title: Unauthorized
                status: 401
                detail: 認証トークンが提供されていません
                instance: /api/projects/456
            invalidToken:
              summary: 無効なトークン
              value:
                type: https://api.example.com/errors/unauthorized
                title: Unauthorized
                status: 401
                detail: 認証トークンが無効または期限切れです
                instance: /api/projects/456
```

### レスポンス例1: トークン未提供

```json
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api.example.com"
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "認証トークンが提供されていません。Authorization ヘッダーを追加してください。",
  "instance": "/api/projects/456"
}
```

### レスポンス例2: トークン期限切れ

```json
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api.example.com", error="invalid_token", error_description="Token expired"
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/token-expired",
  "title": "Token Expired",
  "status": 401,
  "detail": "認証トークンの有効期限が切れています。再ログインしてください。",
  "instance": "/api/projects/456",
  "expiredAt": "2026-01-10T23:59:59Z"
}
```

---

## 403 Forbidden

### 用途

認証は成功しているが、リソースへのアクセス権限がない場合。

### OpenAPI 定義

```yaml
components:
  responses:
    Forbidden:
      description: 権限エラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            insufficientPermissions:
              summary: 権限不足
              value:
                type: https://api.example.com/errors/forbidden
                title: Forbidden
                status: 403
                detail: このリソースへのアクセス権限がありません
                instance: /api/projects/456
```

### レスポンス例1: 権限不足

```json
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "このプロジェクトを開始する権限がありません。プロジェクトマネージャーロールが必要です。",
  "instance": "/api/projects/456/start",
  "requiredRole": "PROJECT_MANAGER",
  "userRole": "ENGINEER"
}
```

### レスポンス例2: リソースオーナーのみ許可

```json
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "このプロジェクトを削除できるのはプロジェクトオーナーのみです。",
  "instance": "/api/projects/456",
  "projectOwner": 10,
  "currentUser": 5
}
```

---

## 404 Not Found

### 用途

指定されたリソースが存在しない場合。

### OpenAPI 定義

```yaml
components:
  responses:
    NotFound:
      description: リソースが見つからない
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            resourceNotFound:
              summary: リソース不存在
              value:
                type: https://api.example.com/errors/not-found
                title: Resource Not Found
                status: 404
                detail: 指定されたプロジェクトが見つかりません
                instance: /api/projects/999
```

### レスポンス例1: プロジェクト不存在

```json
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "指定されたプロジェクトが見つかりません",
  "instance": "/api/projects/999",
  "resourceType": "Project",
  "resourceId": 999
}
```

### レスポンス例2: 外部キーエラー（関連リソース不存在）

```json
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "指定された顧客が見つかりません",
  "instance": "/api/projects",
  "field": "customerID",
  "value": 999,
  "resourceType": "Customer"
}
```

---

## 409 Conflict

### 用途

リソースの競合や重複が発生した場合。

### OpenAPI 定義

```yaml
components:
  responses:
    Conflict:
      description: リソースの競合
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            duplicateResource:
              summary: 重複エラー
              value:
                type: https://api.example.com/errors/conflict
                title: Resource Conflict
                status: 409
                detail: この顧客には既に同名のプロジェクトが存在します
                instance: /api/projects
```

### レスポンス例1: 重複エラー

```json
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/conflict",
  "title": "Resource Conflict",
  "status": 409,
  "detail": "この顧客には既に同名のプロジェクトが存在します",
  "instance": "/api/projects",
  "conflictFields": ["customerID", "projectName"],
  "conflictValues": [123, "新システム開発"],
  "existingResourceId": 456
}
```

### レスポンス例2: Idempotency-Key 重複

```json
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/idempotency-conflict",
  "title": "Idempotency Key Conflict",
  "status": 409,
  "detail": "この Idempotency-Key は既に使用されていますが、リクエスト内容が異なります",
  "instance": "/api/projects/456/start",
  "idempotencyKey": "550e8400-e29b-41d4-a716-446655440000",
  "originalRequest": {
    "startDateTime": "2026-02-01T09:00:00Z"
  },
  "currentRequest": {
    "startDateTime": "2026-02-02T09:00:00Z"
  }
}
```

### レスポンス例3: 同時更新競合（楽観的ロック）

```json
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/optimistic-lock-error",
  "title": "Optimistic Lock Error",
  "status": 409,
  "detail": "リソースが既に他のユーザーによって更新されています",
  "instance": "/api/projects/456",
  "expectedVersion": 5,
  "actualVersion": 6
}
```

---

## 422 Unprocessable Entity

### 用途

リクエストの構文は正しいが、ビジネスルール違反により処理できない場合。

### 400 vs 422

- **400 Bad Request**: 構文エラー、型エラー、必須項目欠損
- **422 Unprocessable Entity**: ビジネスロジックエラー、制約違反

### OpenAPI 定義

```yaml
components:
  responses:
    UnprocessableEntity:
      description: ビジネスルール違反
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            businessRuleViolation:
              summary: ビジネスルール違反
              value:
                type: https://api.example.com/errors/business-rule-violation
                title: Business Rule Violation
                status: 422
                detail: プロジェクトを開始できません
                instance: /api/projects/456/start
```

### レスポンス例1: 状態遷移エラー

```json
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/invalid-state-transition",
  "title": "Invalid State Transition",
  "status": 422,
  "detail": "既に完了したプロジェクトは開始できません",
  "instance": "/api/projects/456/start",
  "currentState": "COMPLETED",
  "requestedTransition": "START",
  "allowedTransitions": []
}
```

### レスポンス例2: ビジネス制約違反

```json
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/business-constraint-violation",
  "title": "Business Constraint Violation",
  "status": 422,
  "detail": "同一人物を同じプロジェクトに重複してアサインできません",
  "instance": "/api/projects/456/members",
  "field": "personID",
  "value": 3,
  "reason": "Person 3 is already assigned to this project"
}
```

### レスポンス例3: 日付制約違反

```json
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/date-constraint-violation",
  "title": "Date Constraint Violation",
  "status": 422,
  "detail": "プロジェクト完了日は開始日より後である必要があります",
  "instance": "/api/projects/456/complete",
  "field": "completeDateTime",
  "value": "2026-01-15T10:00:00Z",
  "constraint": "completeDateTime > startDateTime",
  "startDateTime": "2026-02-01T09:00:00Z"
}
```

---

## 429 Too Many Requests

### 用途

レート制限を超過した場合。

### OpenAPI 定義

```yaml
components:
  responses:
    TooManyRequests:
      description: レート制限超過
      headers:
        Retry-After:
          schema:
            type: integer
          description: 再試行可能になるまでの秒数
        X-RateLimit-Limit:
          schema:
            type: integer
          description: レート制限の上限
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: 残りリクエスト数
        X-RateLimit-Reset:
          schema:
            type: integer
          description: レート制限リセット時刻（Unixタイムスタンプ）
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            rateLimitExceeded:
              summary: レート制限超過
              value:
                type: https://api.example.com/errors/rate-limit-exceeded
                title: Rate Limit Exceeded
                status: 429
                detail: リクエスト制限を超過しました
                instance: /api/projects
```

### レスポンス例

```json
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704967200
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "リクエスト制限（100リクエスト/分）を超過しました。60秒後に再試行してください。",
  "instance": "/api/projects",
  "rateLimit": {
    "limit": 100,
    "remaining": 0,
    "resetAt": "2026-01-11T10:00:00Z"
  }
}
```

---

## 500 Internal Server Error

### 用途

サーバー内部エラー、予期しない例外が発生した場合。

### OpenAPI 定義

```yaml
components:
  responses:
    InternalServerError:
      description: サーバー内部エラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            serverError:
              summary: サーバー内部エラー
              value:
                type: https://api.example.com/errors/internal-server-error
                title: Internal Server Error
                status: 500
                detail: サーバー内部エラーが発生しました
                instance: /api/projects/456
```

### レスポンス例

```json
HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "予期しないエラーが発生しました。システム管理者に連絡してください。",
  "instance": "/api/projects/456/start",
  "requestId": "req-12345",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

**注意**: 本番環境では、セキュリティ上の理由から詳細なスタックトレースやエラー内容を含めない。

---

## 503 Service Unavailable

### 用途

サーバーが一時的に利用できない場合（メンテナンス、過負荷など）。

### OpenAPI 定義

```yaml
components:
  responses:
    ServiceUnavailable:
      description: サービス一時停止
      headers:
        Retry-After:
          schema:
            type: integer
          description: サービス復旧予定時刻までの秒数
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            maintenance:
              summary: メンテナンス中
              value:
                type: https://api.example.com/errors/service-unavailable
                title: Service Unavailable
                status: 503
                detail: 現在メンテナンス中です
                instance: /api/projects
```

### レスポンス例1: メンテナンス中

```json
HTTP/1.1 503 Service Unavailable
Retry-After: 3600
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/maintenance",
  "title": "Service Under Maintenance",
  "status": 503,
  "detail": "システムメンテナンスのため、一時的にサービスを停止しています。1時間後に再試行してください。",
  "instance": "/api/projects",
  "maintenanceWindow": {
    "start": "2026-01-11T10:00:00Z",
    "end": "2026-01-11T11:00:00Z"
  }
}
```

### レスポンス例2: データベース接続エラー

```json
HTTP/1.1 503 Service Unavailable
Retry-After: 30
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/database-unavailable",
  "title": "Database Unavailable",
  "status": 503,
  "detail": "データベースに接続できません。しばらくしてから再試行してください。",
  "instance": "/api/projects/456",
  "requestId": "req-12345"
}
```

---

## OpenAPI での定義

### ProblemDetails スキーマ

```yaml
components:
  schemas:
    ProblemDetails:
      type: object
      required:
        - type
        - title
        - status
      properties:
        type:
          type: string
          format: uri
          description: エラー種別を示すURI
          example: https://api.example.com/errors/validation-error
        title:
          type: string
          description: エラーの概要
          example: Validation Error
        status:
          type: integer
          description: HTTPステータスコード
          example: 400
        detail:
          type: string
          description: エラーの詳細説明
          example: 必須項目が不足しています
        instance:
          type: string
          format: uri
          description: エラーが発生したリクエストURI
          example: /api/projects
      additionalProperties: true
      description: RFC 7807 準拠のエラーレスポンス
```

### 拡張スキーマ（バリデーションエラー用）

```yaml
components:
  schemas:
    ValidationError:
      allOf:
        - $ref: '#/components/schemas/ProblemDetails'
        - type: object
          properties:
            errors:
              type: array
              description: 詳細なバリデーションエラー
              items:
                type: object
                required:
                  - field
                  - message
                properties:
                  field:
                    type: string
                    description: エラーが発生したフィールド名
                    example: projectName
                  message:
                    type: string
                    description: エラーメッセージ
                    example: プロジェクト名は必須です
                  value:
                    description: 送信された値
                    example: null
                  constraint:
                    type: object
                    description: 制約条件
                    example:
                      minLength: 1
                      maxLength: 200
```

### エンドポイントでの使用例

```yaml
/api/projects:
  post:
    summary: 新しいプロジェクトを作成する
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProjectCreateCommand'
    responses:
      '201':
        description: プロジェクト作成成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectCreateResponse'
      '400':
        description: バリデーションエラー
        content:
          application/problem+json:
            schema:
              $ref: '#/components/schemas/ValidationError'
            examples:
              missingFields:
                $ref: '#/components/examples/ValidationErrorMissingFields'
      '404':
        description: 顧客が見つからない
        content:
          application/problem+json:
            schema:
              $ref: '#/components/schemas/ProblemDetails'
            examples:
              customerNotFound:
                $ref: '#/components/examples/CustomerNotFound'
      '409':
        description: プロジェクト重複
        content:
          application/problem+json:
            schema:
              $ref: '#/components/schemas/ProblemDetails'
            examples:
              duplicateProject:
                $ref: '#/components/examples/DuplicateProject'
      '500':
        description: サーバー内部エラー
        content:
          application/problem+json:
            schema:
              $ref: '#/components/schemas/ProblemDetails'
```

### 共通エラーレスポンス定義

全エンドポイントで共有できる標準エラーレスポンスを定義:

```yaml
components:
  responses:
    BadRequest:
      description: バリデーションエラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ValidationError'
          examples:
            validationError:
              $ref: '#/components/examples/ValidationErrorMissingFields'

    Unauthorized:
      description: 認証エラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            unauthorized:
              $ref: '#/components/examples/Unauthorized'

    Forbidden:
      description: 権限エラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            forbidden:
              $ref: '#/components/examples/Forbidden'

    NotFound:
      description: リソースが見つからない
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            notFound:
              $ref: '#/components/examples/NotFound'

    Conflict:
      description: リソースの競合
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            conflict:
              $ref: '#/components/examples/Conflict'

    UnprocessableEntity:
      description: ビジネスルール違反
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            businessRuleViolation:
              $ref: '#/components/examples/BusinessRuleViolation'

    TooManyRequests:
      description: レート制限超過
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            rateLimitExceeded:
              $ref: '#/components/examples/RateLimitExceeded'

    InternalServerError:
      description: サーバー内部エラー
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            serverError:
              $ref: '#/components/examples/InternalServerError'

    ServiceUnavailable:
      description: サービス一時停止
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            maintenance:
              $ref: '#/components/examples/ServiceUnavailable'
```

### エンドポイントでの参照

```yaml
/api/projects/{projectId}/start:
  post:
    summary: プロジェクトを開始する
    responses:
      '201':
        description: プロジェクト開始成功
      '400':
        $ref: '#/components/responses/BadRequest'
      '401':
        $ref: '#/components/responses/Unauthorized'
      '403':
        $ref: '#/components/responses/Forbidden'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
      '422':
        $ref: '#/components/responses/UnprocessableEntity'
      '500':
        $ref: '#/components/responses/InternalServerError'
```

---

## ベストプラクティス

### ✅ DO: 一貫したエラーフォーマット

全APIで RFC 7807 形式を使用:

```json
{
  "type": "https://api.example.com/errors/...",
  "title": "...",
  "status": 400,
  "detail": "...",
  "instance": "/api/..."
}
```

### ✅ DO: type URI でエラー種別を明確に

```json
"type": "https://api.example.com/errors/validation-error"
"type": "https://api.example.com/errors/business-rule-violation"
"type": "https://api.example.com/errors/rate-limit-exceeded"
```

### ✅ DO: 詳細なエラー情報を提供（開発環境）

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "必須項目が不足しています",
  "instance": "/api/projects",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は必須です",
      "value": null,
      "constraint": {
        "required": true
      }
    }
  ]
}
```

### ✅ DO: 本番環境ではスタックトレースを隠す

```json
❌ 本番環境で避けるべき
{
  "status": 500,
  "error": "NullPointerException at line 123",
  "stackTrace": "..."
}

✅ 本番環境で推奨
{
  "type": "https://api.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "予期しないエラーが発生しました。システム管理者に連絡してください。",
  "instance": "/api/projects/456",
  "requestId": "req-12345"
}
```

### ✅ DO: 多言語対応

Accept-Language ヘッダーに応じて `title` と `detail` を翻訳:

```http
GET /api/projects/999
Accept-Language: ja
```

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "リソースが見つかりません",
  "status": 404,
  "detail": "指定されたプロジェクトが見つかりません"
}
```

```http
GET /api/projects/999
Accept-Language: en
```

```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "The specified project was not found"
}
```

### ✅ DO: requestId を含める（トレーサビリティ）

```json
{
  "type": "https://api.example.com/errors/internal-server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "予期しないエラーが発生しました",
  "instance": "/api/projects/456",
  "requestId": "req-12345",
  "timestamp": "2026-01-11T10:00:00Z"
}
```

クライアントがエラー報告時に `requestId` を提供できる。

### ✅ DO: Content-Type に application/problem+json を使用

```http
HTTP/1.1 400 Bad Request
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "必須項目が不足しています"
}
```

### ❌ DON'T: エラーコードを数値で管理

```json
❌ 避けるべき
{
  "errorCode": 1001,
  "message": "Validation error"
}
```

理由: エラーコードの意味がわかりにくい。代わりに `type` URI を使用。

```json
✅ 推奨
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400
}
```

### ❌ DON'T: エラーメッセージだけ返す

```json
❌ 避けるべき
{
  "error": "Invalid input"
}
```

### ✅ DO: RFC 7807 完全準拠

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid input",
  "instance": "/api/projects"
}
```

---

## まとめ

### RFC 7807 の利点

1. **標準化**: 全APIで一貫したエラーフォーマット
2. **機械可読性**: `type` URIでエラー種別を識別
3. **人間可読性**: `title`, `detail` で詳細説明
4. **拡張性**: カスタムフィールドで追加情報を提供
5. **国際化対応**: 多言語エラーメッセージ

### 実装チェックリスト

- [ ] 全エラーレスポンスが RFC 7807 形式
- [ ] Content-Type: application/problem+json を使用
- [ ] `type` URI が全エラーに設定されている
- [ ] `title`, `status`, `detail` が適切に記述されている
- [ ] バリデーションエラーに `errors` 配列を含む
- [ ] 本番環境でスタックトレースを隠す
- [ ] `requestId` を含めてトレーサビリティを確保
- [ ] Accept-Language ヘッダーに応じた多言語対応
- [ ] OpenAPI で全エラーレスポンスを定義

### 参考資料

- [RFC 7807 公式仕様](https://tools.ietf.org/html/rfc7807)
- [MDN - HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Zalando API Guidelines - Problem Details](https://opensource.zalando.com/restful-api-guidelines/#176)
