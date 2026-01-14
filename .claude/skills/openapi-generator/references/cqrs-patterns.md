# CQRS Patterns Reference

CQRS（Command Query Responsibility Segregation）パターンに基づくAPI設計のリファレンス。

## Table of Contents

1. [CQRS の基本原則](#cqrs-の基本原則)
2. [Command Operations (Write)](#command-operations-write)
3. [Query Operations (Read)](#query-operations-read)
4. [イミュータブルデータモデルとの統合](#イミュータブルデータモデルとの統合)
5. [Idempotency パターン](#idempotency-パターン)
6. [State Aggregation パターン](#state-aggregation-パターン)

---

## CQRS の基本原則

### コア概念

**CQRS** = Command Query Responsibility Segregation（コマンドクエリ責務分離）

- **Command（コマンド）**: システムの状態を変更する操作
- **Query（クエリ）**: システムの状態を取得する操作（変更しない）

### なぜ CQRS？

従来のCRUD APIの問題点:
```
❌ POST /api/projects     → 「作成」という意味しか伝わらない
❌ PUT /api/projects/123  → 「更新」だが、何の更新？
❌ バックエンドがDAOだけになる（ビジネスロジックが薄い）
```

CQRS APIの利点:
```
✅ POST /api/projects/123/start    → 「プロジェクト開始」という意図が明確
✅ POST /api/projects/123/complete → 「プロジェクト完了」という意図が明確
✅ ビジネスイベントがAPIに反映される
✅ イベントソーシングと相性が良い
```

### CQRS の基本ルール

| 種別 | HTTPメソッド | 用途 | 副作用 | 例 |
|-----|------------|------|-------|-----|
| **Command** | POST, PUT | 状態変更 | あり | イベント記録、リソース作成 |
| **Query** | GET | 状態取得 | なし | データ検索、集約計算 |

**重要**: DELETEは使用しない（イミュータブルデータモデルでは論理削除）

---

## Command Operations (Write)

### Command の種類

#### 1. Resource Creation（リソース作成）

**パターン**: 新しいリソースの作成

```
POST /api/{resources}
```

**例**:
```yaml
POST /api/customers
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

{
  "customerName": "株式会社サンプル",
  "industryID": 1
}

Response: 201 Created
{
  "customerID": 123,
  "customerName": "株式会社サンプル",
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**データモデル**: `CUSTOMER` テーブルへの INSERT

#### 2. Action Events（アクションイベント）

**パターン**: リソースに対するビジネスアクション

```
POST /api/{resources}/{id}/{action}
```

**例**:
```yaml
POST /api/projects/456/start
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440001

{
  "startDateTime": "2026-02-01T09:00:00Z",
  "registeredBy": 1
}

Response: 201 Created
{
  "eventID": 789,
  "projectID": 456,
  "startDateTime": "2026-02-01T09:00:00Z",
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**データモデル**: `PROJECT_START` イベントテーブルへの INSERT

**重要**: これは単なるUPDATEではなく、**イベントの記録**

#### 3. Assignment Operations（割当操作）

**パターン**: リソースへのサブジェクト割当

```
POST /api/{resources}/{id}/{subjects}
```

**例**:
```yaml
POST /api/projects/456/members
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440002

{
  "personID": 3,
  "role": "Engineer",
  "assignedDate": "2026-02-01"
}

Response: 201 Created
{
  "assignmentID": 10,
  "projectID": 456,
  "personID": 3,
  "role": "Engineer",
  "assignedDate": "2026-02-01",
  "createdAt": "2026-01-11T10:30:00Z"
}
```

**データモデル**: `PERSON_ASSIGN` ジャンクションテーブルへの INSERT

#### 4. Replacement Operations（置換操作）

**パターン**: 既存の割当の置換

```
PUT /api/{resources}/{id}/{subjects}/{subjectId}/replace
```

**例**:
```yaml
PUT /api/projects/456/members/3/replace
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440003

{
  "newPersonID": 5,
  "replacedDate": "2026-03-01",
  "reason": "プロジェクト異動"
}

Response: 201 Created
{
  "replacementID": 20,
  "projectID": 456,
  "oldPersonID": 3,
  "newPersonID": 5,
  "replacedDate": "2026-03-01",
  "createdAt": "2026-01-11T11:00:00Z"
}
```

**データモデル**: `PERSON_REPLACE` イベントテーブルへの INSERT

**重要**: 古いレコードは削除せず、置換イベントを記録

#### 5. Evaluation Operations（評価操作）

**パターン**: リソースに対する評価・査定

```
POST /api/{resources}/{id}/evaluations
```

**例**:
```yaml
POST /api/projects/456/risks
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440004

{
  "riskLevel": "HIGH",
  "description": "スケジュール遅延のリスク",
  "evaluatedBy": 1,
  "evaluatedAt": "2026-02-15T14:00:00Z"
}

Response: 201 Created
{
  "evaluationID": 30,
  "projectID": 456,
  "riskLevel": "HIGH",
  "evaluatedAt": "2026-02-15T14:00:00Z"
}
```

**データモデル**: `RISK_EVALUATE` イベントテーブルへの INSERT

### Command の設計原則

#### ✅ DO: ビジネスの意図を反映

```yaml
POST /api/projects/456/start      # 「開始する」という意図が明確
POST /api/projects/456/complete   # 「完了する」という意図が明確
POST /api/projects/456/cancel     # 「キャンセルする」という意図が明確
```

#### ❌ DON'T: 単純なCRUD動詞

```yaml
PUT /api/projects/456             # 「更新」だが、何の更新？意図不明
PATCH /api/projects/456/status    # 「ステータス変更」だが、どんな変更？
```

#### ✅ DO: Idempotency-Key を必須化

```yaml
POST /api/projects/456/start
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000  # UUID必須
```

理由: ネットワーク障害時のリトライで重複イベントを防ぐ

#### ✅ DO: Command Body に意図を含める

```yaml
{
  "startDateTime": "2026-02-01T09:00:00Z",  # いつ開始したか
  "registeredBy": 1,                        # 誰が記録したか
  "note": "顧客との契約締結済み"              # なぜ開始したか
}
```

#### ❌ DON'T: 副作用のあるGET

```yaml
❌ GET /api/projects/456/start   # GETで状態変更は禁止
```

---

## Query Operations (Read)

### Query の種類

#### 1. List Queries（一覧取得）

**パターン**: リソースの一覧を取得

```
GET /api/{resources}
```

**例**:
```yaml
GET /api/projects?customerID=123&status=IN_PROGRESS&limit=50&offset=0&sort=-createdAt

Response: 200 OK
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "projects": [
    {"projectID": 456, "projectName": "新システム開発", "status": "IN_PROGRESS"},
    {"projectID": 457, "projectName": "インフラ刷新", "status": "IN_PROGRESS"}
  ]
}
```

**データモデル**: `PROJECT` テーブルからの SELECT

#### 2. Detail Queries（詳細取得）

**パターン**: 単一リソースの詳細を取得

```
GET /api/{resources}/{id}
```

**例**:
```yaml
GET /api/projects/456

Response: 200 OK
{
  "projectID": 456,
  "projectName": "新システム開発",
  "customer": {"customerID": 123, "customerName": "株式会社サンプル"},
  "status": "IN_PROGRESS",
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**データモデル**: `PROJECT` テーブルと関連テーブルのJOIN

#### 3. State Aggregation Queries（状態集約クエリ）

**パターン**: イベントから現在の状態を集約

##### Pattern A: Latest State（最新状態）

```
GET /api/{resources}/{id}/{event-type}/latest
```

**例**:
```yaml
GET /api/projects/456/start/latest

Response: 200 OK
{
  "eventID": 789,
  "projectID": 456,
  "startDateTime": "2026-02-01T09:00:00Z",
  "registeredBy": 1,
  "createdAt": "2026-01-11T10:00:00Z"
}
```

**SQL**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = 456
ORDER BY StartDateTime DESC
LIMIT 1;
```

##### Pattern B: History（履歴）

```
GET /api/{resources}/{id}/{event-type}/history
```

**例**:
```yaml
GET /api/projects/456/start/history?limit=10&offset=0

Response: 200 OK
{
  "total": 3,
  "events": [
    {"eventID": 789, "startDateTime": "2026-02-01T09:00:00Z"},
    {"eventID": 790, "startDateTime": "2026-02-10T09:00:00Z"},
    {"eventID": 791, "startDateTime": "2026-02-20T09:00:00Z"}
  ]
}
```

**SQL**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = 456
ORDER BY StartDateTime ASC;
```

##### Pattern C: Current Assignments（現在の割当）

```
GET /api/{resources}/{id}/{subjects}/current
```

**例**:
```yaml
GET /api/projects/456/members/current

Response: 200 OK
{
  "projectID": 456,
  "currentMembers": [
    {"personID": 3, "personName": "山田太郎", "role": "PM", "assignedDate": "2026-02-01"},
    {"personID": 5, "personName": "佐藤花子", "role": "Engineer", "assignedDate": "2026-03-01"}
  ]
}
```

**SQL**:
```sql
SELECT pa.*, p.PersonName
FROM PERSON_ASSIGN pa
JOIN PERSON p ON pa.PersonID = p.PersonID
WHERE pa.ProjectID = 456
  AND NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
  );
```

**重要**: `PERSON_REPLACE` で置換されていないアサインのみ取得

##### Pattern D: Summary（サマリー集約）

```
GET /api/{resources}/{id}/{event-type}/summary
```

**例**:
```yaml
GET /api/projects/456/risks/summary

Response: 200 OK
{
  "projectID": 456,
  "riskCount": 15,
  "highRiskCount": 3,
  "latestEvaluation": "2026-02-15T14:00:00Z"
}
```

**SQL**:
```sql
SELECT
  ProjectID,
  COUNT(*) as riskCount,
  SUM(CASE WHEN RiskLevel = 'HIGH' THEN 1 ELSE 0 END) as highRiskCount,
  MAX(EvaluatedAt) as latestEvaluation
FROM RISK_EVALUATE
WHERE ProjectID = 456
GROUP BY ProjectID;
```

#### 4. Search Queries（検索クエリ）

**パターン**: 複雑な検索条件での取得

```
GET /api/{resources}/search
```

**例**:
```yaml
GET /api/projects/search?customerName=サンプル&plannedStartDateFrom=2026-01-01&plannedStartDateTo=2026-12-31

Response: 200 OK
{
  "total": 25,
  "projects": [...]
}
```

**データモデル**: 複数テーブルのJOINと複雑なWHERE句

### Query の設計原則

#### ✅ DO: 副作用なし（冪等）

```yaml
GET /api/projects/456    # 何度呼んでも同じ結果、状態変更なし
```

#### ✅ DO: クエリパラメータで検索条件

```yaml
GET /api/projects?customerID=123&status=IN_PROGRESS&limit=50
```

#### ✅ DO: ページネーション対応

```yaml
GET /api/projects?limit=50&offset=100

Response:
{
  "total": 500,
  "limit": 50,
  "offset": 100,
  "projects": [...]
}
```

#### ✅ DO: ソート指定可能

```yaml
GET /api/projects?sort=-createdAt,projectName
# -createdAt: 作成日時降順
# projectName: プロジェクト名昇順
```

#### ❌ DON'T: Request Body での検索

```yaml
❌ GET /api/projects
   Body: {"customerID": 123}  # GETにBodyは避ける
```

理由: GETのRequest Bodyはキャッシュやプロキシで問題になる可能性

代わりに:
```yaml
✅ POST /api/projects/search  # 複雑な検索条件の場合はPOSTを使う
   Body: {"customerID": 123, "filters": [...]}
```

---

## イミュータブルデータモデルとの統合

### エンティティ分類とAPIマッピング

| エンティティ分類 | 役割 | Command API | Query API |
|----------------|------|------------|-----------|
| **Resource** | 基本リソース | POST (作成) | GET (一覧・詳細) |
| **Event** | ビジネスイベント | POST (イベント記録) | GET (履歴・最新) |
| **Junction** | 多対多関連 | POST (割当), PUT (置換) | GET (現在の割当) |

### 例: プロジェクト管理システム

#### リソースエンティティ: PROJECT

```yaml
# Command: プロジェクト作成
POST /api/projects
Body: {"projectName": "新システム開発", "customerID": 123}

# Query: プロジェクト一覧
GET /api/projects

# Query: プロジェクト詳細
GET /api/projects/456
```

#### イベントエンティティ: PROJECT_START

```yaml
# Command: プロジェクト開始イベント記録
POST /api/projects/456/start
Body: {"startDateTime": "2026-02-01T09:00:00Z", "registeredBy": 1}

# Query: 最新の開始イベント
GET /api/projects/456/start/latest

# Query: 開始イベント履歴
GET /api/projects/456/start/history
```

#### ジャンクションエンティティ: PERSON_ASSIGN

```yaml
# Command: メンバーアサイン
POST /api/projects/456/members
Body: {"personID": 3, "role": "Engineer"}

# Query: 現在のアサイン状況
GET /api/projects/456/members/current
```

#### イベントエンティティ: PERSON_REPLACE

```yaml
# Command: メンバー交代
PUT /api/projects/456/members/3/replace
Body: {"newPersonID": 5, "replacedDate": "2026-03-01"}

# Query: 交代履歴
GET /api/projects/456/members/history
```

### イミュータブルの重要性

**❌ 避けるべき: DELETE操作**
```yaml
❌ DELETE /api/projects/456/members/3  # 物理削除
```

**✅ 推奨: イベントでの記録**
```yaml
✅ PUT /api/projects/456/members/3/replace
   Body: {"newPersonID": null, "replacedDate": "2026-03-01", "reason": "プロジェクト離脱"}
```

理由:
- 履歴が保存される
- 監査証跡が残る
- 状態の復元が可能
- イベントソーシングとの親和性

---

## Idempotency パターン

### なぜ Idempotency が必要？

**問題**: ネットワーク障害時のリトライで重複イベントが記録される

```
Client → POST /api/projects/456/start → Server ✓ (記録成功)
       ← (タイムアウト、レスポンス未受信)
Client → POST /api/projects/456/start → Server ✓ (重複記録)
```

結果: 同じ「プロジェクト開始」イベントが2回記録される

### 解決策: Idempotency-Key ヘッダー

```yaml
POST /api/projects/456/start
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "startDateTime": "2026-02-01T09:00:00Z",
  "registeredBy": 1
}
```

**サーバー側処理**:
```python
def handle_project_start(project_id, idempotency_key, body):
    # 1. Idempotency-Key で既存イベントを検索
    existing_event = db.query("SELECT * FROM PROJECT_START WHERE IdempotencyKey = ?", idempotency_key)

    if existing_event:
        # 2. 既に記録済み → 既存レスポンスを返す（重複防止）
        return 200, existing_event

    # 3. 新規イベント記録
    event_id = db.insert("PROJECT_START", {
        "ProjectID": project_id,
        "StartDateTime": body["startDateTime"],
        "RegisteredBy": body["registeredBy"],
        "IdempotencyKey": idempotency_key
    })

    return 201, {"eventID": event_id, ...}
```

**データモデル**:
```sql
CREATE TABLE PROJECT_START (
    EventID SERIAL PRIMARY KEY,
    ProjectID INT NOT NULL,
    StartDateTime TIMESTAMP NOT NULL,
    RegisteredBy INT NOT NULL,
    IdempotencyKey UUID UNIQUE NOT NULL,  -- UNIQUE制約で重複防止
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Idempotency のベストプラクティス

#### ✅ DO: 全POST/PUTに必須化

```yaml
POST /api/projects
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000  # 必須

POST /api/projects/456/start
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440001  # 必須

PUT /api/projects/456/members/3/replace
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440002  # 必須
```

#### ✅ DO: UUID v4 形式

```
550e8400-e29b-41d4-a716-446655440000  # UUID v4（ランダム）
```

#### ✅ DO: クライアント側で生成

```typescript
import { v4 as uuidv4 } from 'uuid';

async function startProject(projectId: number) {
    const idempotencyKey = uuidv4();

    const response = await fetch(`/api/projects/${projectId}/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
            startDateTime: new Date().toISOString(),
            registeredBy: 1
        })
    });

    // リトライ時も同じ idempotencyKey を使用
    if (response.status === 503) {
        await retryWithSameKey(projectId, idempotencyKey);
    }
}
```

#### ❌ DON'T: サーバー側で自動生成

```python
❌ idempotency_key = uuid.uuid4()  # サーバーで生成するとリトライ時に重複する
```

理由: クライアントがリトライする際、同じキーを使う必要がある

#### ✅ DO: 既存イベントの完全なレスポンス

```python
if existing_event:
    # 既存イベントの完全なデータを返す
    return 200, {
        "eventID": existing_event.event_id,
        "projectID": existing_event.project_id,
        "startDateTime": existing_event.start_date_time,
        "createdAt": existing_event.created_at
    }
```

#### ❌ DON'T: 409 Conflict を返す

```python
❌ if existing_event:
       return 409, {"error": "Duplicate request"}
```

理由: Idempotency の目的は「同じ操作を何度実行しても安全」であること

---

## State Aggregation パターン

### なぜ State Aggregation が必要？

イミュータブルデータモデルでは:
- イベントは追記のみ（更新・削除なし）
- 現在の状態はイベントから集約する必要がある

**例**: 「プロジェクトの現在のメンバー」を取得したい

```sql
-- ❌ 単純なSELECT（置換を考慮していない）
SELECT * FROM PERSON_ASSIGN WHERE ProjectID = 456;

-- ✅ 置換を考慮したSELECT
SELECT pa.*
FROM PERSON_ASSIGN pa
WHERE pa.ProjectID = 456
  AND NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
  );
```

### State Aggregation の4パターン

#### Pattern 1: Latest State（最新状態）

**用途**: イベントの最新の発生を取得

**API**:
```yaml
GET /api/projects/456/start/latest
```

**SQL**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = 456
ORDER BY StartDateTime DESC
LIMIT 1;
```

**使用例**:
- 「プロジェクトはいつ開始したか？」
- 「最新のリスク評価はいつか？」

#### Pattern 2: History（履歴）

**用途**: イベントの全履歴を時系列で取得

**API**:
```yaml
GET /api/projects/456/start/history?limit=10&offset=0
```

**SQL**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = 456
ORDER BY StartDateTime ASC
LIMIT 10 OFFSET 0;
```

**使用例**:
- 「プロジェクトの開始履歴を全て見たい」
- 「リスク評価の推移を確認したい」

#### Pattern 3: Current Assignments（現在の割当）

**用途**: 置換を考慮した現在のアサイン状況を取得

**API**:
```yaml
GET /api/projects/456/members/current
```

**SQL**:
```sql
SELECT pa.*, p.PersonName, p.Email
FROM PERSON_ASSIGN pa
JOIN PERSON p ON pa.PersonID = p.PersonID
WHERE pa.ProjectID = 456
  AND NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
  );
```

**重要ロジック**:
```
現在のメンバー = PERSON_ASSIGN - PERSON_REPLACE で置換済みのメンバー
```

**使用例**:
- 「このプロジェクトの現在のメンバーは誰か？」
- 「過去のメンバーを除外して現在のメンバーだけ表示したい」

#### Pattern 4: Summary（サマリー集約）

**用途**: イベントから統計情報を算出

**API**:
```yaml
GET /api/projects/456/risks/summary
```

**SQL**:
```sql
SELECT
  ProjectID,
  COUNT(*) as riskCount,
  SUM(CASE WHEN RiskLevel = 'HIGH' THEN 1 ELSE 0 END) as highRiskCount,
  AVG(CASE WHEN RiskLevel = 'HIGH' THEN 1 ELSE 0 END) as highRiskRatio,
  MAX(EvaluatedAt) as latestEvaluation,
  MIN(EvaluatedAt) as firstEvaluation
FROM RISK_EVALUATE
WHERE ProjectID = 456
GROUP BY ProjectID;
```

**使用例**:
- 「このプロジェクトのリスク評価は何回行われたか？」
- 「HIGH リスクの割合は？」
- 「最後にリスク評価したのはいつか？」

### State Aggregation のベストプラクティス

#### ✅ DO: 検索条件でパフォーマンス最適化

```sql
-- インデックス活用
CREATE INDEX idx_project_start_project_id_datetime
ON PROJECT_START (ProjectID, StartDateTime DESC);

-- クエリ
SELECT * FROM PROJECT_START
WHERE ProjectID = 456  -- インデックス使用
ORDER BY StartDateTime DESC
LIMIT 1;
```

#### ✅ DO: キャッシュ活用

```python
@cache(ttl=60)  # 60秒キャッシュ
def get_current_members(project_id):
    return db.query("""
        SELECT pa.*, p.PersonName
        FROM PERSON_ASSIGN pa
        JOIN PERSON p ON pa.PersonID = p.PersonID
        WHERE pa.ProjectID = ?
          AND NOT EXISTS (
            SELECT 1 FROM PERSON_REPLACE pr
            WHERE pr.ProjectID = pa.ProjectID
              AND pr.OldPersonID = pa.PersonID
          )
    """, project_id)
```

#### ✅ DO: マテリアライズドビュー（大量データ）

```sql
-- マテリアライズドビュー作成
CREATE MATERIALIZED VIEW project_current_members AS
SELECT pa.ProjectID, pa.PersonID, p.PersonName, pa.Role
FROM PERSON_ASSIGN pa
JOIN PERSON p ON pa.PersonID = p.PersonID
WHERE NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
);

-- 定期的にリフレッシュ
REFRESH MATERIALIZED VIEW project_current_members;

-- クエリ（高速）
SELECT * FROM project_current_members WHERE ProjectID = 456;
```

#### ❌ DON'T: N+1 クエリ

```python
❌ # 非効率（N+1問題）
projects = db.query("SELECT * FROM PROJECT")
for project in projects:
    members = db.query("SELECT * FROM PERSON_ASSIGN WHERE ProjectID = ?", project.id)
```

```python
✅ # 効率的（JOIN）
result = db.query("""
    SELECT p.*, pa.*
    FROM PROJECT p
    LEFT JOIN PERSON_ASSIGN pa ON p.ProjectID = pa.ProjectID
    WHERE NOT EXISTS (
        SELECT 1 FROM PERSON_REPLACE pr
        WHERE pr.ProjectID = pa.ProjectID
          AND pr.OldPersonID = pa.PersonID
    )
""")
```

---

## まとめ

### CQRS + イミュータブルデータモデルの利点

1. **ビジネスの意図が明確**: APIがビジネスイベントを反映
2. **監査証跡**: 全ての変更履歴が残る
3. **イベントソーシング**: 過去の任意の時点の状態を復元可能
4. **スケーラビリティ**: Read/Writeを独立してスケール可能
5. **Idempotency**: ネットワーク障害時も安全にリトライ可能

### API設計チェックリスト

#### Command API
- [ ] POST/PUT でビジネスアクションを表現
- [ ] Idempotency-Key ヘッダー必須
- [ ] イベントテーブルへの INSERT
- [ ] 201 Created レスポンス
- [ ] RFC 7807 エラーレスポンス

#### Query API
- [ ] GET で状態取得（副作用なし）
- [ ] ページネーション対応
- [ ] ソート指定可能
- [ ] State Aggregation パターン適用
- [ ] キャッシュ・インデックス最適化

### 参考資料

- [CQRS Pattern - Microsoft](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Event Sourcing - Martin Fowler](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Idempotency - Stripe API](https://stripe.com/docs/api/idempotent_requests)
- [RFC 7807 - Problem Details](https://tools.ietf.org/html/rfc7807)
