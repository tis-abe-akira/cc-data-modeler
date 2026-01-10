---
name: postgres-test
description: Automated PostgreSQL DB construction and SQL testing for immutable data models. Sets up PostgreSQL container with project-specific schema/data, executes all queries, and generates comprehensive test reports. Use when validating DDL generation results or testing query examples against real database. Triggers include "PostgreSQLで検証", "SQLをテスト", "クエリを実行", "データベースで動作確認", "DDLを検証".
---

# PostgreSQL DB Testing Skill

## Overview

Automate PostgreSQL database construction and SQL testing for immutable data model projects. This skill:
- Sets up isolated PostgreSQL containers per project
- Validates schema correctness (tables, constraints, indexes)
- Validates sample data integrity (row counts, FK relationships, chronological order)
- Executes all query examples automatically
- Generates comprehensive test reports in Markdown format

## Workflow

### Phase 0: Project Validation

**Objective**: Verify project exists and has required SQL files.

**Steps**:
1. Determine project name (from user input or context)
2. Verify `artifacts/{project-name}/` directory exists
3. Check for required files:
   - `schema.sql` - DDL definitions
   - `sample_data_relative.sql` - Sample data with relative dates
   - `query_examples.sql` - Query test suite

**If any file is missing**:
```
[エラー] 必須ファイルが見つかりません

プロジェクト: {project-name}
不足しているファイル:
- artifacts/{project-name}/schema.sql
- artifacts/{project-name}/sample_data_relative.sql
- artifacts/{project-name}/query_examples.sql

これらのファイルを生成してから再実行してください。
```

**Output**: Validated project path

---

### Phase 1: PostgreSQL Environment Setup

**Objective**: Create isolated PostgreSQL container with project-specific SQL files.

**Execute Python script**:
```bash
python .claude/skills/postgres-test/scripts/postgres_manager.py setup {project-name}
```

**Script operations**:
1. **Stop existing container** (if exists): `cc-data-modeler-postgres-{project}`
2. **Remove old container and volumes** (clean slate)
3. **Start new PostgreSQL 16 container**:
   ```bash
   docker run -d \
     --name cc-data-modeler-postgres-{project} \
     -e POSTGRES_USER=datamodeler \
     -e POSTGRES_PASSWORD=datamodeler123 \
     -e POSTGRES_DB=immutable_model_db \
     -e TZ='Asia/Tokyo' \
     -p 5432:5432 \
     -v {absolute_path}/artifacts/{project}/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql \
     -v {absolute_path}/artifacts/{project}/sample_data_relative.sql:/docker-entrypoint-initdb.d/02-sample_data.sql \
     postgres:16-alpine
   ```
4. **Wait for health check**: Poll `pg_isready` until ready (max 30 seconds)
5. **Verify connection**: Test database connection with simple query

**Success output**:
```
✅ PostgreSQL container started successfully
   Container: cc-data-modeler-postgres-{project}
   Database: immutable_model_db
   Port: 5432
   Status: Healthy
```

**Error handling**:
- Port 5432 occupied → Suggest stopping other containers
- Container startup timeout → Show container logs
- SQL file mount error → Verify file paths

**Output**: Connection parameters (host, port, database, credentials)

---

### Phase 2: Schema Validation

**Objective**: Verify DDL executed correctly and matches expectations.

**Execute validation queries**:

1. **Table count and list**:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

2. **Column count per table**:
```sql
SELECT table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;
```

3. **Foreign key constraints**:
```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

4. **Indexes**:
```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**Compare with model.json** (if available):
- Parse `artifacts/{project}/model.json`
- Extract expected entity count (resources + events + junctions)
- Compare expected vs actual table count
- Validate naming conventions (UPPER_SNAKE_CASE for tables)

**Validation results**:
```
### Schema Validation ✅

**Tables**: Expected 21, Actual 21 ✅
**Foreign Keys**: Expected 24, Actual 24 ✅
**Indexes**: Expected 32, Actual 32 ✅

| Table Name | Column Count | Status |
|------------|--------------|--------|
| PROJECT | 7 | ✅ |
| PERSON | 4 | ✅ |
| ORGANIZATION | 5 | ✅ |
...
```

**Output**: Schema validation section for report

---

### Phase 3: Data Validation

**Objective**: Verify sample data loaded correctly and maintains integrity.

**Execute validation queries**:

1. **Row counts per table**:
```sql
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

2. **Foreign key integrity check**:
```sql
-- For each FK constraint, verify all references are valid
-- Dynamically generated based on schema validation results
```

3. **Event chronological order check** (for immutable model):
```sql
-- For each event table with datetime attribute:
SELECT
    MIN({datetime_column}) as first_event,
    MAX({datetime_column}) as last_event,
    COUNT(*) as event_count
FROM {event_table};

-- Verify: first_event < last_event
```

4. **Relative date verification**:
```sql
-- Check that dates are relative to current date
SELECT
    table_name,
    column_name,
    MIN(column_value) as oldest_date,
    MAX(column_value) as newest_date
FROM (
    -- Dynamically query all TIMESTAMP columns
) date_columns;

-- Verify: dates span past to future from current date
```

**Validation results**:
```
### Data Validation ✅

**Row Counts**: All tables populated ✅
**FK Integrity**: All foreign keys valid ✅
**Chronological Order**: All events in correct time sequence ✅

| Table Name | Row Count | Status |
|------------|-----------|--------|
| INDUSTRY | 3 | ✅ |
| CUSTOMER | 3 | ✅ |
| PROJECT | 3 | ✅ |
| PROJECT_START | 3 | ✅ |
...
```

**Output**: Data validation section for report

---

### Phase 4: Query Execution

**Objective**: Execute all queries from `query_examples.sql` and capture results.

**Parse query_examples.sql**:
```python
# Use comment markers to identify queries:
# -- ================================================
# -- 【クエリN】Query Title
# -- Description
# -- ================================================
# SELECT ...

queries = parse_query_file('artifacts/{project}/query_examples.sql')
# Returns: [
#   {
#     "id": 1,
#     "title": "プロジェクト一覧と現在の状態",
#     "description": "イミュータブルモデルの特徴: イベントから現在の状態を集約",
#     "sql": "SELECT ...",
#     "line_number": 10
#   },
#   ...
# ]
```

**Execute each query**:
```python
for query in queries:
    start_time = time.time()
    try:
        result = execute_query(query['sql'], connection)
        execution_time = (time.time() - start_time) * 1000  # ms

        query_result = {
            'id': query['id'],
            'title': query['title'],
            'status': 'success',
            'execution_time_ms': execution_time,
            'row_count': len(result.rows),
            'sample_rows': result.rows[:5],  # First 5 rows
            'columns': result.column_names
        }
    except Exception as e:
        query_result = {
            'id': query['id'],
            'title': query['title'],
            'status': 'error',
            'error_message': str(e),
            'error_line': extract_error_line(e)
        }
```

**Continue on failure**: If a query fails, capture error and continue with next query.

**Query execution results**:
```
### Query 1: プロジェクト一覧と現在の状態 ✅
**Execution Time**: 12ms
**Rows Returned**: 3

**Sample Results** (first 5 rows):
| ProjectID | プロジェクト名 | 顧客名 | 状態 |
|-----------|---------------|--------|------|
| 1 | 次世代ECサイト構築 | 株式会社テックソリューション | 完了 |
| 2 | 勘定系システムリプレース | 金融太郎銀行 | 進行中 |
| 3 | 生産管理システム改修 | 製造花子工業株式会社 | 進行中 |

---

### Query 2: 現在の担当者一覧 ✅
**Execution Time**: 18ms
**Rows Returned**: 5
...
```

**Output**: Query execution results with timing, row counts, sample data

---

### Phase 5: Report Generation

**Objective**: Generate comprehensive Markdown test report.

**Execute report generator**:
```bash
python .claude/skills/postgres-test/scripts/report_generator.py \
    --results results.json \
    --project {project-name} \
    --output artifacts/{project-name}/test_report.md
```

**Report structure**:

```markdown
# PostgreSQL Test Report

**Project**: {project-name}
**Date**: {timestamp}
**Status**: ✅ PASS | ❌ FAIL
**Container**: cc-data-modeler-postgres-{project}

---

## Executive Summary

- Total Queries: {count}
- Successful: {success_count}
- Failed: {fail_count}
- Total Execution Time: {total_time}ms
- Average Query Time: {avg_time}ms

---

## 1. Schema Validation

[Schema validation section from Phase 2]

---

## 2. Data Validation

[Data validation section from Phase 3]

---

## 3. Query Execution Results

[Query results from Phase 4]

---

## 4. Performance Analysis

| Query ID | Title | Execution Time | Rows | Performance |
|----------|-------|----------------|------|-------------|
| 1 | プロジェクト一覧 | 12ms | 3 | ⚡ Fast |
| 2 | 現在の担当者 | 18ms | 5 | ⚡ Fast |
| 7 | 組織階層（再帰CTE） | 234ms | 8 | ⚠️ Slow |
...

**Performance Categories**:
- ⚡ Fast: < 50ms
- ✅ Normal: 50-100ms
- ⚠️ Slow: 100-500ms
- 🔴 Very Slow: > 500ms

**Slowest Queries**:
1. Query 7: 組織階層（再帰CTE） - 234ms
   - Recommendation: Add index on ORGANIZATION.ParentOrganizationID

---

## 5. Immutable Model Validation

### Event Sourcing Pattern ✅
- All events have datetime attributes
- No UPDATE statements detected in queries
- State calculated from event aggregation

### Resource/Event Separation ✅
- Resources: {resource_count} tables
- Events: {event_count} tables
- Junctions: {junction_count} tables

---

## Container Information

**Container**: cc-data-modeler-postgres-{project}
**Status**: Running
**Port**: 5432
**Database**: immutable_model_db
**User**: datamodeler

**To connect manually**:
```bash
docker exec -it cc-data-modeler-postgres-{project} psql -U datamodeler -d immutable_model_db
```

**To stop container**:
```bash
docker stop cc-data-modeler-postgres-{project}
docker rm cc-data-modeler-postgres-{project}
```

---

## Appendix: Test Environment

- PostgreSQL Version: 16 (Alpine)
- Test Date: {timestamp}
- Schema File: artifacts/{project}/schema.sql
- Data File: artifacts/{project}/sample_data_relative.sql
- Query File: artifacts/{project}/query_examples.sql
```

**Save report**:
- Primary: `artifacts/{project-name}/test_report.md`
- Display summary to user
- Prompt for cleanup action

**Output**: Test report file path

---

### Phase 6: Cleanup Prompt

**Ask user**:
```
テストが完了しました。

レポート: artifacts/{project-name}/test_report.md

PostgreSQLコンテナの処理:
1. コンテナを起動したままにする（手動で接続してクエリを試せます）
2. コンテナを停止して削除する

番号を入力してください（デフォルト: 1）:
```

**Option 1 (Keep running)**:
```
✅ コンテナを起動したままにしました。

接続情報:
  docker exec -it cc-data-modeler-postgres-{project} psql -U datamodeler -d immutable_model_db

停止する場合:
  docker stop cc-data-modeler-postgres-{project}
```

**Option 2 (Cleanup)**:
```bash
python .claude/skills/postgres-test/scripts/postgres_manager.py cleanup {project-name}
```

```
✅ コンテナを停止・削除しました。
```

---

## Error Handling

### Common Errors

**1. Port 5432 already in use**
```
[エラー] ポート5432が既に使用されています

解決方法:
1. 既存のPostgreSQLコンテナを停止する:
   docker ps | grep postgres
   docker stop {container_name}

2. または、別のポートを使用する（今後の機能）
```

**2. SQL syntax error in schema.sql**
```
[エラー] スキーマ実行中にエラーが発生しました

Line 45: syntax error at or near "INAVLID"
  CREATE TABLE INAVLID_TABLE ...
               ^

artifacts/{project}/schema.sql を確認してください。
```

**3. Container startup timeout**
```
[エラー] コンテナの起動がタイムアウトしました（30秒経過）

コンテナログ:
  docker logs cc-data-modeler-postgres-{project}

一般的な原因:
- メモリ不足
- ディスク容量不足
- Dockerデーモンが応答していない
```

**4. Query timeout**
```
[警告] クエリ{N}がタイムアウトしました（5分経過）

クエリ: {title}
SQL: {first_100_chars}...

このクエリをスキップして続行します。
```

---

## Reference Files

This skill includes detailed reference documentation:

- **[docker-operations.md](references/docker-operations.md)** - Docker container management patterns, volume mounting, health checks
- **[validation-patterns.md](references/validation-patterns.md)** - SQL validation query templates for schema and data verification
- **[troubleshooting.md](references/troubleshooting.md)** - Common issues and solutions for PostgreSQL testing

Read these as needed during testing for detailed guidance.

---

## Script Usage

### Manual Script Execution

If needed, scripts can be run independently:

**Setup container**:
```bash
cd .claude/skills/postgres-test/scripts
python postgres_manager.py setup project-record-system
```

**Run queries**:
```bash
python postgres_manager.py execute \
    --project project-record-system \
    --query-file artifacts/project-record-system/query_examples.sql
```

**Generate report**:
```bash
python report_generator.py \
    --results results.json \
    --project project-record-system \
    --output artifacts/project-record-system/test_report.md
```

**Cleanup**:
```bash
python postgres_manager.py cleanup project-record-system
```

---

## Multi-Project Support

Test multiple projects sequentially:
```bash
python postgres_manager.py test-all \
    --projects invoice-management,project-record-system
```

Each project gets its own container:
- `cc-data-modeler-postgres-invoice-management`
- `cc-data-modeler-postgres-project-record-system`

---

## Notes

- Always use `sample_data_relative.sql` (not `sample_data.sql`) for consistent relative date testing
- Container names are project-specific to allow parallel testing
- Reports are saved in each project's artifacts directory
- Query execution continues even if individual queries fail
- Performance analysis helps identify slow queries for optimization
