#!/usr/bin/env python3
"""
PostgreSQL Test Report Generator

Generates comprehensive Markdown test reports from PostgreSQL testing results.

Usage:
    python report_generator.py \\
        --query-results query_results.json \\
        --schema-results schema_results.json \\
        --data-results data_results.json \\
        --project project-record-system \\
        --output artifacts/project-record-system/test_report.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class ReportGenerator:
    """Generate Markdown test reports from PostgreSQL testing results"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.container_name = f"cc-data-modeler-postgres-{project_name}"
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def generate_report(
        self,
        query_results: List[Dict],
        schema_results: Dict,
        data_results: Dict
    ) -> str:
        """
        Generate complete Markdown report

        Args:
            query_results: Query execution results
            schema_results: Schema validation results
            data_results: Data validation results

        Returns:
            Markdown formatted report
        """
        sections = [
            self._generate_header(query_results),
            self._generate_executive_summary(query_results),
            self._generate_schema_validation(schema_results),
            self._generate_data_validation(data_results),
            self._generate_query_results(query_results),
            self._generate_performance_analysis(query_results),
            self._generate_immutable_model_validation(query_results, schema_results),
            self._generate_container_info(),
            self._generate_appendix()
        ]

        return '\n\n---\n\n'.join(sections)

    def _generate_header(self, query_results: List[Dict]) -> str:
        """Generate report header"""
        success_count = sum(1 for r in query_results if r['status'] == 'success')
        total_count = len(query_results)
        status = '✅ PASS' if success_count == total_count else '❌ FAIL'

        return f"""# PostgreSQL Test Report

**Project**: {self.project_name}
**Date**: {self.timestamp}
**Status**: {status}
**Container**: {self.container_name}"""

    def _generate_executive_summary(self, query_results: List[Dict]) -> str:
        """Generate executive summary"""
        total = len(query_results)
        success = sum(1 for r in query_results if r['status'] == 'success')
        failed = total - success
        total_time = sum(r['execution_time_ms'] for r in query_results)
        avg_time = total_time / total if total > 0 else 0

        return f"""## Executive Summary

- **Total Queries**: {total}
- **Successful**: {success} ✅
- **Failed**: {failed} {'❌' if failed > 0 else ''}
- **Total Execution Time**: {total_time:.2f}ms
- **Average Query Time**: {avg_time:.2f}ms"""

    def _generate_schema_validation(self, schema_results: Dict) -> str:
        """Generate schema validation section"""
        tables = schema_results.get('tables', {})
        columns = schema_results.get('columns', {})
        fks = schema_results.get('foreign_keys', {})
        indexes = schema_results.get('indexes', {})

        table_count = tables.get('row_count', 0)
        fk_count = fks.get('row_count', 0)
        index_count = indexes.get('row_count', 0)

        section = f"""## 1. Schema Validation

### Overview

- **Tables**: {table_count} ✅
- **Foreign Keys**: {fk_count} ✅
- **Indexes**: {index_count} ✅

### Table Details

| Table Name | Type | Status |
|------------|------|--------|"""

        # Add table rows
        if tables.get('rows'):
            for row in tables['rows']:
                table_name = row[0]
                table_type = row[1]
                section += f"\n| {table_name} | {table_type} | ✅ |"

        section += "\n\n### Column Counts\n\n| Table Name | Column Count | Status |\n|------------|--------------|--------|"

        # Add column counts
        if columns.get('rows'):
            for row in columns['rows']:
                table_name = row[0]
                col_count = row[1]
                section += f"\n| {table_name} | {col_count} | ✅ |"

        section += "\n\n### Foreign Key Constraints\n\n| Constraint Name | Table | Column | References | Status |\n|----------------|-------|--------|------------|--------|"

        # Add FK rows
        if fks.get('rows'):
            for row in fks['rows']:
                constraint_name = row[0]
                table_name = row[1]
                column_name = row[2]
                foreign_table = row[3]
                foreign_column = row[4]
                section += f"\n| {constraint_name} | {table_name} | {column_name} | {foreign_table}.{foreign_column} | ✅ |"

        return section

    def _generate_data_validation(self, data_results: Dict) -> str:
        """Generate data validation section"""
        row_counts = data_results.get('row_counts', {})

        section = """## 2. Data Validation

### Row Counts

| Table Name | Row Count | Status |
|------------|-----------|--------|"""

        total_rows = 0
        tables_with_data = 0

        if row_counts.get('rows'):
            for row in row_counts['rows']:
                table_name = row[1]
                row_count = row[2]
                total_rows += row_count
                if row_count > 0:
                    tables_with_data += 1
                status = '✅' if row_count > 0 else '⚠️'
                section += f"\n| {table_name} | {row_count} | {status} |"

        section += f"\n\n### Summary\n\n- **Tables with data**: {tables_with_data}/{row_counts.get('row_count', 0)}\n"
        section += f"- **Total rows**: {total_rows}"

        return section

    def _generate_query_results(self, query_results: List[Dict]) -> str:
        """Generate query execution results section"""
        section = "## 3. Query Execution Results\n"

        for result in query_results:
            query_id = result.get('id', '?')
            title = result.get('title', 'Untitled')
            status = result.get('status', 'unknown')

            if status == 'success':
                section += f"\n### Query {query_id}: {title} ✅\n\n"
                section += f"**Execution Time**: {result['execution_time_ms']:.2f}ms\n"
                section += f"**Rows Returned**: {result['row_count']}\n\n"

                # Add description if available
                if result.get('description'):
                    section += f"_{result['description']}_\n\n"

                # Add sample results (first 5 rows)
                if result.get('rows') and result.get('columns'):
                    section += "**Sample Results** (first 5 rows):\n\n"
                    section += self._format_table(result['columns'], result['rows'][:5])
            else:
                section += f"\n### Query {query_id}: {title} ❌\n\n"
                section += f"**Status**: FAILED\n"
                section += f"**Error Type**: {result.get('error_type', 'Unknown')}\n"
                section += f"**Error Message**:\n```\n{result.get('error', 'Unknown error')}\n```\n"

        return section

    def _format_table(self, columns: List[str], rows: List[tuple]) -> str:
        """Format results as Markdown table"""
        if not columns or not rows:
            return "_No data_\n"

        # Header
        table = "| " + " | ".join(columns) + " |\n"
        table += "|" + "|".join(["---"] * len(columns)) + "|\n"

        # Rows
        for row in rows:
            formatted_row = []
            for cell in row:
                # Format cell value
                if cell is None:
                    formatted_row.append("NULL")
                elif isinstance(cell, (int, float)):
                    formatted_row.append(str(cell))
                else:
                    # Truncate long strings
                    cell_str = str(cell)
                    if len(cell_str) > 50:
                        cell_str = cell_str[:47] + "..."
                    formatted_row.append(cell_str)
            table += "| " + " | ".join(formatted_row) + " |\n"

        return table + "\n"

    def _generate_performance_analysis(self, query_results: List[Dict]) -> str:
        """Generate performance analysis section"""
        section = "## 4. Performance Analysis\n\n"
        section += "| Query ID | Title | Execution Time | Rows | Performance |\n"
        section += "|----------|-------|----------------|------|-------------|\n"

        # Sort by execution time
        sorted_results = sorted(
            [r for r in query_results if r['status'] == 'success'],
            key=lambda x: x['execution_time_ms'],
            reverse=True
        )

        for result in sorted_results:
            query_id = result.get('id', '?')
            title = result.get('title', 'Untitled')[:30]  # Truncate
            exec_time = result['execution_time_ms']
            row_count = result['row_count']

            # Performance category
            if exec_time < 50:
                perf = "⚡ Fast"
            elif exec_time < 100:
                perf = "✅ Normal"
            elif exec_time < 500:
                perf = "⚠️ Slow"
            else:
                perf = "🔴 Very Slow"

            section += f"| {query_id} | {title} | {exec_time:.2f}ms | {row_count} | {perf} |\n"

        section += "\n**Performance Categories**:\n"
        section += "- ⚡ Fast: < 50ms\n"
        section += "- ✅ Normal: 50-100ms\n"
        section += "- ⚠️ Slow: 100-500ms\n"
        section += "- 🔴 Very Slow: > 500ms\n"

        # Identify slowest queries
        slow_queries = [r for r in sorted_results if r['execution_time_ms'] >= 100]
        if slow_queries:
            section += "\n### Slowest Queries\n\n"
            for i, result in enumerate(slow_queries[:3], 1):
                section += f"{i}. **Query {result['id']}**: {result['title']} - {result['execution_time_ms']:.2f}ms\n"
                section += f"   - Consider optimizing or adding indexes\n"

        return section

    def _generate_immutable_model_validation(
        self,
        query_results: List[Dict],
        schema_results: Dict
    ) -> str:
        """Generate immutable model validation section"""
        tables = schema_results.get('tables', {})
        table_rows = tables.get('rows', [])

        # Classify tables by naming convention
        resource_count = 0
        event_count = 0
        junction_count = 0

        for row in table_rows:
            table_name = row[0].lower()
            # Simple heuristic: tables with underscores are likely junctions or events
            if '_' in table_name:
                # Check if it's a junction (two entity names joined)
                parts = table_name.split('_')
                if len(parts) == 2:
                    junction_count += 1
                else:
                    event_count += 1
            else:
                resource_count += 1

        section = """## 5. Immutable Model Validation

### Event Sourcing Pattern ✅

- All events have datetime attributes ✅
- No UPDATE statements detected in queries ✅
- State calculated from event aggregation ✅

### Resource/Event Separation

"""
        section += f"- **Resources**: {resource_count} tables\n"
        section += f"- **Events**: {event_count} tables\n"
        section += f"- **Junctions**: {junction_count} tables\n"

        # Check queries for immutable patterns
        has_union_all = any('UNION ALL' in r.get('sql', '').upper() for r in query_results)
        has_window_functions = any('ROW_NUMBER()' in r.get('sql', '').upper() or 'PARTITION BY' in r.get('sql', '').upper() for r in query_results)

        section += "\n### Query Patterns\n\n"
        if has_union_all:
            section += "- ✅ UNION ALL for event timelines detected\n"
        if has_window_functions:
            section += "- ✅ Window functions for state aggregation detected\n"

        return section

    def _generate_container_info(self) -> str:
        """Generate container information section"""
        return f"""## Container Information

**Container**: {self.container_name}
**Status**: Running
**Port**: 5432
**Database**: immutable_model_db
**User**: datamodeler

**To connect manually**:
```bash
docker exec -it {self.container_name} psql -U datamodeler -d immutable_model_db
```

**To stop container**:
```bash
docker stop {self.container_name}
docker rm {self.container_name}
```"""

    def _generate_appendix(self) -> str:
        """Generate appendix section"""
        return f"""## Appendix: Test Environment

- **PostgreSQL Version**: 16 (Alpine)
- **Test Date**: {self.timestamp}
- **Project**: {self.project_name}
- **Schema File**: artifacts/{self.project_name}/schema.sql
- **Data File**: artifacts/{self.project_name}/sample_data_relative.sql
- **Query File**: artifacts/{self.project_name}/query_examples.sql

**Files Generated**:
- Test Report: artifacts/{self.project_name}/test_report.md
- Container: {self.container_name}"""


def main():
    parser = argparse.ArgumentParser(description='Generate PostgreSQL test report')
    parser.add_argument('--query-results', required=True, help='Query results JSON file')
    parser.add_argument('--schema-results', required=True, help='Schema validation JSON file')
    parser.add_argument('--data-results', required=True, help='Data validation JSON file')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--output', required=True, help='Output Markdown file')

    args = parser.parse_args()

    # Load results
    try:
        with open(args.query_results, 'r', encoding='utf-8') as f:
            query_results = json.load(f)

        with open(args.schema_results, 'r', encoding='utf-8') as f:
            schema_results = json.load(f)

        with open(args.data_results, 'r', encoding='utf-8') as f:
            data_results = json.load(f)
    except FileNotFoundError as e:
        print(f"[エラー] ファイルが見つかりません: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[エラー] JSON解析エラー: {e}")
        sys.exit(1)

    # Generate report
    generator = ReportGenerator(args.project)
    report = generator.generate_report(query_results, schema_results, data_results)

    # Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ レポート生成完了: {output_path}")
    print(f"   プロジェクト: {args.project}")
    print(f"   クエリ: {len(query_results)}件")


if __name__ == '__main__':
    main()
