#!/usr/bin/env python3
"""
PostgreSQL Manager for Immutable Data Model Testing

This script manages PostgreSQL containers for testing immutable data models:
- Setup: Create and start project-specific PostgreSQL containers
- Execute: Run queries and capture results
- Validate: Check schema and data integrity
- Cleanup: Stop and remove containers

Usage:
    python postgres_manager.py setup <project-name>
    python postgres_manager.py execute --project <project-name> --query-file <path>
    python postgres_manager.py cleanup <project-name>
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import docker
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


class PostgresManager:
    """Manage PostgreSQL containers for testing"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.container_name = f"cc-data-modeler-postgres-{project_name}"
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'immutable_model_db',
            'user': 'datamodeler',
            'password': 'datamodeler123'
        }
        self.docker_client = docker.from_env()
        self.project_root = self._find_project_root()
        self.artifacts_dir = self.project_root / 'artifacts' / project_name

    def _find_project_root(self) -> Path:
        """Find project root directory (contains .claude/skills/)"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.claude' / 'skills').exists():
                return current
            current = current.parent
        return Path.cwd()

    def validate_project_files(self) -> Tuple[bool, List[str]]:
        """Validate required SQL files exist"""
        required_files = [
            'schema.sql',
            'sample_data_relative.sql',
            'query_examples.sql'
        ]
        missing = []

        if not self.artifacts_dir.exists():
            return False, [f"Project directory not found: {self.artifacts_dir}"]

        for filename in required_files:
            if not (self.artifacts_dir / filename).exists():
                missing.append(f"{self.artifacts_dir}/{filename}")

        return len(missing) == 0, missing

    def setup_container(self, cleanup: bool = True) -> Dict:
        """
        Setup PostgreSQL container for testing

        Args:
            cleanup: Remove existing container if True

        Returns:
            Dict with connection info and status
        """
        print(f"\n🚀 Setting up PostgreSQL container for project: {self.project_name}")

        # Validate project files
        valid, missing = self.validate_project_files()
        if not valid:
            print("\n[エラー] 必須ファイルが見つかりません")
            print("\n不足しているファイル:")
            for file in missing:
                print(f"  - {file}")
            return {'status': 'error', 'message': 'Missing required files'}

        # Stop and remove existing container
        if cleanup:
            self._stop_container()

        # Start new container
        try:
            schema_path = str(self.artifacts_dir / 'schema.sql')
            data_path = str(self.artifacts_dir / 'sample_data_relative.sql')

            print(f"\n📦 Starting container: {self.container_name}")
            print(f"   Schema: {schema_path}")
            print(f"   Data: {data_path}")

            container = self.docker_client.containers.run(
                'postgres:16-alpine',
                name=self.container_name,
                environment={
                    'POSTGRES_USER': self.db_config['user'],
                    'POSTGRES_PASSWORD': self.db_config['password'],
                    'POSTGRES_DB': self.db_config['database'],
                    'TZ': 'Asia/Tokyo'
                },
                ports={'5432/tcp': self.db_config['port']},
                volumes={
                    schema_path: {'bind': '/docker-entrypoint-initdb.d/01-schema.sql', 'mode': 'ro'},
                    data_path: {'bind': '/docker-entrypoint-initdb.d/02-sample_data.sql', 'mode': 'ro'}
                },
                detach=True,
                remove=False
            )

            # Wait for health check
            if not self._wait_for_health(container):
                return {'status': 'error', 'message': 'Health check timeout'}

            print("\n✅ Container started successfully")
            print(f"   Container: {self.container_name}")
            print(f"   Database: {self.db_config['database']}")
            print(f"   Port: {self.db_config['port']}")
            print(f"   Status: Healthy")

            return {
                'status': 'success',
                'container': self.container_name,
                'connection': self.db_config
            }

        except docker.errors.APIError as e:
            if 'port is already allocated' in str(e):
                print(f"\n[エラー] ポート{self.db_config['port']}が既に使用されています")
                print("\n解決方法:")
                print("  docker ps | grep postgres")
                print("  docker stop <container_name>")
                return {'status': 'error', 'message': 'Port already in use'}
            else:
                print(f"\n[エラー] Container creation failed: {e}")
                return {'status': 'error', 'message': str(e)}

    def _stop_container(self):
        """Stop and remove existing container"""
        try:
            existing = self.docker_client.containers.get(self.container_name)
            print(f"⏹️  Stopping existing container: {self.container_name}")
            existing.stop()
            existing.remove(v=True)  # Remove volumes
            print("   Container stopped and removed")
        except docker.errors.NotFound:
            pass  # Container doesn't exist, that's fine
        except Exception as e:
            print(f"   Warning: Error stopping container: {e}")

    def _wait_for_health(self, container, timeout: int = 30) -> bool:
        """Wait for PostgreSQL to be ready"""
        print(f"\n⏳ Waiting for PostgreSQL to be ready (max {timeout}s)...")
        start = time.time()

        while time.time() - start < timeout:
            try:
                # Try to connect
                conn = psycopg2.connect(**self.db_config, connect_timeout=2)
                conn.close()
                print("   PostgreSQL is ready!")
                return True
            except psycopg2.OperationalError:
                time.sleep(1)
                print(".", end="", flush=True)

        print(f"\n[エラー] Health check timeout ({timeout}s)")
        print("\nContainer logs:")
        print(container.logs().decode()[:500])
        return False

    def execute_query(self, query: str) -> Dict:
        """
        Execute a single query and return results

        Returns:
            Dict with columns, rows, execution_time_ms, status
        """
        start = time.time()

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute(query)

            # Fetch results if available
            try:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall() if cursor.description else []
            except psycopg2.ProgrammingError:
                columns = []
                rows = []

            conn.commit()
            cursor.close()
            conn.close()

            execution_time = (time.time() - start) * 1000  # ms

            return {
                'status': 'success',
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': round(execution_time, 2)
            }

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time_ms': round(execution_time, 2)
            }

    def validate_schema(self) -> Dict:
        """Validate schema structure"""
        print("\n🔍 Validating schema...")

        results = {
            'tables': self.execute_query("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """),
            'columns': self.execute_query("""
                SELECT table_name, COUNT(*) as column_count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                GROUP BY table_name
                ORDER BY table_name;
            """),
            'foreign_keys': self.execute_query("""
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
            """),
            'indexes': self.execute_query("""
                SELECT
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
        }

        # Summary
        table_count = results['tables']['row_count']
        fk_count = results['foreign_keys']['row_count']
        index_count = results['indexes']['row_count']

        print(f"   Tables: {table_count}")
        print(f"   Foreign Keys: {fk_count}")
        print(f"   Indexes: {index_count}")

        return results

    def validate_data(self) -> Dict:
        """Validate data integrity"""
        print("\n📊 Validating data...")

        results = {
            'row_counts': self.execute_query("""
                SELECT
                    schemaname,
                    tablename,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
        }

        # Summary
        tables_with_data = sum(1 for row in results['row_counts']['rows'] if row[2] > 0)
        total_rows = sum(row[2] for row in results['row_counts']['rows'])

        print(f"   Tables with data: {tables_with_data}/{results['row_counts']['row_count']}")
        print(f"   Total rows: {total_rows}")

        return results

    def parse_query_file(self, query_file: Path) -> List[Dict]:
        """
        Parse query_examples.sql into individual queries

        Returns:
            List of dicts with id, title, description, sql, line_number
        """
        print(f"\n📖 Parsing query file: {query_file}")

        with open(query_file, 'r', encoding='utf-8') as f:
            content = f.read()

        queries = []
        lines = content.split('\n')
        current_query = None
        query_sql_lines = []

        for i, line in enumerate(lines, 1):
            # Check for query header
            if line.startswith('-- 【クエリ') and '】' in line:
                # Save previous query
                if current_query and query_sql_lines:
                    current_query['sql'] = '\n'.join(query_sql_lines).strip()
                    queries.append(current_query)

                # Extract query ID and title
                header = line.split('】', 1)
                if len(header) == 2:
                    id_part = header[0].replace('-- 【クエリ', '').strip()
                    title = header[1].strip()

                    current_query = {
                        'id': int(id_part) if id_part.isdigit() else len(queries) + 1,
                        'title': title,
                        'description': '',
                        'line_number': i
                    }
                    query_sql_lines = []

            # Check for description line
            elif current_query and line.startswith('-- イミュータブル') and not current_query['description']:
                current_query['description'] = line.replace('--', '').strip()

            # Collect SQL lines (not comments, not empty, not separator)
            elif current_query and not line.startswith('--') and line.strip() and not line.startswith('='):
                query_sql_lines.append(line)

        # Save last query
        if current_query and query_sql_lines:
            current_query['sql'] = '\n'.join(query_sql_lines).strip()
            queries.append(current_query)

        print(f"   Found {len(queries)} queries")
        return queries

    def execute_query_file(self, query_file: Path) -> List[Dict]:
        """Execute all queries from file"""
        queries = self.parse_query_file(query_file)
        results = []

        print(f"\n🚀 Executing {len(queries)} queries...")

        for i, query in enumerate(queries, 1):
            print(f"\n   Query {query['id']}: {query['title']}")
            result = self.execute_query(query['sql'])

            query_result = {
                **query,
                **result
            }

            if result['status'] == 'success':
                print(f"      ✅ Success: {result['row_count']} rows in {result['execution_time_ms']}ms")
            else:
                print(f"      ❌ Error: {result.get('error', 'Unknown error')}")

            results.append(query_result)

        # Summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_time = sum(r['execution_time_ms'] for r in results)

        print(f"\n📊 Execution Summary:")
        print(f"   Total: {len(results)}")
        print(f"   Success: {success_count}")
        print(f"   Failed: {len(results) - success_count}")
        print(f"   Total time: {total_time:.2f}ms")

        return results

    def cleanup(self):
        """Stop and remove container"""
        print(f"\n🧹 Cleaning up container: {self.container_name}")
        self._stop_container()
        print("✅ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(description='PostgreSQL Manager for Immutable Data Model Testing')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup PostgreSQL container')
    setup_parser.add_argument('project', help='Project name')
    setup_parser.add_argument('--no-cleanup', action='store_true', help='Keep existing container')

    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute queries')
    execute_parser.add_argument('--project', required=True, help='Project name')
    execute_parser.add_argument('--query-file', required=True, help='Path to query file')
    execute_parser.add_argument('--output', help='Output JSON file')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup container')
    cleanup_parser.add_argument('project', help='Project name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'setup':
        manager = PostgresManager(args.project)
        result = manager.setup_container(cleanup=not args.no_cleanup)

        if result['status'] == 'success':
            # Validate schema and data
            schema_results = manager.validate_schema()
            data_results = manager.validate_data()

            print("\n✅ Setup complete!")
            sys.exit(0)
        else:
            print(f"\n❌ Setup failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)

    elif args.command == 'execute':
        manager = PostgresManager(args.project)
        query_file = Path(args.query_file)

        if not query_file.exists():
            print(f"[エラー] Query file not found: {query_file}")
            sys.exit(1)

        results = manager.execute_query_file(query_file)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {args.output}")

        sys.exit(0)

    elif args.command == 'cleanup':
        manager = PostgresManager(args.project)
        manager.cleanup()
        sys.exit(0)


if __name__ == '__main__':
    main()
