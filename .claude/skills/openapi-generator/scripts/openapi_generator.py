#!/usr/bin/env python3
"""
OpenAPI 3.1.0 Generator

Main orchestration script that generates complete OpenAPI specification from immutable data models.

Usage:
    python openapi_generator.py <project-name>

Input Files:
    - artifacts/{project-name}/entities_classified.json
    - artifacts/{project-name}/model.json

Output File:
    - artifacts/{project-name}/openapi.yaml

Features:
    - CQRS pattern (POST/PUT for events, GET for queries)
    - Event → Action API mapping
    - Resource → CRUD API mapping
    - State aggregation queries (latest, history, current, summary)
    - RFC 7807 error responses
    - Idempotency-Key headers
    - Pagination and filtering
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List
import yaml

# Import mappers
from event_mapper import EventMapper, EndpointDefinition as EventEndpoint
from resource_mapper import ResourceMapper, EndpointDefinition as ResourceEndpoint
from state_aggregation_inferrer import StateAggregationInferrer, AggregationEndpointDefinition


class OpenAPIGenerator:
    """Main OpenAPI 3.1.0 specification generator."""

    def __init__(self, project_name: str, enable_nablarch: bool = False):
        """
        Initialize OpenAPI Generator.

        Args:
            project_name: Name of the project (e.g., "project-record-system")
            enable_nablarch: Enable Nablarch/Spring metadata enhancement (default: False)
        """
        self.project_name = project_name
        self.enable_nablarch_enhancement = enable_nablarch
        self.artifacts_dir = Path(f"artifacts/{project_name}")

        # Initialize mappers
        self.event_mapper = EventMapper()
        self.resource_mapper = ResourceMapper()
        self.aggregation_inferrer = StateAggregationInferrer()

        # Load data
        self.entities_classified = self._load_json(self.artifacts_dir / "entities_classified.json")
        self.model = self._load_json(self.artifacts_dir / "model.json")

        # OpenAPI spec structure
        self.openapi_spec = self._load_base_template()

    def generate(self) -> None:
        """Generate complete OpenAPI specification."""
        print(f"🚀 Generating OpenAPI 3.1.0 specification for {self.project_name}...")

        # Step 1: Extract entities by classification
        resources, events, junctions = self._classify_entities()
        print(f"📊 Found {len(resources)} resources, {len(events)} events, {len(junctions)} junctions")

        # Step 2: Generate resource endpoints (CRUD)
        print("🔨 Generating resource endpoints (CRUD)...")
        resource_endpoints = self._generate_resource_endpoints(resources)

        # Step 3: Generate event endpoints (Actions)
        print("⚡ Generating event endpoints (Actions)...")
        event_endpoints = self._generate_event_endpoints(events)

        # Step 4: Generate state aggregation endpoints
        print("📈 Generating state aggregation endpoints...")
        aggregation_endpoints = self._generate_aggregation_endpoints(events, resources + events + junctions)

        # Step 5: Build OpenAPI paths and schemas
        print("🏗️  Building OpenAPI paths and schemas...")
        self._build_paths(resource_endpoints, event_endpoints, aggregation_endpoints)
        self._build_schemas(resources, events, junctions)
        self._build_tags(resources, events, junctions)

        # Step 6: Add common components
        print("🧩 Adding common components...")
        self._add_common_components()

        # Step 6.5: Nablarch Enhancement (opt-in)
        if self.enable_nablarch_enhancement:
            print("🏯 Adding Nablarch/Spring metadata enhancement...")
            from nablarch_enhancer import NablarchEnhancer
            enhancer = NablarchEnhancer()
            self.openapi_spec = enhancer.enhance(
                self.openapi_spec,
                self.entities_classified,
                self.model
            )
            print("✅ Nablarch enhancement completed")

        # Step 7: Write output
        output_path = self.artifacts_dir / "openapi.yaml"
        self._write_yaml(output_path, self.openapi_spec)

        print(f"✅ OpenAPI specification generated: {output_path}")
        print(f"📝 Total endpoints: {len(self.openapi_spec['paths'])}")

    def _classify_entities(self) -> tuple:
        """Classify entities into resources, events, and junctions."""
        # entities_classified.json has the structure: {"resources": [...], "events": [...], "junctions": [...]}
        resources = self.entities_classified.get('resources', [])
        events = self.entities_classified.get('events', [])
        junctions = self.entities_classified.get('junctions', [])

        return resources, events, junctions

    def _generate_resource_endpoints(self, resources: List[Dict]) -> List[ResourceEndpoint]:
        """Generate CRUD endpoints for resources."""
        all_endpoints = []

        for resource in resources:
            endpoints = self.resource_mapper.map_resource_to_endpoints(resource)
            all_endpoints.extend(endpoints)

        print(f"   ✓ Generated {len(all_endpoints)} resource endpoints")
        return all_endpoints

    def _generate_event_endpoints(self, events: List[Dict]) -> List[EventEndpoint]:
        """Generate action endpoints for events."""
        all_endpoints = []

        for event in events:
            endpoint = self.event_mapper.map_event_to_endpoint(event)
            all_endpoints.append(endpoint)

        print(f"   ✓ Generated {len(all_endpoints)} event endpoints")
        return all_endpoints

    def _generate_aggregation_endpoints(
        self,
        events: List[Dict],
        all_entities: List[Dict]
    ) -> List[AggregationEndpointDefinition]:
        """Generate state aggregation endpoints."""
        endpoints = self.aggregation_inferrer.infer_aggregation_endpoints(events, all_entities)
        print(f"   ✓ Generated {len(endpoints)} aggregation endpoints")
        return endpoints

    def _build_paths(
        self,
        resource_endpoints: List[ResourceEndpoint],
        event_endpoints: List[EventEndpoint],
        aggregation_endpoints: List[AggregationEndpointDefinition]
    ) -> None:
        """Build OpenAPI paths section."""
        paths = {}

        # Add resource endpoints
        for endpoint in resource_endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            paths[endpoint.path][endpoint.method.lower()] = self._build_operation(endpoint)

        # Add event endpoints
        for endpoint in event_endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            paths[endpoint.path][endpoint.method.lower()] = self._build_operation(endpoint)

        # Add aggregation endpoints
        for endpoint in aggregation_endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}

            paths[endpoint.path][endpoint.method.lower()] = self._build_aggregation_operation(endpoint)

        self.openapi_spec['paths'] = paths

    def _build_operation(self, endpoint) -> Dict:
        """Build OpenAPI operation object."""
        operation = {
            'summary': endpoint.summary,
            'description': endpoint.description,
            'operationId': endpoint.operation_id,
            'tags': endpoint.tags,
            'responses': self._build_responses(endpoint)
        }

        # Add query parameters (for GET endpoints)
        if hasattr(endpoint, 'query_parameters') and endpoint.query_parameters:
            operation['parameters'] = endpoint.query_parameters

        # Add request body (for POST/PUT/PATCH)
        if endpoint.request_body_schema:
            operation['requestBody'] = {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': endpoint.request_body_schema
                    }
                }
            }

        # Add Idempotency-Key header (for POST/PUT)
        if endpoint.requires_idempotency_key:
            if 'parameters' not in operation:
                operation['parameters'] = []

            operation['parameters'].append({
                '$ref': '#/components/parameters/IdempotencyKey'
            })

        # Add security
        operation['security'] = [{'BearerAuth': []}]

        return operation

    def _build_aggregation_operation(self, endpoint: AggregationEndpointDefinition) -> Dict:
        """Build OpenAPI operation object for aggregation endpoints."""
        operation = {
            'summary': endpoint.summary,
            'description': endpoint.description,
            'operationId': endpoint.operation_id,
            'tags': endpoint.tags,
            'responses': {
                '200': {
                    'description': '成功',
                    'content': {
                        'application/json': {
                            'schema': endpoint.response_schema
                        }
                    }
                },
                '404': {'$ref': '#/components/responses/NotFound'},
                '500': {'$ref': '#/components/responses/InternalServerError'}
            }
        }

        # Add query parameters
        if endpoint.query_parameters:
            operation['parameters'] = endpoint.query_parameters

        # Add security
        operation['security'] = [{'BearerAuth': []}]

        return operation

    def _build_responses(self, endpoint) -> Dict:
        """Build responses section for endpoint."""
        method = endpoint.method.upper()

        # Success response
        if method == 'GET':
            success_response = {
                '200': {
                    'description': '成功',
                    'content': {
                        'application/json': {
                            'schema': endpoint.response_schema
                        }
                    }
                }
            }
        elif method == 'POST':
            success_response = {
                '201': {
                    'description': '作成成功',
                    'content': {
                        'application/json': {
                            'schema': endpoint.response_schema
                        }
                    }
                }
            }
        elif method in ['PUT', 'PATCH']:
            success_response = {
                '200': {
                    'description': '更新成功',
                    'content': {
                        'application/json': {
                            'schema': endpoint.response_schema
                        }
                    }
                }
            }
        elif method == 'DELETE':
            success_response = {
                '204': {
                    'description': '削除成功'
                }
            }
        else:
            success_response = {}

        # Error responses
        error_responses = {
            '400': {'$ref': '#/components/responses/BadRequest'},
            '401': {'$ref': '#/components/responses/Unauthorized'},
            '403': {'$ref': '#/components/responses/Forbidden'},
            '404': {'$ref': '#/components/responses/NotFound'},
            '409': {'$ref': '#/components/responses/Conflict'},
            '422': {'$ref': '#/components/responses/UnprocessableEntity'},
            '500': {'$ref': '#/components/responses/InternalServerError'}
        }

        # Merge success and error responses
        responses = {**success_response, **error_responses}

        return responses

    def _build_schemas(
        self,
        resources: List[Dict],
        events: List[Dict],
        junctions: List[Dict]
    ) -> None:
        """Build OpenAPI schemas section."""
        schemas = {}

        # Build schemas for resources
        for resource in resources:
            schemas[resource['english']] = self._build_entity_schema(resource)

        # Build schemas for events
        for event in events:
            schemas[event['english']] = self._build_entity_schema(event)

        # Build schemas for junctions
        for junction in junctions:
            schemas[junction['english']] = self._build_entity_schema(junction)

        self.openapi_spec['components']['schemas'] = {
            **schemas,
            **self.openapi_spec['components'].get('schemas', {})
        }

    def _build_entity_schema(self, entity: Dict) -> Dict:
        """Build schema for a single entity."""
        properties = {}
        required = []

        for attr in entity.get('attributes', []):
            prop_name = self._to_camel_case(attr['english'])
            prop_def = {
                'type': self._map_sql_type_to_openapi(attr['type']),
                'description': attr['japanese']
            }

            # Add format for specific types
            if attr['type'] == 'TIMESTAMP':
                prop_def['format'] = 'date-time'
            elif attr['type'] == 'DATE':
                prop_def['format'] = 'date'

            # Add constraints
            if attr['type'] in ['VARCHAR', 'CHAR'] and 'length' in attr:
                prop_def['maxLength'] = attr['length']

            properties[prop_name] = prop_def

            # Check if required (simplified: assume primary keys and non-nullable are required)
            if attr.get('is_primary_key') or attr['english'].endswith('ID'):
                required.append(prop_name)

        return {
            'type': 'object',
            'required': required if required else None,
            'properties': properties,
            'description': entity['japanese']
        }

    def _build_tags(
        self,
        resources: List[Dict],
        events: List[Dict],
        junctions: List[Dict]
    ) -> None:
        """Build OpenAPI tags section."""
        tags_set = set()

        # Extract tags from all entities
        for resource in resources:
            tags_set.add(self._pluralize(resource['english']))

        # Add special tags
        tags_set.add('Approvals')
        tags_set.add('Events')

        tags = []
        for tag in sorted(tags_set):
            tags.append({
                'name': tag,
                'description': f'{tag}関連のエンドポイント'
            })

        self.openapi_spec['tags'] = tags

    def _add_common_components(self) -> None:
        """Add common components from common-components.yaml."""
        common_components_path = Path(__file__).parent.parent / "templates" / "common-components.yaml"

        if not common_components_path.exists():
            print(f"⚠️  Warning: common-components.yaml not found at {common_components_path}")
            return

        common_components = self._load_yaml(common_components_path)

        # Merge components
        for key in ['schemas', 'responses', 'parameters', 'headers', 'examples']:
            if key in common_components.get('components', {}):
                if key not in self.openapi_spec['components']:
                    self.openapi_spec['components'][key] = {}

                self.openapi_spec['components'][key].update(
                    common_components['components'][key]
                )

    def _load_base_template(self) -> Dict:
        """Load base OpenAPI template."""
        template_path = Path(__file__).parent.parent / "templates" / "openapi-base-template.yaml"

        if not template_path.exists():
            raise FileNotFoundError(f"Base template not found: {template_path}")

        spec = self._load_yaml(template_path)

        # Update info
        spec['info']['title'] = f"{self.project_name} API"

        # Initialize empty components if None (YAML comments create None values)
        if 'components' not in spec:
            spec['components'] = {}

        for key in ['schemas', 'responses', 'parameters', 'headers', 'examples']:
            if key not in spec['components'] or spec['components'][key] is None:
                spec['components'][key] = {}

        return spec

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _write_yaml(self, file_path: Path, data: Dict) -> None:
        """Write YAML file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=1000  # Prevent line wrapping
            )

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert PascalCase to camelCase."""
        if not text:
            return text
        return text[0].lower() + text[1:]

    @staticmethod
    def _pluralize(text: str) -> str:
        """Simple English pluralization."""
        if text.endswith('y') and text[-2] not in 'aeiou':
            return text[:-1] + 'ies'
        elif text.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return text + 'es'
        else:
            return text + 's'

    @staticmethod
    def _map_sql_type_to_openapi(sql_type: str) -> str:
        """Map SQL types to OpenAPI types."""
        type_mapping = {
            'INT': 'integer',
            'BIGINT': 'integer',
            'SMALLINT': 'integer',
            'DECIMAL': 'number',
            'NUMERIC': 'number',
            'FLOAT': 'number',
            'DOUBLE': 'number',
            'VARCHAR': 'string',
            'TEXT': 'string',
            'CHAR': 'string',
            'DATE': 'string',
            'TIMESTAMP': 'string',
            'BOOLEAN': 'boolean',
        }
        return type_mapping.get(sql_type.upper(), 'string')


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='OpenAPI 3.1.0 Generator - Generate OpenAPI specification from immutable data models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate OpenAPI without Nablarch enhancement
  python openapi_generator.py project-record-system

  # Generate OpenAPI with Nablarch/Spring metadata enhancement
  python openapi_generator.py project-record-system --enable-nablarch
        """
    )
    parser.add_argument('project_name', help='Project name (e.g., project-record-system)')
    parser.add_argument('--enable-nablarch', action='store_true',
                       help='Enable Nablarch/Spring metadata enhancement (tags, domain annotations, constraints)')

    args = parser.parse_args()

    try:
        generator = OpenAPIGenerator(args.project_name, enable_nablarch=args.enable_nablarch)
        generator.generate()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure the following files exist:")
        print(f"  - artifacts/{args.project_name}/entities_classified.json")
        print(f"  - artifacts/{args.project_name}/model.json")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
