---
name: openapi-generator
description: OpenAPI仕様書自動生成スキル。イミュータブルデータモデル（model.json, entities_classified.json）から、CQRS準拠のOpenAPI 3.1.0仕様書を完全自動生成する。イベント→POST/PUT、リソース→GET、状態集約→GET のマッピング、Idempotency-Key ヘッダー、RFC 7807 準拠エラーレスポンスを含む。Use when: (1) Phase 6（DDL生成）完了後にPhase 7として実行, (2) model.json と entities_classified.json が存在, (3) ユースケース指向APIの仕様書が必要, (4) `/openapi-generator` コマンドで明示的に実行
---

# OpenAPI Generator Skill

このスキルは、イミュータブルデータモデルから**ユースケース指向のOpenAPI 3.1.0仕様書**を完全自動生成する。

## 目的

Phase 6（DDL生成）で作成されたデータモデルに対して：

1. **イベント→POST/PUT マッピング** - イベントエンティティを意味のあるアクションAPIに変換
2. **リソース→GET マッピング** - リソースエンティティを取得APIに変換
3. **状態集約→GET マッピング** - イベントから現在状態を推論するクエリAPI生成
4. **RFC 7807準拠エラー** - Problem Details 形式のエラーレスポンス定義
5. **Idempotency-Key** - 全POST/PUT操作に冪等性保証

## 重要な設計原則

**❌ 避けるもの**: 単純なCRUD API（バックエンドがDAOだけになる）

**✅ 目指すもの**: ユースケース指向API（実際の利用シーンに基づく）

- イベントエンティティ → 意味のあるPOST操作
  - 例: `ProjectStart` → `POST /api/projects/{id}/start`（プロジェクト開始アクション）
- リソースエンティティ → 状態取得のGET操作
  - 例: `Project` → `GET /api/projects/{id}/status`（現在の状態を集約）
- **CQRS パターン**: Command（POST/PUT）とQuery（GET）を明確に分離

## ワークフロー

### Step 1: プロジェクト検証

必須ファイルの確認:
- `artifacts/{project}/entities_classified.json` - エンティティ定義（必須）
- `artifacts/{project}/model.json` - モデル全体定義（必須）
- `artifacts/{project}/usecase_detailed.md` - 詳細ユースケース（オプション、利用可能なら活用）

プロジェクト名の取得:
- ユーザーから明示的に指定される場合: `/openapi-generator {project-name}`
- または既存ファイルから自動検出

### Step 2: エンティティ分析

`entities_classified.json` と `model.json` を読み込み、エンティティを分類:

```python
# エンティティ分類
resources = [e for e in entities if e['classification'] == 'resource']
events = [e for e in entities if e['classification'] == 'event']
junctions = [e for e in entities if e['classification'] == 'junction']

# 関連情報取得
relationships = parse_relationships(model_json)
```

参照: `scripts/openapi_generator.py` - メイン処理

### Step 3: API エンドポイント生成

#### 3.1 イベントエンティティ → POST/PUT エンドポイント

参照: `scripts/event_mapper.py`

イベントエンティティの命名パターンを解析し、適切なHTTPメソッドとエンドポイントを生成:

| イベント種別 | HTTPメソッド | エンドポイント例 | 説明 |
|------------|------------|----------------|------|
| `{Resource}Create` | POST | `/api/{resources}` | 新規作成 |
| `{Resource}Start` | POST | `/api/{resources}/{id}/start` | 開始アクション |
| `{Resource}Complete` | POST | `/api/{resources}/{id}/complete` | 完了アクション |
| `{Subject}Assign` | POST | `/api/{resources}/{id}/{subjects}` | 割当（追加） |
| `{Subject}Replace` | PUT | `/api/{resources}/{id}/{subjects}/{subjectId}/replace` | 置換（更新） |
| `{Action}Evaluate` | POST | `/api/{resources}/{id}/evaluations` | 評価登録 |

**変換ルール**: `references/event-naming-patterns.md` を参照

**Example**:

`ProjectStart` イベント:
```json
{
  "japanese": "プロジェクト開始",
  "english": "ProjectStart",
  "datetime_attribute": {
    "english": "StartDateTime",
    "type": "TIMESTAMP"
  },
  "attributes": [
    {"english": "EventID", "type": "INT", "is_primary_key": true},
    {"english": "ProjectID", "type": "INT"},
    {"english": "StartDateTime", "type": "TIMESTAMP"},
    {"english": "RegisteredBy", "type": "INT"}
  ]
}
```

**生成されるOpenAPI定義**:
```yaml
/api/projects/{projectId}/start:
  post:
    summary: プロジェクトを開始する
    operationId: startProject
    tags: [Projects]
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
        description: 冪等性キー（重複防止用UUID）
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
    security:
      - BearerAuth: []
```

**Command/Response スキーマ**:
```yaml
components:
  schemas:
    ProjectStartCommand:
      type: object
      required: [startDateTime, registeredBy]
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
        startDateTime:
          type: string
          format: date-time
        createdAt:
          type: string
          format: date-time
```

#### 3.2 リソースエンティティ → GET エンドポイント

参照: `scripts/resource_mapper.py`

リソースエンティティに対して、基本的なCRUD操作のエンドポイントを生成:

| 操作 | HTTPメソッド | エンドポイント | 説明 |
|-----|------------|--------------|------|
| 一覧取得 | GET | `/api/{resources}` | 検索・フィルタ・ページング |
| 詳細取得 | GET | `/api/{resources}/{id}` | 単一リソース |
| 作成 | POST | `/api/{resources}` | 新規作成 |
| 更新 | PUT/PATCH | `/api/{resources}/{id}` | 部分更新 |
| 削除 | DELETE | `/api/{resources}/{id}` | 論理削除 |

**検索・フィルタ・ページネーション**:

各リソースの属性に基づいて、自動的にクエリパラメータを生成:

```python
for attr in resource['attributes']:
    if attr['type'] in ['VARCHAR', 'TEXT']:
        # String属性 → 部分一致検索
        add_query_param(attr['english'], 'string', 'partial match')
    elif attr['type'] == 'INT' and attr['english'].endswith('ID'):
        # 外部キー属性 → 完全一致フィルタ
        add_query_param(attr['english'], 'integer', 'exact match')
    elif attr['type'] in ['DATE', 'TIMESTAMP']:
        # Date属性 → 範囲検索
        add_query_param(f"{attr['english']}From", 'date', 'range start')
        add_query_param(f"{attr['english']}To", 'date', 'range end')
```

**Example**:

`Project` リソース:
```yaml
/api/projects:
  get:
    summary: プロジェクト一覧を取得
    operationId: listProjects
    tags: [Projects]
    parameters:
      # String属性 → 部分一致検索
      - name: projectName
        in: query
        schema:
          type: string
        description: プロジェクト名（部分一致）

      # 外部キー属性 → 完全一致フィルタ
      - name: customerID
        in: query
        schema:
          type: integer
        description: 顧客IDでフィルタ

      # Date属性 → 範囲検索
      - name: plannedStartDateFrom
        in: query
        schema:
          type: string
          format: date
      - name: plannedStartDateTo
        in: query
        schema:
          type: string
          format: date

      # ページネーション
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
          maximum: 500
      - name: offset
        in: query
        schema:
          type: integer
          default: 0

      # ソート
      - name: sort
        in: query
        schema:
          type: string
          enum: [projectName, plannedStartDate, -projectName, -plannedStartDate]
          default: -createdAt
    responses:
      '200':
        description: プロジェクト一覧取得成功
        content:
          application/json:
            schema:
              type: object
              properties:
                total:
                  type: integer
                limit:
                  type: integer
                offset:
                  type: integer
                projects:
                  type: array
                  items:
                    $ref: '#/components/schemas/Project'
```

#### 3.3 状態集約クエリ → GET エンドポイント

参照: `scripts/state_aggregation_inferrer.py`

イベントテーブルから現在状態を推論するクエリAPIを自動生成:

##### パターン1: 最新状態取得

**検出条件**: イベントテーブルに datetime 属性がある

**SQL例**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = ?
ORDER BY StartDateTime DESC
LIMIT 1;
```

**生成API**:
```yaml
/api/projects/{projectId}/start/latest:
  get:
    summary: プロジェクトの最新開始情報を取得
    operationId: getProjectStartLatest
    tags: [Projects]
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: 最新開始情報取得成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectStartEvent'
      '404':
        $ref: '#/components/responses/NotFound'
```

##### パターン2: 履歴取得

**検出条件**: 同一リソースに対する複数イベント

**SQL例**:
```sql
SELECT * FROM PROJECT_START
WHERE ProjectID = ?
ORDER BY StartDateTime ASC;
```

**生成API**:
```yaml
/api/projects/{projectId}/start/history:
  get:
    summary: プロジェクト開始履歴を取得
    operationId: getProjectStartHistory
    tags: [Projects]
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
      - name: offset
        in: query
        schema:
          type: integer
          default: 0
    responses:
      '200':
        description: 開始履歴取得成功
        content:
          application/json:
            schema:
              type: object
              properties:
                total:
                  type: integer
                limit:
                  type: integer
                offset:
                  type: integer
                events:
                  type: array
                  items:
                    $ref: '#/components/schemas/ProjectStartEvent'
```

##### パターン3: 現在の割当（Replace考慮）

**検出条件**: `{Subject}Assign` と `{Subject}Replace` のペア

**SQL例**:
```sql
SELECT pa.*
FROM PERSON_ASSIGN pa
WHERE pa.ProjectID = ?
  AND NOT EXISTS (
    SELECT 1 FROM PERSON_REPLACE pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
  );
```

**生成API**:
```yaml
/api/projects/{projectId}/assignments/current:
  get:
    summary: プロジェクトの現在のアサイン状況を取得
    description: 置換済みのアサインを除外した現在のメンバー一覧
    operationId: getCurrentAssignments
    tags: [Projects]
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: 現在のアサイン状況取得成功
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/PersonAssignEvent'
```

##### パターン4: 集約サマリー

**検出条件**: 複数イベントから統計情報を算出

**SQL例**:
```sql
SELECT
  ProjectID,
  COUNT(*) as risk_count,
  MAX(EvaluatedAt) as latest_evaluation
FROM RISK_EVALUATE
WHERE ProjectID = ?
GROUP BY ProjectID;
```

**生成API**:
```yaml
/api/projects/{projectId}/risks/summary:
  get:
    summary: プロジェクトのリスク評価サマリーを取得
    operationId: getRiskSummary
    tags: [Projects]
    parameters:
      - name: projectId
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: リスク評価サマリー取得成功
        content:
          application/json:
            schema:
              type: object
              properties:
                projectID:
                  type: integer
                riskCount:
                  type: integer
                latestEvaluation:
                  type: string
                  format: date-time
```

### Step 4: エラーレスポンス定義

参照: `references/rfc7807-problem-details.md`

すべてのエンドポイントに RFC 7807 準拠のエラーレスポンスを追加:

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
              value:
                type: https://api.example.com/errors/validation-error
                title: Validation Error
                status: 400
                detail: プロジェクト名は1-200文字で入力してください
                errors:
                  - field: projectName
                    message: 1-200文字で入力してください
                    value: ""

    NotFound:
      description: リソースが見つからない
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            resourceNotFound:
              value:
                type: https://api.example.com/errors/not-found
                title: Resource Not Found
                status: 404
                detail: 指定されたプロジェクトが見つかりません

    Conflict:
      description: リソースの競合
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetails'
          examples:
            duplicateResource:
              value:
                type: https://api.example.com/errors/conflict
                title: Resource Conflict
                status: 409
                detail: 同じ顧客・プロジェクト名が既に存在します

  schemas:
    ProblemDetails:
      type: object
      required: [type, title, status]
      properties:
        type:
          type: string
          format: uri
          description: エラー種別を示すURI
        title:
          type: string
          description: エラーの概要
        status:
          type: integer
          description: HTTPステータスコード
        detail:
          type: string
          description: エラーの詳細説明
        instance:
          type: string
          format: uri
          description: エラーが発生したエンドポイント
        errors:
          type: array
          description: 詳細なバリデーションエラー
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string
              value:
                type: string
```

### Step 5: OpenAPI仕様書出力

完全なOpenAPI 3.1.0仕様書を `artifacts/{project}/openapi.yaml` に出力:

参照: `templates/openapi-base-template.yaml`

```yaml
openapi: 3.1.0
info:
  title: {project-name} API
  version: 1.0.0
  description: イミュータブルデータモデルに基づくRESTful API
servers:
  - url: https://api.example.com
    description: Production
  - url: https://api-staging.example.com
    description: Staging
paths:
  # 生成されたパス
  /api/projects:
    get: {...}
    post: {...}
  /api/projects/{projectId}:
    get: {...}
    put: {...}
    delete: {...}
  /api/projects/{projectId}/start:
    post: {...}
  # ...（全エンドポイント）
components:
  schemas:
    # 生成されたスキーマ
  responses:
    # 標準エラーレスポンス
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
security:
  - BearerAuth: []
```

### Step 6: 確認と出力

生成した OpenAPI 仕様書をユーザーに提示:

```
以下の内容で OpenAPI 仕様書を生成しました:

【統計】
- 総エンドポイント数: 52
  - POST: 15（イベント操作）
  - GET: 30（リソース取得 + 状態集約）
  - PUT: 5（置換操作）
  - DELETE: 2（削除操作）

- 定義されたスキーマ数: 45
  - Command: 15
  - Response: 20
  - Resource: 10

【主要エンドポイント】
- POST /api/projects/{id}/start - プロジェクト開始
- POST /api/projects/{id}/members - メンバーアサイン
- GET /api/projects/{id}/assignments/current - 現在のメンバー一覧
- GET /api/projects - プロジェクト一覧（検索・フィルタ対応）

artifacts/{project}/openapi.yaml に保存してよろしいですか？
1. はい、保存する
2. いいえ、プレビューする

番号を入力してください:
```

プレビューが選択された場合、主要なエンドポイントを表示。

承認後、ファイルに書き込み:

```
✅ OpenAPI 仕様書を生成しました: artifacts/{project}/openapi.yaml

【次のステップ】
1. Swagger UI で可視化:
   npx @redocly/cli preview-docs artifacts/{project}/openapi.yaml

2. バリデーション:
   npx @apidevtools/swagger-cli validate artifacts/{project}/openapi.yaml

3. Mock Server 起動:
   npx @stoplight/prism-cli mock artifacts/{project}/openapi.yaml

4. Phase 8（PostgreSQL検証）に進む:
   /postgres-test {project}
```

## 推奨される使い方

### パターン1: Phase 6完了後に自動実行（推奨）

```
Phase 6: DDL生成 → schema.sql, query_examples.sql 生成
    ↓
ユーザー確認: 「OpenAPI仕様書を生成しますか？」
    ↓
YES → /openapi-generator 自動実行
```

### パターン2: 明示的なコマンド実行

```bash
# プロジェクト名を指定
/openapi-generator project-record-system

# または現在のプロジェクトで実行
/openapi-generator
```

### パターン3: usecase_detailed.md との連携

詳細ユースケースが存在する場合、それを参照してエンドポイントの説明を豊富化:

```python
if os.path.exists(f'artifacts/{project}/usecase_detailed.md'):
    # ユースケースからエンドポイントの説明を抽出
    enrich_endpoint_descriptions(usecase_detailed)
```

## トラブルシューティング

### 必須ファイルが見つからない

```
[エラー] entities_classified.json が見つかりません

解決策:
1. Phase 1-2（エンティティ抽出・分類）を先に実行
2. プロジェクト名が正しいか確認
```

### イベント命名パターンが未対応

```
[警告] 未対応のイベント命名パターン: CustomerUpdate

対応:
- フォールバックとして POST /api/{resources}/{id}/events にマッピング
- または手動で openapi.yaml をカスタマイズ
```

参照: `references/event-naming-patterns.md` - サポートされるパターン一覧

### OpenAPI バリデーションエラー

```
[エラー] OpenAPI Validator で検証エラー

解決策:
1. 生成された openapi.yaml を確認
2. 手動で修正が必要な箇所を特定
3. Issue報告（パターンの追加提案）
```

## スクリプト実行

スキルは内部的にPythonスクリプトを使用。手動実行も可能:

### 環境セットアップ

```bash
cd .claude/skills/openapi-generator/scripts
pip install -r requirements.txt
```

### メインスクリプト実行

```bash
python openapi_generator.py {project-name}

# 出力: artifacts/{project-name}/openapi.yaml
```

### 個別モジュールのテスト

```bash
# イベントマッピングのみ
python event_mapper.py artifacts/project-record-system/entities_classified.json

# リソースマッピングのみ
python resource_mapper.py artifacts/project-record-system/entities_classified.json

# 状態集約推論のみ
python state_aggregation_inferrer.py artifacts/project-record-system/entities_classified.json
```

## 制限事項

1. **イベント命名パターン**: 限られたパターンのみサポート（Start, Complete, Assign, Replace, Evaluate）
2. **複雑なビジネスロジック**: 単純なCRUD以外の複雑なロジックは手動カスタマイズが必要
3. **状態集約の精度**: 基本的なパターン（latest/history/current/summary）のみ自動推論

## CQRS パターンについて

参照: `references/cqrs-patterns.md`

このスキルが生成するAPIは、CQRSパターンに従う:

- **Command（コマンド）**: 状態を変更する操作
  - POST, PUT, DELETE
  - イベントエンティティから生成
  - Idempotency-Key 必須

- **Query（クエリ）**: 状態を取得する操作
  - GET
  - リソースエンティティ + 状態集約クエリから生成
  - キャッシュ可能

## 参照

- `scripts/openapi_generator.py` - メイン処理
- `scripts/event_mapper.py` - イベント→API変換
- `scripts/resource_mapper.py` - リソース→API変換
- `scripts/state_aggregation_inferrer.py` - 状態集約推論
- `references/cqrs-patterns.md` - CQRSパターンガイド
- `references/event-naming-patterns.md` - イベント命名→エンドポイント変換ルール
- `references/rfc7807-problem-details.md` - RFC 7807 エラーレスポンス仕様
- `templates/openapi-base-template.yaml` - OpenAPI基本構造テンプレート
- `templates/common-components.yaml` - 共通コンポーネント

## 次のフェーズ

OpenAPI仕様書生成後:

1. **Swagger UI で可視化** - `npx @redocly/cli preview-docs`
2. **Mock Server 起動** - `npx @stoplight/prism-cli mock`
3. **Phase 8: PostgreSQL Verification** - `/postgres-test {project}`

---

**Note**: このスキルはPhase 7に位置し、データモデルからAPI仕様書への橋渡しを行う。生成された仕様書は、バックエンド実装とフロントエンド開発の両方で活用できる。
