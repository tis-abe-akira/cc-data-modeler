# Troubleshooting Guide

Common issues and solutions for PostgreSQL testing.

## Container Issues

### Port 5432 Already in Use

**Symptoms**:
```
Error: port is already allocated
docker.errors.APIError: 500 Server Error: Internal Server Error
```

**Cause**: Another PostgreSQL container or service is using port 5432

**Solution**:
```bash
# 1. Find the conflicting container/service
docker ps | grep 5432
lsof -i :5432

# 2. Stop the conflicting container
docker stop <container_name>

# 3. Or stop local PostgreSQL service
sudo systemctl stop postgresql  # Linux
brew services stop postgresql   # macOS

# 4. Retry setup
python postgres_manager.py setup <project-name>
```

**Prevention**: Use project-specific container names and automatic cleanup

### Container Starts But Health Check Fails

**Symptoms**:
```
⏳ Waiting for PostgreSQL to be ready (max 30s)...
[エラー] Health check timeout (30s)
```

**Cause**: PostgreSQL initialization taking longer than expected

**Diagnosis**:
```bash
# Check container status
docker ps -a | grep cc-data-modeler-postgres

# View logs
docker logs cc-data-modeler-postgres-<project>

# Check if container is running
docker inspect cc-data-modeler-postgres-<project> | grep Status
```

**Common log patterns**:

1. **SQL syntax error**:
   ```
   ERROR: syntax error at or near "INAVLID"
   LINE 45: CREATE TABLE INAVLID_TABLE
   ```
   **Fix**: Correct schema.sql syntax error at indicated line

2. **File permission error**:
   ```
   permission denied while trying to read /docker-entrypoint-initdb.d/01-schema.sql
   ```
   **Fix**: Check file permissions: `chmod 644 artifacts/<project>/schema.sql`

3. **Memory/disk issues**:
   ```
   could not fork new process for connection: Cannot allocate memory
   ```
   **Fix**: Increase Docker memory limits or free up disk space

**Solution for slow initialization**:
- Increase timeout: Modify `_wait_for_health()` timeout parameter
- Simplify schema: Split large SQL files
- Reduce sample data: Use smaller dataset for testing

### Container Exists But Won't Start

**Symptoms**:
```
Error response from daemon: Conflict. The container name "/cc-data-modeler-postgres-<project>" is already in use
```

**Cause**: Previous container not properly cleaned up

**Solution**:
```bash
# Remove existing container
docker stop cc-data-modeler-postgres-<project>
docker rm cc-data-modeler-postgres-<project>

# Or use cleanup command
python postgres_manager.py cleanup <project>

# Retry setup
python postgres_manager.py setup <project>
```

### Image Not Found

**Symptoms**:
```
Error: No such image: postgres:16-alpine
```

**Cause**: PostgreSQL image not downloaded

**Solution**:
```bash
# Pull image manually
docker pull postgres:16-alpine

# Verify
docker images | grep postgres
```

## Connection Issues

### Connection Refused

**Symptoms**:
```python
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Diagnosis**:
```bash
# 1. Check if container is running
docker ps | grep cc-data-modeler-postgres

# 2. Check port binding
docker port cc-data-modeler-postgres-<project>

# 3. Test connection from container
docker exec cc-data-modeler-postgres-<project> pg_isready -U datamodeler
```

**Solutions**:

1. **Container not running**:
   ```bash
   docker start cc-data-modeler-postgres-<project>
   ```

2. **Port not exposed**:
   - Verify `-p 5432:5432` in container creation
   - Recreate container with correct port mapping

3. **PostgreSQL not ready**:
   - Wait longer for initialization
   - Check logs: `docker logs cc-data-modeler-postgres-<project>`

### Authentication Failed

**Symptoms**:
```python
psycopg2.OperationalError: FATAL: password authentication failed for user "datamodeler"
```

**Cause**: Incorrect credentials or environment variables

**Solution**:
```bash
# Check environment variables
docker exec cc-data-modeler-postgres-<project> env | grep POSTGRES

# Expected:
# POSTGRES_USER=datamodeler
# POSTGRES_PASSWORD=datamodeler123
# POSTGRES_DB=immutable_model_db

# If incorrect, recreate container with correct env vars
```

### Database Does Not Exist

**Symptoms**:
```python
psycopg2.OperationalError: FATAL: database "immutable_model_db" does not exist
```

**Cause**: Database not created during initialization

**Solution**:
```bash
# Connect to default database and create
docker exec -it cc-data-modeler-postgres-<project> psql -U datamodeler -d postgres -c "CREATE DATABASE immutable_model_db;"

# Or recreate container (ensures clean state)
python postgres_manager.py cleanup <project>
python postgres_manager.py setup <project>
```

## SQL Execution Issues

### Query Timeout

**Symptoms**:
```
Query execution exceeded 5 minute timeout
```

**Cause**: Complex query or missing indexes

**Solutions**:

1. **Add indexes**:
   ```sql
   CREATE INDEX idx_project_start_datetime ON PROJECT_START(StartDateTime);
   CREATE INDEX idx_person_assign_project ON PERSON_ASSIGN(ProjectID);
   ```

2. **Optimize query**:
   - Use EXPLAIN ANALYZE to identify bottlenecks
   - Add WHERE clauses to limit data
   - Consider materialized views for complex aggregations

3. **Increase timeout**:
   ```python
   conn = psycopg2.connect(..., connect_timeout=10)
   cursor.execute(query)
   cursor.execute("SET statement_timeout = '10min'")
   ```

### Syntax Error in Query

**Symptoms**:
```
psycopg2.errors.SyntaxError: syntax error at or near "..."
```

**Cause**: Invalid SQL syntax in query_examples.sql

**Solution**:
```bash
# Test query manually
docker exec -it cc-data-modeler-postgres-<project> psql -U datamodeler -d immutable_model_db

# Run problematic query
immutable_model_db=# SELECT * FROM PROJECT WHERE ...;

# Fix syntax in query_examples.sql
# Line numbers are reported in error messages
```

### Foreign Key Violation

**Symptoms**:
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "..." violates foreign key constraint
```

**Cause**: sample_data.sql inserts data in wrong order

**Solution**:
1. **Reorder inserts**: Insert parent tables before child tables
   ```sql
   -- Correct order:
   INSERT INTO CUSTOMER ...;  -- Parent
   INSERT INTO PROJECT ...;   -- Child (references CUSTOMER)
   ```

2. **Disable FK checks temporarily** (testing only):
   ```sql
   SET session_replication_role = 'replica';  -- Disable triggers/FKs
   -- Insert data
   SET session_replication_role = 'origin';   -- Re-enable
   ```

## File Issues

### Required Files Not Found

**Symptoms**:
```
[エラー] 必須ファイルが見つかりません

不足しているファイル:
- artifacts/<project>/schema.sql
- artifacts/<project>/sample_data_relative.sql
- artifacts/<project>/query_examples.sql
```

**Cause**: Project not fully generated

**Solution**:
```bash
# Run DDL generator skill first
# This creates all required files

# Verify files exist
ls -la artifacts/<project>/

# Expected files:
# - entities_classified.json
# - model.json
# - schema.sql
# - sample_data_relative.sql
# - query_examples.sql
```

### Volume Mount Path Issues

**Symptoms**:
```
Error response from daemon: invalid mount config for type "bind": bind source path does not exist
```

**Cause**: Relative path used instead of absolute path

**Solution**:
```python
# Wrong:
volume = './artifacts/project/schema.sql'

# Correct:
from pathlib import Path
volume = str(Path.cwd() / 'artifacts' / 'project' / 'schema.sql')

# Or:
import os
volume = os.path.abspath('./artifacts/project/schema.sql')
```

### File Encoding Issues

**Symptoms**:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Cause**: SQL files not saved as UTF-8

**Solution**:
```bash
# Check encoding
file -I artifacts/<project>/schema.sql

# Convert to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 schema.sql > schema_utf8.sql
```

## Python Script Issues

### Module Not Found

**Symptoms**:
```python
ModuleNotFoundError: No module named 'psycopg2'
```

**Cause**: Dependencies not installed

**Solution**:
```bash
cd .claude/skills/postgres-test/scripts
pip install -r requirements.txt

# Verify installation
python -c "import psycopg2; import docker; print('OK')"
```

### Docker SDK Connection Error

**Symptoms**:
```python
docker.errors.DockerException: Error while fetching server API version
```

**Cause**: Docker daemon not running or not accessible

**Solution**:
```bash
# Start Docker daemon
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker

# Check Docker status
docker ps

# Verify connection
python -c "import docker; docker.from_env().ping()"
```

## Performance Issues

### Slow Query Execution

**Symptoms**: Queries taking > 1 second

**Diagnosis**:
```sql
-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM PROJECT_START ps
JOIN PROJECT p ON ps.ProjectID = p.ProjectID;

-- Look for:
-- - Seq Scan (full table scan - slow)
-- - Index Scan (using index - fast)
-- - Hash Join vs Nested Loop
```

**Solutions**:

1. **Add missing indexes**:
   ```sql
   -- Foreign key indexes
   CREATE INDEX idx_project_start_project_id ON PROJECT_START(ProjectID);

   -- Datetime range queries
   CREATE INDEX idx_project_start_datetime ON PROJECT_START(StartDateTime);

   -- Composite indexes for common joins
   CREATE INDEX idx_person_assign_project_person ON PERSON_ASSIGN(ProjectID, PersonID);
   ```

2. **Update statistics**:
   ```sql
   ANALYZE;  -- Update query planner statistics
   ```

3. **Increase shared buffers** (container config):
   ```bash
   docker run ... -c shared_buffers=256MB -c work_mem=16MB postgres:16-alpine
   ```

### Container Using Too Much Memory

**Symptoms**: Docker consuming excessive RAM

**Diagnosis**:
```bash
docker stats cc-data-modeler-postgres-<project>
```

**Solution**:
```bash
# Limit container memory
docker update --memory 512m cc-data-modeler-postgres-<project>

# Or recreate with memory limit
docker run ... --memory 512m postgres:16-alpine
```

## Cleanup Issues

### Container Won't Stop

**Symptoms**:
```
Error response from daemon: cannot stop container: operation timed out
```

**Solution**:
```bash
# Force kill
docker kill cc-data-modeler-postgres-<project>

# Remove
docker rm cc-data-modeler-postgres-<project>
```

### Volume Removal Failed

**Symptoms**:
```
Error response from daemon: unable to remove volume: volume is in use
```

**Solution**:
```bash
# Stop all containers using the volume
docker ps -a | grep cc-data-modeler-postgres

# Remove containers first
docker rm -f <container_id>

# Then remove volume
docker volume rm <volume_name>
```

## Debugging Techniques

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Capture SQL Queries

```python
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

conn.set_trace_callback(print)  # Print all SQL
```

### Interactive Debugging

```bash
# Connect to container
docker exec -it cc-data-modeler-postgres-<project> bash

# Run psql
psql -U datamodeler -d immutable_model_db

# Test queries interactively
\dt  -- List tables
\d PROJECT  -- Describe table
SELECT COUNT(*) FROM PROJECT;
```

### Log Analysis

```bash
# Container logs
docker logs cc-data-modeler-postgres-<project> 2>&1 | grep ERROR

# PostgreSQL logs inside container
docker exec cc-data-modeler-postgres-<project> tail -f /var/lib/postgresql/data/pg_log/postgresql-*.log
```

## Getting Help

When reporting issues, include:

1. **Environment info**:
   ```bash
   docker --version
   python --version
   pip list | grep -E "(psycopg2|docker|pyyaml)"
   ```

2. **Container status**:
   ```bash
   docker ps -a | grep cc-data-modeler-postgres
   docker inspect cc-data-modeler-postgres-<project>
   ```

3. **Error messages**:
   - Full error output from Python script
   - Relevant container logs
   - SQL error messages

4. **File structure**:
   ```bash
   tree artifacts/<project>/
   ```

5. **Minimal reproduction**:
   - Steps to reproduce the issue
   - Expected vs actual behavior
