---
name: ddl-generator
description: Generate PostgreSQL DDL, sample data, and query examples from immutable data model JSON. Use when the user asks to generate database schema, create sample data, or prepare SQL examples from a model.json in artifacts/{project-name}/ directory. Triggers include "DDLを生成", "サンプルデータを作って", "スキーマとデータを用意", or similar requests to transform a data model into executable SQL.
---

# DDL Generator

## Overview

Generate production-ready PostgreSQL DDL (schema.sql), realistic sample data (sample_data.sql), and practical query examples (query_examples.sql) from an immutable data model JSON file. This skill transforms a model.json into a complete, testable database implementation.

## Workflow

### 1. Locate the model.json

Read the model.json from `artifacts/{project-name}/model.json`:

```bash
Read: /path/to/artifacts/{project-name}/model.json
```

### 2. Generate schema.sql

Create `artifacts/{project-name}/schema.sql` following PostgreSQL best practices:

**File Structure:**
1. Header comment with generation date
2. Resource tables
3. Junction tables (for M:N relationships)
4. Event tables
5. Indexes for performance optimization

**Key Requirements:**
- Follow naming conventions from [postgresql-best-practices.md](references/postgresql-best-practices.md)
- Apply immutable model principles from [immutable-model-principles.md](references/immutable-model-principles.md)
- Add Japanese comments to all tables and columns
- Create indexes for foreign keys and datetime columns
- Use `GENERATED ALWAYS AS IDENTITY` for primary keys
- Set `ON DELETE RESTRICT` for foreign keys
- **カラム名はすべて小文字snake_caseを使用**

**Example Structure:**

```sql
-- ================================================
-- イミュータブルデータモデル DDL
-- {Project Name}
-- 生成日時: {Date}
-- ================================================

-- ================================================
-- リソーステーブル
-- ================================================

CREATE TABLE RESOURCE_NAME (
    resource_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE RESOURCE_NAME IS 'リソース名';
COMMENT ON COLUMN RESOURCE_NAME.resource_id IS 'リソースID';
-- ... more comments

-- ================================================
-- ジャンクションテーブル（多対多関係）
-- ================================================

CREATE TABLE JUNCTION_TABLE (
    resource_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (resource_id, tag_id),
    CONSTRAINT fk_junction_resource FOREIGN KEY (resource_id)
        REFERENCES RESOURCE_NAME(resource_id) ON DELETE RESTRICT
);

-- ================================================
-- イベントテーブル
-- ================================================

CREATE TABLE EVENT_NAME (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_id INTEGER NOT NULL,
    event_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_event_resource FOREIGN KEY (resource_id)
        REFERENCES RESOURCE_NAME(resource_id) ON DELETE RESTRICT
);

-- ================================================
-- インデックス（パフォーマンス最適化）
-- ================================================

CREATE INDEX idx_event_resource ON EVENT_NAME(resource_id);
CREATE INDEX idx_event_datetime ON EVENT_NAME(event_date_time);
```

For detailed rules, see [postgresql-best-practices.md](references/postgresql-best-practices.md).

### 3. Generate sample_data.sql

Create `artifacts/{project-name}/sample_data.sql` with realistic scenarios and edge cases:

**File Structure:**
1. Header comment
2. Master/lookup data
3. Resource data (3-5 records)
4. Junction data (tag associations)
5. Event data in chronological order (multiple scenarios)
6. Data summary comment

**Scenario Patterns:**

Design 2-4 scenarios that demonstrate:
- **Normal flow**: Standard business case
- **Edge case 1**: Multiple events (split payments, replacements)
- **Edge case 2**: State transitions (risk changes, status updates)
- **Edge case 3**: Complex relationships (hierarchies, reassignments)

**Example Structure:**

```sql
-- ================================================
-- サンプルデータINSERT
-- {Project Name}のデモ用データ
-- ================================================

-- ================================================
-- リソースデータ投入
-- ================================================

-- Master data
INSERT INTO MASTER_TABLE (name, ...) VALUES
('Item 1', ...),
('Item 2', ...);

-- Resource data
INSERT INTO RESOURCE_TABLE (name, ...) VALUES
('Resource A', ...),
('Resource B', ...);

-- Junction data (tags)
INSERT INTO JUNCTION_TABLE (resource_id, tag_id) VALUES
(1, 1), (1, 2), (2, 3);

-- ================================================
-- イベントデータ投入（時系列で発生したイベント）
-- ================================================

-- ========================================
-- シナリオ1: Normal flow
-- ========================================
INSERT INTO EVENT_START (...) VALUES ('2024-04-01 10:00:00+09', ...);
INSERT INTO EVENT_PROCESS (...) VALUES ('2024-04-15 14:00:00+09', ...);
INSERT INTO EVENT_COMPLETE (...) VALUES ('2024-04-30 17:00:00+09', ...);

-- ========================================
-- シナリオ2: Edge case with replacement
-- ========================================
INSERT INTO EVENT_ASSIGN (...) VALUES ('2024-05-01 10:00:00+09', ...);
INSERT INTO EVENT_REPLACE (...) VALUES ('2024-05-15 11:00:00+09', ...);

-- ================================================
-- データサマリー
-- ================================================
-- リソース: X件
-- イベント: Y件
-- 状態パターン:
--   ✅ Normal: ...
--   ⚠️ Edge case: ...
-- ================================================
```

For detailed patterns, see [sample-data-patterns.md](references/sample-data-patterns.md).

### 4. Generate query_examples.sql

Create `artifacts/{project-name}/query_examples.sql` with 8-12 practical queries:

**Query Types to Include:**

1. **Current state** - Latest status from events (using window functions)
2. **Event aggregation** - Summing/counting events per resource
3. **Event history** - Time-series tracking
4. **Replacement handling** - Excluding replaced records (using NOT EXISTS)
5. **Tag aggregation** - Multiple tags per resource (using STRING_AGG)
6. **Conditional aggregation** - Status breakdown (using CASE)
7. **Recursive CTE** - Hierarchical structures
8. **Timeline union** - All events combined (using UNION ALL)

**Example Structure:**

```sql
-- ================================================
-- イミュータブルデータモデル クエリ例集
-- {Project Name}
-- 複雑だけど強力！生成AIでサポート可能なクエリ集
-- ================================================

-- ================================================
-- 【クエリ1】Current state from events
-- イミュータブルモデルの特徴: イベントから現在の状態を集約
-- ================================================
WITH latest_event AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY resource_id ORDER BY event_date_time DESC) AS rn
    FROM EVENT_TABLE
)
SELECT * FROM latest_event WHERE rn = 1;

-- ================================================
-- 【クエリ2】Aggregation example
-- ================================================
SELECT
    r.resource_id,
    COUNT(e.event_id) AS event_count,
    SUM(e.amount) AS total_amount
FROM RESOURCE r
LEFT JOIN EVENT e ON r.resource_id = e.resource_id
GROUP BY r.resource_id;

-- ... 6-10 more queries
```

For comprehensive patterns, see [query-patterns.md](references/query-patterns.md).

## Reference Files

This skill includes detailed reference documentation:

- **[immutable-model-principles.md](references/immutable-model-principles.md)** - Design principles for immutable data models (resource/event/junction patterns, state calculation)
- **[postgresql-best-practices.md](references/postgresql-best-practices.md)** - DDL generation rules (naming, data types, constraints, indexes)
- **[sample-data-patterns.md](references/sample-data-patterns.md)** - Realistic scenario design and edge case patterns
- **[query-patterns.md](references/query-patterns.md)** - Immutable model query patterns (window functions, CTEs, aggregations)

Read these as needed during generation for detailed guidance.

## Output Files

After completion, the following files should exist in `artifacts/{project-name}/`:

- ✅ `schema.sql` - Complete PostgreSQL DDL
- ✅ `sample_data.sql` - Realistic sample data with scenarios
- ✅ `query_examples.sql` - 8-12 practical query examples

## Notes

- Always maintain chronological order in sample data events
- Include Japanese comments throughout for clarity
- Balance realism with demonstration of immutable model patterns
- Queries should showcase both practical use cases and advanced patterns
- **カラム名はすべて小文字snake_caseを使用（CamelCase禁止）**
