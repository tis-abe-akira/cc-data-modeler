# Validation Rules Reference

API設計における一般的なバリデーションルールのリファレンス。

## Table of Contents

1. [Required Fields](#required-fields)
2. [String Validations](#string-validations)
3. [Numeric Validations](#numeric-validations)
4. [Date/Time Validations](#datetime-validations)
5. [Email/URL Validations](#emailurl-validations)
6. [Foreign Key Validations](#foreign-key-validations)
7. [Uniqueness Constraints](#uniqueness-constraints)
8. [Business Rule Validations](#business-rule-validations)

---

## Required Fields

### Pattern 1: Mandatory Fields

**検証ルール**:
```
必須項目: projectName, plannedStartDate, contractAmount
```

**APIバリデーション**:
- Request Body で `null` や欠損を許可しない
- 空文字列 `""` も不可

**エラーレスポンス** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "必須項目が不足しています",
  "errors": [
    {
      "field": "projectName",
      "message": "プロジェクト名は必須です",
      "value": null
    }
  ]
}
```

### Pattern 2: Conditional Required Fields

**検証ルール**:
```
contractAmount が 10,000,000 以上の場合、approverID が必須
```

**APIバリデーション**:
```typescript
if (contractAmount >= 10000000 && !approverID) {
  throw ValidationError("契約金額が1000万円以上の場合、承認者IDが必要です");
}
```

---

## String Validations

### Pattern 1: Length Constraints

| フィールド | 最小 | 最大 | 例 |
|----------|-----|------|---|
| 名前系 | 1 | 100 | customerName, projectName |
| 説明文 | 0 (任意) | 500 | description |
| 長文 | 0 (任意) | 5000 | detailedNote |
| コード | 3 | 20 | projectCode |

**検証ルール**:
```
projectName: 1-200文字
description: 0-500文字（任意）
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "errors": [
    {
      "field": "projectName",
      "message": "1-200文字で入力してください",
      "value": "" (空文字列または201文字以上)
    }
  ]
}
```

### Pattern 2: Pattern Matching (Regex)

**検証ルール**:
```
projectCode: 英数字のみ、ハイフン可、例: PRJ-2026-001
```

**正規表現**:
```regex
^[A-Z0-9-]+$
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "projectCode",
  "message": "プロジェクトコードは英数字とハイフンのみ使用可能です",
  "value": "プロジェクト-001"
}
```

### Pattern 3: Allowed Values (Enum)

**検証ルール**:
```
status: PLANNING, IN_PROGRESS, COMPLETED, CANCELLED のいずれか
```

**APIバリデーション**:
```typescript
const allowedStatuses = ['PLANNING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'];
if (!allowedStatuses.includes(status)) {
  throw ValidationError("無効なステータスです");
}
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "status",
  "message": "ステータスは PLANNING, IN_PROGRESS, COMPLETED, CANCELLED のいずれかを指定してください",
  "value": "UNKNOWN"
}
```

---

## Numeric Validations

### Pattern 1: Range Constraints

**検証ルール**:
```
contractAmount: 0以上
progressRate: 0-100（パーセント）
priority: 1-5
```

**APIバリデーション**:
```typescript
if (contractAmount < 0) {
  throw ValidationError("契約金額は0以上である必要があります");
}

if (progressRate < 0 || progressRate > 100) {
  throw ValidationError("進捗率は0-100の範囲で指定してください");
}
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "contractAmount",
  "message": "契約金額は0以上である必要があります",
  "value": -1000
}
```

### Pattern 2: Precision Constraints

**検証ルール**:
```
contractAmount: 小数点以下0桁（整数のみ）
estimatedHours: 小数点以下1桁まで（例: 120.5）
```

**APIバリデーション**:
```typescript
if (!Number.isInteger(contractAmount)) {
  throw ValidationError("契約金額は整数で指定してください");
}
```

### Pattern 3: Positive/Negative Constraints

**検証ルール**:
```
quantity: 正の整数（1以上）
adjustment: 負の値可（増減を表す）
```

---

## Date/Time Validations

### Pattern 1: Date Range

**検証ルール**:
```
plannedStartDate: 今日以降
completedDate: plannedStartDate 以降
```

**APIバリデーション**:
```typescript
if (new Date(plannedStartDate) < new Date().setHours(0, 0, 0, 0)) {
  throw ValidationError("予定開始日は今日以降である必要があります");
}

if (completedDate && new Date(completedDate) < new Date(plannedStartDate)) {
  throw ValidationError("完了日は予定開始日以降である必要があります");
}
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "plannedStartDate",
  "message": "予定開始日は今日以降である必要があります",
  "value": "2025-01-01"
}
```

### Pattern 2: Past/Future Constraints

| フィールド | 制約 | 理由 |
|----------|------|------|
| birthDate | 過去のみ | 誕生日は未来にはならない |
| plannedDate | 未来のみ | 計画は未来に対して行う |
| recordedAt | 過去〜現在 | 記録は過去または現在 |

### Pattern 3: Date Format

**検証ルール**:
```
日付: YYYY-MM-DD (ISO 8601)
日時: YYYY-MM-DDTHH:MM:SSZ (ISO 8601, UTC)
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "plannedStartDate",
  "message": "日付はYYYY-MM-DD形式で指定してください",
  "value": "2026/01/11"
}
```

### Pattern 4: Business Days

**検証ルール**:
```
契約日: 平日のみ（土日祝日は不可）
```

**APIバリデーション**:
```typescript
if (isWeekend(contractDate) || isHoliday(contractDate)) {
  throw ValidationError("契約日は平日を指定してください");
}
```

---

## Email/URL Validations

### Pattern 1: Email Format

**検証ルール**:
```
email: RFC 5322準拠
```

**正規表現** (簡略版):
```regex
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "email",
  "message": "有効なメールアドレスを入力してください",
  "value": "invalid-email"
}
```

### Pattern 2: URL Format

**検証ルール**:
```
websiteURL: http:// または https:// で始まる
```

**正規表現**:
```regex
^https?://[^\s]+$
```

**エラーレスポンス** (400 Bad Request):
```json
{
  "field": "websiteURL",
  "message": "有効なURLを入力してください（http:// または https:// で始まる必要があります）",
  "value": "example.com"
}
```

---

## Foreign Key Validations

### Pattern 1: Existence Check

**検証ルール**:
```
customerID: 存在する顧客IDへの参照
```

**APIバリデーション**:
```typescript
const customer = await db.customers.findById(customerID);
if (!customer) {
  throw NotFoundError("指定された顧客が存在しません");
}
```

**エラーレスポンス** (404 Not Found):
```json
{
  "type": "https://api.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "指定された顧客が存在しません",
  "field": "customerID",
  "value": 999
}
```

### Pattern 2: Soft Delete Consideration

**検証ルール**:
```
customerID: 存在し、かつ削除されていない顧客
```

**APIバリデーション**:
```typescript
const customer = await db.customers.findById(customerID);
if (!customer || customer.deletedAt) {
  throw NotFoundError("指定された顧客が存在しないか、削除されています");
}
```

### Pattern 3: Circular Reference Check

**検証ルール**:
```
managerID: 自分自身を参照しない（循環参照防止）
```

**APIバリデーション**:
```typescript
if (managerID === personID) {
  throw ValidationError("自分自身を上司として指定することはできません");
}
```

---

## Uniqueness Constraints

### Pattern 1: Simple Uniqueness

**検証ルール**:
```
email: ユニーク（重複不可）
```

**APIバリデーション**:
```typescript
const existing = await db.persons.findOne({ email });
if (existing && existing.id !== personID) {
  throw ConflictError("このメールアドレスは既に使用されています");
}
```

**エラーレスポンス** (409 Conflict):
```json
{
  "type": "https://api.example.com/errors/conflict",
  "title": "Resource Conflict",
  "status": 409,
  "detail": "このメールアドレスは既に使用されています",
  "field": "email",
  "value": "existing@example.com"
}
```

### Pattern 2: Composite Uniqueness

**検証ルール**:
```
(customerID, projectName): 同一顧客で同じプロジェクト名は不可
```

**APIバリデーション**:
```typescript
const existing = await db.projects.findOne({ customerID, projectName });
if (existing && existing.id !== projectID) {
  throw ConflictError("この顧客には既に同名のプロジェクトが存在します");
}
```

**エラーレスポンス** (409 Conflict):
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

## Business Rule Validations

### Pattern 1: State Transition

**検証ルール**:
```
ステータス遷移: PLANNING → IN_PROGRESS → COMPLETED
逆方向の遷移は不可
```

**APIバリデーション**:
```typescript
const allowedTransitions = {
  'PLANNING': ['IN_PROGRESS', 'CANCELLED'],
  'IN_PROGRESS': ['COMPLETED', 'CANCELLED'],
  'COMPLETED': [], // 完了後は変更不可
  'CANCELLED': []  // キャンセル後は変更不可
};

if (!allowedTransitions[currentStatus].includes(newStatus)) {
  throw BusinessRuleError(
    `${currentStatus} から ${newStatus} への遷移は許可されていません`
  );
}
```

**エラーレスポンス** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/business-rule-violation",
  "title": "Business Rule Violation",
  "status": 422,
  "detail": "COMPLETED から PLANNING への遷移は許可されていません",
  "currentStatus": "COMPLETED",
  "requestedStatus": "PLANNING"
}
```

### Pattern 2: Capacity Constraints

**検証ルール**:
```
プロジェクトの最大メンバー数: 20人
```

**APIバリデーション**:
```typescript
const currentMemberCount = await db.person_assign.count({ projectID });
if (currentMemberCount >= 20) {
  throw BusinessRuleError("プロジェクトの最大メンバー数（20人）に達しています");
}
```

### Pattern 3: Time-based Constraints

**検証ルール**:
```
プロジェクト開始後は契約金額の変更不可
```

**APIバリデーション**:
```typescript
const project = await db.projects.findById(projectID);
const hasStarted = await db.project_start.exists({ projectID });

if (hasStarted && contractAmount !== project.contractAmount) {
  throw BusinessRuleError("プロジェクト開始後は契約金額を変更できません");
}
```

**エラーレスポンス** (422 Unprocessable Entity):
```json
{
  "type": "https://api.example.com/errors/business-rule-violation",
  "title": "Business Rule Violation",
  "status": 422,
  "detail": "プロジェクト開始後は契約金額を変更できません",
  "projectID": 456,
  "hasStarted": true
}
```

### Pattern 4: Role-based Constraints

**検証ルール**:
```
プロジェクトマネージャーのみがプロジェクトを削除可能
```

**APIバリデーション**:
```typescript
const userRole = await getUserRole(requestingUserID, projectID);
if (userRole !== 'PM') {
  throw ForbiddenError("この操作にはプロジェクトマネージャー権限が必要です");
}
```

**エラーレスポンス** (403 Forbidden):
```json
{
  "type": "https://api.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "この操作にはプロジェクトマネージャー権限が必要です",
  "requiredRole": "PM",
  "userRole": "Engineer"
}
```

---

## Validation Summary Table

| バリデーション種別 | HTTPステータス | 例 |
|-----------------|--------------|---|
| 必須項目欠損 | 400 Bad Request | フィールド未入力 |
| 型不正 | 400 Bad Request | 文字列に数値が期待される |
| フォーマット不正 | 400 Bad Request | 日付形式エラー |
| 範囲外 | 400 Bad Request | 0-100の範囲外 |
| 存在しない参照 | 404 Not Found | 無効なcustomerID |
| 重複 | 409 Conflict | 既存のメールアドレス |
| ビジネスルール違反 | 422 Unprocessable Entity | 無効なステータス遷移 |
| 権限不足 | 403 Forbidden | 管理者のみ操作可能 |

---

## Best Practices

### 1. Early Validation

リクエスト受信後、ビジネスロジック実行前にバリデーション:

```typescript
// ✅ Good
async function createProject(data) {
  // 1. バリデーション
  validate(data);

  // 2. ビジネスロジック
  const project = await db.projects.create(data);

  return project;
}

// ❌ Bad
async function createProject(data) {
  // バリデーションなしで直接DB操作
  const project = await db.projects.create(data);
}
```

### 2. Detailed Error Messages

ユーザーにとって有用なエラーメッセージ:

```typescript
// ✅ Good
"プロジェクト名は1-200文字で入力してください"

// ❌ Bad
"Invalid input"
```

### 3. Field-Level Errors

複数のエラーをまとめて返却:

```json
{
  "errors": [
    {"field": "projectName", "message": "..."},
    {"field": "contractAmount", "message": "..."}
  ]
}
```

### 4. Client-Side Validation

サーバーサイドバリデーションを補完（ただし信用しない）:

```typescript
// フロントエンド: UXのため即座にエラー表示
// バックエンド: セキュリティのため必ず再検証
```

### 5. Validation Rules Documentation

OpenAPI仕様書にバリデーションルールを明記:

```yaml
projectName:
  type: string
  minLength: 1
  maxLength: 200
  example: "新システム開発"
  description: プロジェクト名（1-200文字）
```

---

## Anti-Patterns（避けるべきパターン）

### ❌ Avoid: Silent Failures

```typescript
// ❌ Bad: エラーを無視
if (!isValid(data)) {
  return null; // ユーザーに原因がわからない
}
```

**代わりに明示的なエラー**:

```typescript
// ✅ Good
if (!isValid(data)) {
  throw ValidationError("詳細なエラーメッセージ");
}
```

### ❌ Avoid: Generic Error Messages

```json
// ❌ Bad
{"error": "Validation failed"}
```

**代わりに具体的なエラー**:

```json
// ✅ Good
{
  "errors": [
    {"field": "projectName", "message": "1-200文字で入力してください"}
  ]
}
```

### ❌ Avoid: Client-Only Validation

```typescript
// ❌ Bad: フロントエンドだけでバリデーション
// 悪意のあるユーザーがバイパス可能
```

**必ずサーバーサイドでも検証**:

```typescript
// ✅ Good: サーバーサイドで必ず再検証
```
