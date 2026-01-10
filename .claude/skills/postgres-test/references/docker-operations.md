# Docker Operations Reference

Docker container management patterns for PostgreSQL testing.

## Container Lifecycle

### Creating Project-Specific Containers

Use project-specific naming to enable parallel testing:

```bash
docker run -d \
  --name cc-data-modeler-postgres-{project-name} \
  -e POSTGRES_USER=datamodeler \
  -e POSTGRES_PASSWORD=datamodeler123 \
  -e POSTGRES_DB=immutable_model_db \
  -e TZ='Asia/Tokyo' \
  -p 5432:5432 \
  postgres:16-alpine
```

**Key patterns**:
- Container name includes project name for isolation
- Fixed port (5432) - only one active container per machine
- Timezone set to Asia/Tokyo for consistent timestamps

### Volume Mounting

Mount SQL files for automatic initialization:

```bash
-v /absolute/path/artifacts/{project}/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro \
-v /absolute/path/artifacts/{project}/sample_data_relative.sql:/docker-entrypoint-initdb.d/02-sample_data.sql:ro
```

**Critical details**:
- Use absolute paths (Docker requirement)
- Files execute in alphanumeric order (01-, 02-)
- Read-only mount (`:ro`) prevents accidental modification
- `/docker-entrypoint-initdb.d/` runs scripts on first container start

### Health Checks

Wait for PostgreSQL to be ready before running queries:

```python
import psycopg2
import time

def wait_for_health(db_config, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(**db_config, connect_timeout=2)
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(1)
    return False
```

Alternative using `pg_isready`:

```bash
docker exec {container-name} pg_isready -U datamodeler -d immutable_model_db
```

## Container Management

### Listing Containers

Find project-specific containers:

```bash
docker ps --filter "name=cc-data-modeler-postgres-"
```

### Stopping and Removing

Clean up before creating new container:

```python
try:
    container = docker_client.containers.get(container_name)
    container.stop()
    container.remove(v=True)  # Remove volumes
except docker.errors.NotFound:
    pass  # Container doesn't exist
```

**Important**: Remove volumes (`v=True`) to ensure fresh data on restart.

### Inspecting Logs

Debug container startup issues:

```bash
docker logs cc-data-modeler-postgres-{project}
```

Common log patterns:
- `database system is ready to accept connections` - Success
- `port is already allocated` - Port conflict
- `syntax error at or near` - SQL file error

## Port Management

### Port Conflicts

Only one container can bind to port 5432:

```python
except docker.errors.APIError as e:
    if 'port is already allocated' in str(e):
        # Suggest stopping existing container
        print("Port 5432 is in use. Check: docker ps | grep postgres")
```

**Resolution**:
1. List all PostgreSQL containers: `docker ps | grep postgres`
2. Stop conflicting container: `docker stop {container-name}`
3. Retry container creation

### Using Alternative Ports (Future)

Currently not supported, but could be implemented:

```python
# Port selection logic
port = 5432
while port < 5442:  # Try ports 5432-5441
    try:
        container = docker_client.containers.run(..., ports={f'5432/tcp': port})
        break
    except docker.errors.APIError:
        port += 1
```

## Connecting to Containers

### Direct psql Connection

```bash
docker exec -it cc-data-modeler-postgres-{project} psql -U datamodeler -d immutable_model_db
```

### From Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='immutable_model_db',
    user='datamodeler',
    password='datamodeler123'
)
```

### Running Queries

```python
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM PROJECT;")
result = cursor.fetchone()
cursor.close()
conn.close()
```

## Best Practices

### Container Naming

- **Pattern**: `cc-data-modeler-postgres-{project-name}`
- **Benefits**:
  - Clear ownership (cc-data-modeler)
  - Purpose identification (postgres)
  - Project isolation ({project-name})

### Cleanup Strategy

**Option 1: Automatic cleanup** (default)
```python
manager.setup_container(cleanup=True)  # Removes old container
```

**Option 2: Keep existing** (manual testing)
```python
manager.setup_container(cleanup=False)  # Reuse existing
```

### Error Recovery

Always handle container errors gracefully:

```python
try:
    container = docker_client.containers.run(...)
except docker.errors.ContainerError as e:
    print(f"Container failed to start: {e}")
    # Show logs
    print(container.logs())
except docker.errors.ImageNotFound:
    print("postgres:16-alpine image not found. Run: docker pull postgres:16-alpine")
except docker.errors.APIError as e:
    print(f"Docker API error: {e}")
```

## Multi-Project Support

Test multiple projects concurrently:

```bash
# Project 1
docker run -d --name cc-data-modeler-postgres-project1 -p 5432:5432 ...

# Project 2 (different machine or sequential testing)
docker run -d --name cc-data-modeler-postgres-project2 -p 5433:5432 ...
```

**Current limitation**: Single port (5432) allows only one active container per machine.

**Workaround**: Sequential testing with automatic cleanup between projects.

## Docker Python SDK

### Installation

```bash
pip install docker>=7.0.0
```

### Basic Usage

```python
import docker

client = docker.from_env()

# List containers
containers = client.containers.list(all=True)

# Get specific container
container = client.containers.get('cc-data-modeler-postgres-project1')

# Check status
print(container.status)  # 'running', 'exited', etc.

# Execute command
result = container.exec_run('psql -U datamodeler -c "SELECT 1"')
print(result.output.decode())
```

## Troubleshooting

### Container won't start

1. Check Docker daemon: `docker ps`
2. Check image availability: `docker images | grep postgres`
3. Pull if missing: `docker pull postgres:16-alpine`

### SQL files not loading

1. Verify absolute paths in volume mounts
2. Check file permissions: `ls -la artifacts/{project}/`
3. Inspect container logs: `docker logs {container-name}`

### Connection refused

1. Wait for health check to pass
2. Verify port binding: `docker port {container-name}`
3. Check PostgreSQL logs: `docker logs {container-name}`

### Disk space issues

1. Check available space: `df -h`
2. Remove old containers: `docker container prune`
3. Remove old images: `docker image prune`
