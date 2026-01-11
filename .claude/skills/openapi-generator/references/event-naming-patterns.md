# Event Naming Patterns Reference

イベントエンティティの命名パターンから、適切なAPIエンドポイントへの変換ルールをまとめたリファレンス。

## Table of Contents

1. [基本的な変換ルール](#基本的な変換ルール)
2. [Start パターン](#start-パターン)
3. [Complete/Finish パターン](#completefinish-パターン)
4. [Cancel/Abort パターン](#cancelabort-パターン)
5. [Assign パターン](#assign-パターン)
6. [Replace パターン](#replace-パターン)
7. [Evaluate/Assess パターン](#evaluateassess-パターン)
8. [Approve/Reject パターン](#approvereject-パターン)
9. [Create パターン](#create-パターン)
10. [Update パターン](#update-パターン)
11. [複合パターン](#複合パターン)
12. [カスタムパターン](#カスタムパターン)

---

## 基本的な変換ルール

### 命名規則

イベントエンティティは以下の命名規則に従う:

```
{Resource}{Action}
```

**例**:
- `ProjectStart` → `Project` (Resource) + `Start` (Action)
- `PersonAssign` → `Person` (Resource) + `Assign` (Action)
- `RiskEvaluate` → `Risk` (Resource) + `Evaluate` (Action)

### エンドポイント変換の基本形

```
{Resource}{Action} → POST /api/{resources}/{id}/{action}
```

**変換ステップ**:
1. Resource を複数形に変換（`Project` → `projects`）
2. Action を小文字に変換（`Start` → `start`）
3. リソースIDをパスパラメータに配置（`{id}`）

**例**:
```
ProjectStart → POST /api/projects/{id}/start
RiskEvaluate → POST /api/projects/{id}/risks
PersonAssign → POST /api/projects/{id}/members
```

### HTTPメソッドの選択

| アクション種別 | HTTPメソッド | 理由 |
|-------------|------------|------|
| 新規作成・追加 | POST | 新しいリソースの作成 |
| 置換・交代 | PUT | 既存リソースの置き換え |
| 部分更新 | PATCH | 既存リソースの一部変更 |
| 削除 | DELETE | リソースの削除（論理削除） |

イミュータブルデータモデルでは、ほとんどの操作がイベント記録（POST）か置換（PUT）になる。

---

## Start パターン

### パターン定義

**命名**: `{Resource}Start`

**意味**: リソースの開始・起動

**エンドポイント**: `POST /api/{resources}/{id}/start`

### 変換例

#### 例1: ProjectStart

**エンティティ**:
```json
{
  "japanese": "プロジェクト開始",
  "english": "ProjectStart",
  "classification": "event",
  "datetime_attribute": {
    "japanese": "開始日時",
    "english": "StartDateTime",
    "type": "TIMESTAMP"
  },
  "attributes": [
    {"japanese": "イベントID", "english": "EventID", "type": "INT", "is_primary_key": true},
    {"japanese": "プロジェクトID", "english": "ProjectID", "type": "INT"},
    {"japanese": "開始日時", "english": "StartDateTime", "type": "TIMESTAMP"},
    {"japanese": "登録者", "english": "RegisteredBy", "type": "INT"}
  ]
}
```

**生成されるエンドポイント**:
```yaml
/api/projects/{projectId}/start:
  post:
    summary: プロジェクトを開始する
    operationId: startProject
    tags:
      - Projects
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
        description: プロジェクトID
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
        description: 冪等性キー
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProjectStartCommand'
    responses:
      '201':
        description: プロジェクト開始成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectStartResponse'
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'

components:
  schemas:
    ProjectStartCommand:
      type: object
      required:
        - startDateTime
        - registeredBy
      properties:
        startDateTime:
          type: string
          format: date-time
          description: 開始日時
        registeredBy:
          type: integer
          description: 登録者のPersonID

    ProjectStartResponse:
      type: object
      properties:
        eventID:
          type: integer
          description: 生成されたイベントID
        projectID:
          type: integer
          description: プロジェクトID
        startDateTime:
          type: string
          format: date-time
          description: 開始日時
        createdAt:
          type: string
          format: date-time
          description: イベント記録日時
```

#### 例2: TaskStart

**エンティティ**: `TaskStart`

**エンドポイント**:
```yaml
POST /api/tasks/{taskId}/start
```

**Command Body**:
```json
{
  "startDateTime": "2026-01-15T09:00:00Z",
  "registeredBy": 5
}
```

### 状態集約クエリ

Start イベントに対して自動生成されるクエリAPI:

```yaml
# 最新の開始情報
GET /api/projects/{projectId}/start/latest

# 開始履歴
GET /api/projects/{projectId}/start/history
```

---

## Complete/Finish パターン

### パターン定義

**命名**: `{Resource}Complete` または `{Resource}Finish`

**意味**: リソースの完了・終了

**エンドポイント**: `POST /api/{resources}/{id}/complete`

### 変換例

#### 例1: ProjectComplete

**エンティティ**: `ProjectComplete`

**エンドポイント**:
```yaml
/api/projects/{projectId}/complete:
  post:
    summary: プロジェクトを完了する
    operationId: completeProject
    tags:
      - Projects
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - completeDateTime
              - registeredBy
            properties:
              completeDateTime:
                type: string
                format: date-time
                description: 完了日時
              registeredBy:
                type: integer
                description: 登録者のPersonID
              note:
                type: string
                description: 備考
    responses:
      '201':
        description: プロジェクト完了成功
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

#### 例2: TaskFinish

**エンティティ**: `TaskFinish`

**エンドポイント**:
```yaml
POST /api/tasks/{taskId}/finish
```

**Command Body**:
```json
{
  "finishDateTime": "2026-01-20T17:00:00Z",
  "registeredBy": 5,
  "result": "SUCCESS"
}
```

### 状態集約クエリ

```yaml
# 最新の完了情報
GET /api/projects/{projectId}/complete/latest

# 完了履歴
GET /api/projects/{projectId}/complete/history
```

---

## Cancel/Abort パターン

### パターン定義

**命名**: `{Resource}Cancel` または `{Resource}Abort`

**意味**: リソースのキャンセル・中止

**エンドポイント**: `POST /api/{resources}/{id}/cancel`

### 変換例

#### 例1: ProjectCancel

**エンティティ**: `ProjectCancel`

**エンドポイント**:
```yaml
/api/projects/{projectId}/cancel:
  post:
    summary: プロジェクトをキャンセルする
    operationId: cancelProject
    tags:
      - Projects
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - cancelDateTime
              - registeredBy
              - reason
            properties:
              cancelDateTime:
                type: string
                format: date-time
                description: キャンセル日時
              registeredBy:
                type: integer
                description: 登録者のPersonID
              reason:
                type: string
                description: キャンセル理由
    responses:
      '201':
        description: プロジェクトキャンセル成功
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

### ビジネスルール

Cancel イベントには通常、理由（reason）が必須:

```json
{
  "cancelDateTime": "2026-01-25T10:00:00Z",
  "registeredBy": 1,
  "reason": "顧客の予算削減により中止"
}
```

---

## Assign パターン

### パターン定義

**命名**: `{Subject}Assign` または `{Resource}{Subject}Assign`

**意味**: リソースへのサブジェクトの割当・追加

**エンドポイント**: `POST /api/{resources}/{id}/{subjects}`

### 変換例

#### 例1: PersonAssign

**エンティティ**:
```json
{
  "japanese": "人員アサイン",
  "english": "PersonAssign",
  "classification": "junction",
  "attributes": [
    {"japanese": "アサインID", "english": "AssignmentID", "type": "INT", "is_primary_key": true},
    {"japanese": "プロジェクトID", "english": "ProjectID", "type": "INT"},
    {"japanese": "人員ID", "english": "PersonID", "type": "INT"},
    {"japanese": "役割", "english": "Role", "type": "VARCHAR"},
    {"japanese": "アサイン日", "english": "AssignedDate", "type": "DATE"}
  ]
}
```

**エンドポイント変換**:
```
PersonAssign → POST /api/projects/{projectId}/members
```

**理由**:
- `Person` をリソースとして扱うのではなく、`Project` に対する `Person` の割当と解釈
- `members` は `Person` の複数形として意味的に適切

**生成されるエンドポイント**:
```yaml
/api/projects/{projectId}/members:
  post:
    summary: プロジェクトにメンバーをアサインする
    operationId: assignMemberToProject
    tags:
      - Projects
      - Members
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - personID
              - role
              - assignedDate
            properties:
              personID:
                type: integer
                description: アサインする人員のID
              role:
                type: string
                description: 役割（PM、Engineer、など）
              assignedDate:
                type: string
                format: date
                description: アサイン日
    responses:
      '201':
        description: メンバーアサイン成功
        content:
          application/json:
            schema:
              type: object
              properties:
                assignmentID:
                  type: integer
                  description: 生成されたアサインID
                projectID:
                  type: integer
                personID:
                  type: integer
                role:
                  type: string
                assignedDate:
                  type: string
                  format: date
                createdAt:
                  type: string
                  format: date-time
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

#### 例2: SkillAssign

**エンティティ**: `SkillAssign`

**解釈**: `Person` に `Skill` を割り当てる

**エンドポイント**:
```yaml
POST /api/persons/{personId}/skills
```

**Command Body**:
```json
{
  "skillID": 5,
  "level": "EXPERT",
  "acquiredDate": "2026-01-01"
}
```

### 状態集約クエリ

Assign イベントに対して自動生成されるクエリAPI:

```yaml
# 現在のアサイン状況（Replace を考慮）
GET /api/projects/{projectId}/members/current

# アサイン履歴
GET /api/projects/{projectId}/members/history
```

---

## Replace パターン

### パターン定義

**命名**: `{Subject}Replace` または `{Resource}{Subject}Replace`

**意味**: 既存の割当の置換・交代

**エンドポイント**: `PUT /api/{resources}/{id}/{subjects}/{subjectId}/replace`

### 変換例

#### 例1: PersonReplace

**エンティティ**:
```json
{
  "japanese": "人員交代",
  "english": "PersonReplace",
  "classification": "event",
  "attributes": [
    {"japanese": "交代ID", "english": "ReplacementID", "type": "INT", "is_primary_key": true},
    {"japanese": "プロジェクトID", "english": "ProjectID", "type": "INT"},
    {"japanese": "旧人員ID", "english": "OldPersonID", "type": "INT"},
    {"japanese": "新人員ID", "english": "NewPersonID", "type": "INT"},
    {"japanese": "交代日", "english": "ReplacedDate", "type": "DATE"},
    {"japanese": "理由", "english": "Reason", "type": "VARCHAR"}
  ]
}
```

**エンドポイント変換**:
```
PersonReplace → PUT /api/projects/{projectId}/members/{personId}/replace
```

**生成されるエンドポイント**:
```yaml
/api/projects/{projectId}/members/{personId}/replace:
  put:
    summary: プロジェクトのメンバーを交代させる
    operationId: replaceMemberInProject
    tags:
      - Projects
      - Members
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
        description: プロジェクトID
      - name: personId
        in: path
        required: true
        schema:
          type: integer
        description: 交代させる既存メンバーのPersonID
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - newPersonID
              - replacedDate
            properties:
              newPersonID:
                type: integer
                description: 新しいメンバーのPersonID
                nullable: true
              replacedDate:
                type: string
                format: date
                description: 交代日
              reason:
                type: string
                description: 交代理由
    responses:
      '201':
        description: メンバー交代成功
        content:
          application/json:
            schema:
              type: object
              properties:
                replacementID:
                  type: integer
                  description: 生成された交代ID
                projectID:
                  type: integer
                oldPersonID:
                  type: integer
                newPersonID:
                  type: integer
                  nullable: true
                replacedDate:
                  type: string
                  format: date
                createdAt:
                  type: string
                  format: date-time
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

**重要**: `newPersonID` は nullable（交代ではなく離脱の場合は null）

### 状態集約への影響

Replace イベントは、Assign の状態集約クエリに影響する:

```sql
-- 現在のメンバー（Replace で置換済みを除外）
SELECT pa.*
FROM PERSON_ASSIGN pa
WHERE pa.ProjectID = 456
  AND NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
  );
```

---

## Evaluate/Assess パターン

### パターン定義

**命名**: `{Resource}Evaluate` または `{Resource}Assess`

**意味**: リソースに対する評価・査定・判定

**エンドポイント**: `POST /api/{resources}/{id}/evaluations`

### 変換例

#### 例1: RiskEvaluate

**エンティティ**:
```json
{
  "japanese": "リスク評価",
  "english": "RiskEvaluate",
  "classification": "event",
  "datetime_attribute": {
    "japanese": "評価日時",
    "english": "EvaluatedAt",
    "type": "TIMESTAMP"
  },
  "attributes": [
    {"japanese": "評価ID", "english": "EvaluationID", "type": "INT", "is_primary_key": true},
    {"japanese": "プロジェクトID", "english": "ProjectID", "type": "INT"},
    {"japanese": "リスクレベル", "english": "RiskLevel", "type": "VARCHAR"},
    {"japanese": "説明", "english": "Description", "type": "TEXT"},
    {"japanese": "評価者", "english": "EvaluatedBy", "type": "INT"},
    {"japanese": "評価日時", "english": "EvaluatedAt", "type": "TIMESTAMP"}
  ]
}
```

**エンドポイント変換**:
```
RiskEvaluate → POST /api/projects/{projectId}/risks
```

**生成されるエンドポイント**:
```yaml
/api/projects/{projectId}/risks:
  post:
    summary: プロジェクトのリスクを評価する
    operationId: evaluateProjectRisk
    tags:
      - Projects
      - Risks
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - riskLevel
              - description
              - evaluatedBy
              - evaluatedAt
            properties:
              riskLevel:
                type: string
                enum: [LOW, MEDIUM, HIGH, CRITICAL]
                description: リスクレベル
              description:
                type: string
                description: リスクの説明
              evaluatedBy:
                type: integer
                description: 評価者のPersonID
              evaluatedAt:
                type: string
                format: date-time
                description: 評価日時
    responses:
      '201':
        description: リスク評価登録成功
        content:
          application/json:
            schema:
              type: object
              properties:
                evaluationID:
                  type: integer
                  description: 生成された評価ID
                projectID:
                  type: integer
                riskLevel:
                  type: string
                evaluatedAt:
                  type: string
                  format: date-time
                createdAt:
                  type: string
                  format: date-time
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
```

#### 例2: PerformanceAssess

**エンティティ**: `PerformanceAssess`

**エンドポイント**:
```yaml
POST /api/persons/{personId}/performances
```

**Command Body**:
```json
{
  "assessmentPeriod": "2026-Q1",
  "rating": "A",
  "comment": "優れたパフォーマンス",
  "assessedBy": 10,
  "assessedAt": "2026-04-01T10:00:00Z"
}
```

### 状態集約クエリ

Evaluate イベントに対して自動生成されるクエリAPI:

```yaml
# 最新の評価
GET /api/projects/{projectId}/risks/latest

# 評価履歴
GET /api/projects/{projectId}/risks/history

# 評価サマリー
GET /api/projects/{projectId}/risks/summary
```

**Summary レスポンス例**:
```json
{
  "projectID": 456,
  "riskCount": 15,
  "highRiskCount": 3,
  "criticalRiskCount": 1,
  "latestEvaluation": "2026-02-15T14:00:00Z"
}
```

---

## Approve/Reject パターン

### パターン定義

**命名**: `{Resource}Approve` または `{Resource}Reject`

**意味**: リソースの承認・却下

**エンドポイント**:
- `POST /api/{resources}/{id}/approve`
- `POST /api/{resources}/{id}/reject`

### 変換例

#### 例1: ProjectApprove

**エンティティ**: `ProjectApprove`

**エンドポイント**:
```yaml
/api/projects/{projectId}/approve:
  post:
    summary: プロジェクトを承認する
    operationId: approveProject
    tags:
      - Projects
      - Approvals
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - approvedBy
              - approvedAt
            properties:
              approvedBy:
                type: integer
                description: 承認者のPersonID
              approvedAt:
                type: string
                format: date-time
                description: 承認日時
              comment:
                type: string
                description: 承認コメント
    responses:
      '201':
        description: プロジェクト承認成功
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

#### 例2: ProjectReject

**エンティティ**: `ProjectReject`

**エンドポイント**:
```yaml
/api/projects/{projectId}/reject:
  post:
    summary: プロジェクトを却下する
    operationId: rejectProject
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - rejectedBy
              - rejectedAt
              - reason
            properties:
              rejectedBy:
                type: integer
                description: 却下者のPersonID
              rejectedAt:
                type: string
                format: date-time
                description: 却下日時
              reason:
                type: string
                description: 却下理由（必須）
    responses:
      '201':
        description: プロジェクト却下成功
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
```

**重要**: Reject には通常、理由（reason）が必須

---

## Create パターン

### パターン定義

**命名**: `{Resource}Create`

**意味**: リソースの新規作成

**エンドポイント**: `POST /api/{resources}`

### 変換例

#### 例1: ProjectCreate

**エンティティ**: `ProjectCreate`

**エンドポイント**:
```yaml
/api/projects:
  post:
    summary: 新しいプロジェクトを作成する
    operationId: createProject
    tags:
      - Projects
    parameters:
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - projectName
              - customerID
              - plannedStartDate
            properties:
              projectName:
                type: string
                minLength: 1
                maxLength: 200
                description: プロジェクト名
              customerID:
                type: integer
                description: 顧客ID
              plannedStartDate:
                type: string
                format: date
                description: 予定開始日
              contractAmount:
                type: integer
                minimum: 0
                description: 契約金額
              description:
                type: string
                maxLength: 500
                description: 説明
    responses:
      '201':
        description: プロジェクト作成成功
        content:
          application/json:
            schema:
              type: object
              properties:
                projectID:
                  type: integer
                  description: 生成されたプロジェクトID
                projectName:
                  type: string
                customerID:
                  type: integer
                createdAt:
                  type: string
                  format: date-time
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
      '409':
        $ref: '#/components/responses/Conflict'
```

**注意**: Create イベントは通常、リソーステーブル自体への挿入を意味する

---

## Update パターン

### パターン定義

**命名**: `{Resource}Update`

**意味**: リソースの部分更新

**エンドポイント**: `PATCH /api/{resources}/{id}`

### 変換例

#### 例1: ProjectUpdate

**エンティティ**: `ProjectUpdate`

**エンドポイント**:
```yaml
/api/projects/{projectId}:
  patch:
    summary: プロジェクト情報を部分更新する
    operationId: updateProject
    tags:
      - Projects
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: Idempotency-Key
        in: header
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              projectName:
                type: string
                minLength: 1
                maxLength: 200
              plannedStartDate:
                type: string
                format: date
              contractAmount:
                type: integer
                minimum: 0
              description:
                type: string
                maxLength: 500
            description: 更新したいフィールドのみ指定
    responses:
      '200':
        description: プロジェクト更新成功
        content:
          application/json:
            schema:
              type: object
              properties:
                projectID:
                  type: integer
                projectName:
                  type: string
                updatedAt:
                  type: string
                  format: date-time
      '400':
        $ref: '#/components/responses/BadRequest'
      '404':
        $ref: '#/components/responses/NotFound'
```

**注意**: イミュータブルデータモデルでは、Update イベントは慎重に扱う。可能な限り特定のアクションイベント（Start, Complete など）を使用する。

---

## 複合パターン

### パターン1: {Resource}{Action}{Target}

**例**: `ProjectMemberAdd`

**解釈**: `PersonAssign` と同等

**エンドポイント**:
```yaml
POST /api/projects/{projectId}/members
```

### パターン2: {Resource1}{Resource2}{Action}

**例**: `CustomerProjectCreate`

**解釈**: `Customer` に紐づく `Project` を作成

**エンドポイント**:
```yaml
POST /api/customers/{customerId}/projects
```

### パターン3: {Action}{Resource}

**例**: `RegisterProject`

**解釈**: `ProjectCreate` と同等

**エンドポイント**:
```yaml
POST /api/projects
```

---

## カスタムパターン

### 拡張可能な設計

イベント命名が標準パターンに合わない場合、カスタムマッピングルールを追加:

#### 例: ChangeRequest (変更要求)

**エンティティ**: `ChangeRequest`

**カスタムルール**:
```python
if event_name.startswith("Change"):
    action = "change-requests"
    method = "POST"
    path = f"/api/{resource_plural}/{id}/{action}"
```

**生成エンドポイント**:
```yaml
POST /api/projects/{projectId}/change-requests
```

#### 例: StatusTransition (状態遷移)

**エンティティ**: `StatusTransition`

**カスタムルール**:
```python
if event_name.endswith("Transition"):
    method = "PATCH"
    path = f"/api/{resource_plural}/{id}/status"
```

**生成エンドポイント**:
```yaml
PATCH /api/projects/{projectId}/status
```

### フォールバックルール

標準パターンに一致しない場合のデフォルト:

```yaml
POST /api/{resources}/{id}/events
```

**Request Body**:
```json
{
  "eventType": "CustomEventName",
  "eventData": { ... }
}
```

---

## パターンマッチング優先順位

複数のパターンが当てはまる場合、以下の優先順位で適用:

1. **Assign/Replace** - ジャンクション操作
2. **Start/Complete/Cancel** - ライフサイクル操作
3. **Approve/Reject** - 承認操作
4. **Evaluate/Assess** - 評価操作
5. **Create/Update** - CRUD操作
6. **カスタムルール** - プロジェクト固有
7. **フォールバック** - 汎用イベントエンドポイント

---

## ベストプラクティス

### ✅ DO: 意味的に適切なパスを選択

```yaml
✅ PersonAssign → POST /api/projects/{id}/members
   (プロジェクトに人をアサインする、という意図が明確)

❌ PersonAssign → POST /api/persons/{id}/assignments
   (人に何かをアサインする、と誤解される)
```

### ✅ DO: 複数形を適切に使用

```yaml
✅ POST /api/projects/{id}/members   (複数のメンバーがいる)
✅ POST /api/projects/{id}/risks     (複数のリスクがある)
✅ GET /api/projects/{id}/members/current  (現在のメンバー一覧)
```

### ✅ DO: Idempotency-Key を全イベントに適用

```yaml
POST /api/projects/{id}/start
PUT /api/projects/{id}/members/{memberId}/replace
POST /api/projects/{id}/risks

全てに Idempotency-Key ヘッダーが必須
```

### ❌ DON'T: 深いネスト

```yaml
❌ /api/customers/123/projects/456/members/789/skills/1
   (5階層は深すぎる)

✅ /api/members/789/skills/1
   (直接アクセス)
```

### ✅ DO: リソース指向の設計

```yaml
✅ POST /api/projects/{id}/start      (プロジェクトを開始)
✅ POST /api/projects/{id}/members    (メンバーを追加)

❌ POST /api/startProject             (RPC スタイル、避ける)
❌ POST /api/addMemberToProject       (RPC スタイル、避ける)
```

---

## まとめ

### イベント命名 → API エンドポイント変換フロー

1. **イベント名をパース**: `{Resource}{Action}` に分解
2. **パターンマッチング**: Start, Assign, Replace, Evaluate などのパターンに一致するか確認
3. **エンドポイント生成**: パターンに応じた適切なHTTPメソッドとパスを生成
4. **スキーマ生成**: Command/Response スキーマを attributes から自動生成
5. **Idempotency-Key 追加**: 全POST/PUTに必須ヘッダーを追加
6. **エラーレスポンス定義**: RFC 7807 準拠のエラー定義を追加

### 変換例サマリー

| イベント名 | パターン | HTTPメソッド | エンドポイント |
|----------|---------|------------|--------------|
| ProjectStart | Start | POST | /api/projects/{id}/start |
| ProjectComplete | Complete | POST | /api/projects/{id}/complete |
| ProjectCancel | Cancel | POST | /api/projects/{id}/cancel |
| PersonAssign | Assign | POST | /api/projects/{id}/members |
| PersonReplace | Replace | PUT | /api/projects/{id}/members/{memberId}/replace |
| RiskEvaluate | Evaluate | POST | /api/projects/{id}/risks |
| ProjectApprove | Approve | POST | /api/projects/{id}/approve |
| ProjectReject | Reject | POST | /api/projects/{id}/reject |
| ProjectCreate | Create | POST | /api/projects |
| ProjectUpdate | Update | PATCH | /api/projects/{id} |
