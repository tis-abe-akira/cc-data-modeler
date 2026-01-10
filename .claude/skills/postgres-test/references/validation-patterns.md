# Validation Patterns Reference

SQL query templates for schema and data validation.

## Schema Validation Queries

### Table List and Types

```sql
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Expected output**:
- `table_name`: Table name (e.g., PROJECT, PERSON)
- `table_type`: BASE TABLE or VIEW

**Validation**:
- Count matches expected table count from model.json
- All table names follow UPPER_SNAKE_CASE convention

### Column Counts per Table

```sql
SELECT table_name, COUNT(*) as column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;
```

**Expected output**:
- Each table has at least 2 columns (ID + CreatedAt minimum)
- Resource tables typically have 3-10 columns
- Event tables typically have 4-15 columns

### Column Details

```sql
SELECT
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

**Validation**:
- Primary keys are NOT NULL
- All tables have CreatedAt (TIMESTAMP WITH TIME ZONE)
- VARCHAR columns have appropriate lengths

### Primary Key Constraints

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_name;
```

**Expected output**:
- Every table has exactly one primary key
- Primary key naming: `{TableName}_pkey`

### Foreign Key Constraints

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
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;
```

**Validation**:
- All {EntityName}ID columns have foreign keys (except for self-references)
- Foreign keys reference primary keys
- Naming convention: `{TableName}_{ColumnName}_fkey`

### Unique Constraints

```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'UNIQUE'
ORDER BY tc.table_name;
```

### Check Constraints

```sql
SELECT
    tc.constraint_name,
    tc.table_name,
    cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
  ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
ORDER BY tc.table_name;
```

### Index Listing

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**Expected indexes**:
- Primary key indexes (automatic)
- Foreign key indexes (for performance)
- Unique constraint indexes (automatic)

### Sequence Information

```sql
SELECT
    sequence_name,
    data_type,
    start_value,
    minimum_value,
    maximum_value,
    increment
FROM information_schema.sequences
WHERE sequence_schema = 'public'
ORDER BY sequence_name;
```

**Validation**:
- Each table with GENERATED ALWAYS AS IDENTITY has a sequence
- Naming: `{tablename}_{columnname}_seq`

## Data Validation Queries

### Row Counts (pg_stat_user_tables)

```sql
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Note**: `n_live_tup` is an estimate. For exact counts, use:

```sql
SELECT
    table_name,
    (xpath('/row/cnt/text()',
           query_to_xml(format('SELECT COUNT(*) as cnt FROM %I', table_name),
           false, true, '')))[1]::text::int as row_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Validation**:
- Resource tables have > 0 rows (master data)
- Event tables have > 0 rows (historical data)
- Junction tables may have 0 rows (optional relationships)

### Foreign Key Integrity Check

For each foreign key constraint, verify all references are valid:

```sql
-- Example: Check PROJECT.CustomerID references CUSTOMER
SELECT COUNT(*) as orphaned_records
FROM PROJECT p
LEFT JOIN CUSTOMER c ON p.CustomerID = c.CustomerID
WHERE p.CustomerID IS NOT NULL AND c.CustomerID IS NULL;
```

**Expected**: 0 orphaned records for all foreign keys

**Dynamic generation**:
```python
for fk in foreign_keys:
    query = f"""
        SELECT COUNT(*) as orphaned
        FROM {fk.table} t
        LEFT JOIN {fk.foreign_table} f ON t.{fk.column} = f.{fk.foreign_column}
        WHERE t.{fk.column} IS NOT NULL AND f.{fk.foreign_column} IS NULL;
    """
```

### Event Chronological Order Check

For each event table with a datetime attribute:

```sql
-- Example: Check PROJECT_START chronological order
SELECT
    ProjectID,
    MIN(StartDateTime) as first_event,
    MAX(StartDateTime) as last_event,
    COUNT(*) as event_count
FROM PROJECT_START
GROUP BY ProjectID
HAVING MIN(StartDateTime) >= MAX(StartDateTime);
```

**Expected**: 0 rows (no reverse chronology)

### Relative Date Verification

Check that sample data uses relative dates (past to future from current date):

```sql
-- Find all TIMESTAMP columns
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type LIKE '%timestamp%'
ORDER BY table_name, column_name;

-- For each timestamp column, check date range
-- Example: PROJECT.PlannedStartDate
SELECT
    MIN(PlannedStartDate) as oldest_date,
    MAX(PlannedStartDate) as newest_date,
    CURRENT_DATE as today,
    CASE
        WHEN MIN(PlannedStartDate) < CURRENT_DATE
         AND MAX(PlannedStartDate) > CURRENT_DATE
        THEN 'OK: Dates span past to future'
        ELSE 'WARNING: Dates do not span current date'
    END as validation
FROM PROJECT;
```

**Expected**: Dates span from past to future relative to execution time

### Null Value Analysis

Identify unexpected NULL values:

```sql
-- For each table, count NULLs in all columns
SELECT
    table_name,
    column_name,
    COUNT(*) - COUNT(column_name) as null_count,
    COUNT(*) as total_rows
FROM information_schema.columns c
JOIN (SELECT * FROM {table_name}) t ON true
WHERE table_schema = 'public'
GROUP BY table_name, column_name
HAVING COUNT(*) - COUNT(column_name) > 0
ORDER BY table_name, column_name;
```

**Validation**:
- Primary keys: 0 NULLs
- Required fields: 0 NULLs
- Optional foreign keys: NULLs acceptable

### Duplicate Detection

Check for unexpected duplicates:

```sql
-- Example: Detect duplicate PERSON emails
SELECT Email, COUNT(*) as count
FROM PERSON
GROUP BY Email
HAVING COUNT(*) > 1;
```

**Expected**: 0 rows (assuming email should be unique)

## Immutable Model-Specific Validation

### Event Table Identification

```sql
-- Find tables with datetime attributes (likely events)
SELECT DISTINCT table_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND data_type LIKE '%timestamp%'
  AND column_name NOT IN ('CreatedAt')
ORDER BY table_name;
```

**Validation**: These tables should be classified as "events" in model.json

### Resource Table Identification

```sql
-- Find tables without event-specific datetime columns
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name NOT IN (
      SELECT DISTINCT table_name
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND data_type LIKE '%timestamp%'
        AND column_name NOT IN ('CreatedAt')
  )
ORDER BY table_name;
```

**Validation**: These tables should be classified as "resources" in model.json

### Junction Table Identification

```sql
-- Find tables with multiple foreign keys (likely junctions)
SELECT
    tc.table_name,
    COUNT(*) as foreign_key_count
FROM information_schema.table_constraints AS tc
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
GROUP BY tc.table_name
HAVING COUNT(*) >= 2
ORDER BY foreign_key_count DESC, tc.table_name;
```

**Validation**: Multi-FK tables are typically junctions or events

### State Aggregation Pattern Check

Verify that event tables support state aggregation:

```sql
-- Example: Check if PROJECT can derive state from events
SELECT
    p.ProjectID,
    p.ProjectName,
    (SELECT COUNT(*) FROM PROJECT_START ps WHERE ps.ProjectID = p.ProjectID) as start_events,
    (SELECT COUNT(*) FROM PROJECT_COMPLETE pc WHERE pc.ProjectID = p.ProjectID) as complete_events
FROM PROJECT p;
```

**Expected pattern**:
- start_events ≥ 0 (projects may not have started)
- complete_events ∈ {0, 1} (projects complete at most once)

## Performance Validation

### Query Execution Plan Analysis

For slow queries, analyze execution plans:

```sql
EXPLAIN ANALYZE
SELECT * FROM PROJECT_START
WHERE StartDateTime > CURRENT_TIMESTAMP - INTERVAL '30 days';
```

**Key metrics**:
- Execution time
- Seq Scan vs Index Scan
- Rows processed

### Missing Index Detection

Find foreign keys without indexes:

```sql
SELECT
    tc.table_name,
    kcu.column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND NOT EXISTS (
      SELECT 1
      FROM pg_indexes idx
      WHERE idx.tablename = tc.table_name
        AND idx.indexdef LIKE '%' || kcu.column_name || '%'
  )
ORDER BY tc.table_name, kcu.column_name;
```

**Recommendation**: Add indexes to improve join performance

### Table Statistics

```sql
SELECT
    schemaname,
    tablename,
    n_live_tup as rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_analyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

## Validation Report Template

When generating validation reports, structure results as:

```markdown
### [Validation Category] [✅ PASS | ❌ FAIL]

**Summary**:
- Expected: [description]
- Actual: [result]
- Status: [PASS/FAIL]

**Details**:
[Table with specific validation results]

**Issues Found** (if any):
1. [Issue description]
   - Table: [table_name]
   - Details: [specific problem]
   - Recommendation: [how to fix]
```

## Best Practices

1. **Run validations in order**:
   - Schema → Data → Performance
   - Stop on critical failures (schema errors)

2. **Use transactions for read-only validation**:
   ```sql
   BEGIN;
   SET TRANSACTION READ ONLY;
   -- validation queries
   COMMIT;
   ```

3. **Capture timing for all queries**:
   ```python
   start = time.time()
   cursor.execute(query)
   duration = (time.time() - start) * 1000  # ms
   ```

4. **Compare against expectations**:
   - Parse model.json for expected counts
   - Validate naming conventions programmatically
   - Flag deviations as warnings or errors
