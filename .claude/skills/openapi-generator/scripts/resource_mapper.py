"""
Resource Entity to API Endpoint Mapper

This module converts resource entities from entities_classified.json to OpenAPI endpoint definitions.
Generates standard CRUD operations with pagination, filtering, and sorting support.
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EndpointDefinition:
    """Represents an API endpoint definition."""
    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    tags: List[str]
    query_parameters: Optional[List[Dict]] = None
    request_body_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None
    requires_idempotency_key: bool = False


class ResourceMapper:
    """Maps resource entities to CRUD API endpoints."""

    def __init__(self):
        """Initialize ResourceMapper."""
        pass

    def map_resource_to_endpoints(self, resource_entity: Dict) -> List[EndpointDefinition]:
        """
        Map a resource entity to CRUD API endpoints.

        Args:
            resource_entity: Resource entity from entities_classified.json

        Returns:
            List of EndpointDefinition objects (list, get, create, update, delete)
        """
        english_name = resource_entity['english']
        japanese_name = resource_entity['japanese']

        endpoints = []

        # 1. List endpoint (GET /api/{resources})
        endpoints.append(self._create_list_endpoint(english_name, japanese_name, resource_entity))

        # 2. Get endpoint (GET /api/{resources}/{id})
        endpoints.append(self._create_get_endpoint(english_name, japanese_name, resource_entity))

        # 3. Create endpoint (POST /api/{resources})
        endpoints.append(self._create_create_endpoint(english_name, japanese_name, resource_entity))

        # 4. Update endpoint (PATCH /api/{resources}/{id})
        endpoints.append(self._create_update_endpoint(english_name, japanese_name, resource_entity))

        # 5. Delete endpoint (DELETE /api/{resources}/{id})
        endpoints.append(self._create_delete_endpoint(english_name, japanese_name, resource_entity))

        return endpoints

    def _create_list_endpoint(
        self,
        resource: str,
        japanese_name: str,
        resource_entity: Dict
    ) -> EndpointDefinition:
        """Create list endpoint with pagination, filtering, and sorting."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}"
        method = "GET"
        operation_id = f"list{resource}s"
        summary = f"{resource}一覧を取得"
        description = f"{japanese_name}の一覧を取得します。\n\n" \
                     f"ページネーション、フィルタリング、ソートに対応しています。"

        tags = [self._to_pascal_case(resource_plural)]

        # Generate query parameters
        query_parameters = self._generate_query_parameters(resource_entity)

        # Generate response schema (paginated list)
        response_schema = {
            'type': 'object',
            'required': ['total', 'limit', 'offset', resource_plural],
            'properties': {
                'total': {
                    'type': 'integer',
                    'description': '総件数',
                    'example': 150
                },
                'limit': {
                    'type': 'integer',
                    'description': '1ページあたりの件数',
                    'example': 50
                },
                'offset': {
                    'type': 'integer',
                    'description': 'スキップした件数',
                    'example': 0
                },
                resource_plural: {
                    'type': 'array',
                    'description': f'{japanese_name}のリスト',
                    'items': {
                        '$ref': f'#/components/schemas/{resource}'
                    }
                }
            }
        }

        return EndpointDefinition(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            query_parameters=query_parameters,
            response_schema=response_schema,
            requires_idempotency_key=False
        )

    def _create_get_endpoint(
        self,
        resource: str,
        japanese_name: str,
        resource_entity: Dict
    ) -> EndpointDefinition:
        """Create get endpoint for single resource retrieval."""
        resource_plural = self._pluralize(self._to_snake_case(resource))
        resource_singular = self._to_snake_case(resource)

        # Get primary key attribute
        pk_attr = self._get_primary_key_attribute(resource_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        path = f"/api/{resource_plural}/{{{pk_name}}}"
        method = "GET"
        operation_id = f"get{resource}"
        summary = f"{resource}詳細を取得"
        description = f"{japanese_name}の詳細情報を取得します。"

        tags = [self._to_pascal_case(resource_plural)]

        # Generate response schema
        response_schema = {
            '$ref': f'#/components/schemas/{resource}'
        }

        return EndpointDefinition(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            response_schema=response_schema,
            requires_idempotency_key=False
        )

    def _create_create_endpoint(
        self,
        resource: str,
        japanese_name: str,
        resource_entity: Dict
    ) -> EndpointDefinition:
        """Create create endpoint for resource creation."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}"
        method = "POST"
        operation_id = f"create{resource}"
        summary = f"新しい{resource}を作成"
        description = f"{japanese_name}を新規作成します。"

        tags = [self._to_pascal_case(resource_plural)]

        # Generate request body schema
        request_body_schema = self._generate_create_schema(resource_entity, f"{resource}CreateRequest")

        # Generate response schema
        response_schema = {
            '$ref': f'#/components/schemas/{resource}'
        }

        return EndpointDefinition(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            request_body_schema=request_body_schema,
            response_schema=response_schema,
            requires_idempotency_key=True
        )

    def _create_update_endpoint(
        self,
        resource: str,
        japanese_name: str,
        resource_entity: Dict
    ) -> EndpointDefinition:
        """Create update endpoint for partial resource update."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        # Get primary key attribute
        pk_attr = self._get_primary_key_attribute(resource_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        path = f"/api/{resource_plural}/{{{pk_name}}}"
        method = "PATCH"
        operation_id = f"update{resource}"
        summary = f"{resource}情報を部分更新"
        description = f"{japanese_name}の情報を部分更新します。\n\n" \
                     f"更新したいフィールドのみ指定してください。"

        tags = [self._to_pascal_case(resource_plural)]

        # Generate request body schema (all fields optional)
        request_body_schema = self._generate_update_schema(resource_entity, f"{resource}UpdateRequest")

        # Generate response schema
        response_schema = {
            '$ref': f'#/components/schemas/{resource}'
        }

        return EndpointDefinition(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            request_body_schema=request_body_schema,
            response_schema=response_schema,
            requires_idempotency_key=True
        )

    def _create_delete_endpoint(
        self,
        resource: str,
        japanese_name: str,
        resource_entity: Dict
    ) -> EndpointDefinition:
        """Create delete endpoint for soft delete."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        # Get primary key attribute
        pk_attr = self._get_primary_key_attribute(resource_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        path = f"/api/{resource_plural}/{{{pk_name}}}"
        method = "DELETE"
        operation_id = f"delete{resource}"
        summary = f"{resource}を削除"
        description = f"{japanese_name}を削除します（論理削除）。\n\n" \
                     f"イミュータブルデータモデルでは物理削除を行わず、DeletedAtフィールドに現在時刻を記録します。"

        tags = [self._to_pascal_case(resource_plural)]

        # Delete typically returns 204 No Content
        response_schema = None

        return EndpointDefinition(
            path=path,
            method=method,
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            response_schema=response_schema,
            requires_idempotency_key=False
        )

    def _generate_query_parameters(self, resource_entity: Dict) -> List[Dict]:
        """Generate query parameters for filtering, pagination, and sorting."""
        params = []

        # Add filter parameters for each attribute
        for attr in resource_entity.get('attributes', []):
            # Skip primary keys
            if attr.get('is_primary_key'):
                continue

            # Skip auto-generated fields
            if attr['english'] in ['CreatedAt', 'UpdatedAt', 'DeletedAt']:
                continue

            param_name = self._to_camel_case(attr['english'])
            attr_type = attr['type'].upper()

            # String attributes → Partial match
            if attr_type in ['VARCHAR', 'TEXT', 'CHAR']:
                params.append({
                    'name': param_name,
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string'},
                    'description': f"{attr['japanese']}（部分一致）"
                })

            # ID attributes → Exact match
            elif attr['english'].endswith('ID') and attr_type in ['INT', 'BIGINT']:
                params.append({
                    'name': param_name,
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'integer'},
                    'description': f"{attr['japanese']}でフィルタ"
                })

            # Date attributes → Range search
            elif attr_type == 'DATE':
                params.append({
                    'name': f"{param_name}From",
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string', 'format': 'date'},
                    'description': f"{attr['japanese']}範囲開始"
                })
                params.append({
                    'name': f"{param_name}To",
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string', 'format': 'date'},
                    'description': f"{attr['japanese']}範囲終了"
                })

            # Timestamp attributes → Range search
            elif attr_type == 'TIMESTAMP':
                params.append({
                    'name': f"{param_name}From",
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string', 'format': 'date-time'},
                    'description': f"{attr['japanese']}範囲開始"
                })
                params.append({
                    'name': f"{param_name}To",
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string', 'format': 'date-time'},
                    'description': f"{attr['japanese']}範囲終了"
                })

            # Boolean attributes → Exact match
            elif attr_type == 'BOOLEAN':
                params.append({
                    'name': param_name,
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'boolean'},
                    'description': f"{attr['japanese']}でフィルタ"
                })

        # Add pagination parameters
        params.append({
            'name': 'limit',
            'in': 'query',
            'required': False,
            'schema': {'type': 'integer', 'minimum': 1, 'maximum': 500, 'default': 50},
            'description': '1ページあたりの取得件数'
        })
        params.append({
            'name': 'offset',
            'in': 'query',
            'required': False,
            'schema': {'type': 'integer', 'minimum': 0, 'default': 0},
            'description': 'スキップする件数'
        })

        # Add sort parameter
        # Build sort enum from attributes
        sort_fields = []
        for attr in resource_entity.get('attributes', []):
            if not attr.get('is_primary_key'):
                field = self._to_camel_case(attr['english'])
                sort_fields.extend([field, f"-{field}"])

        params.append({
            'name': 'sort',
            'in': 'query',
            'required': False,
            'schema': {'type': 'string', 'enum': sort_fields, 'default': '-createdAt'},
            'description': 'ソート順（-プレフィックスで降順）'
        })

        return params

    def _generate_create_schema(self, resource_entity: Dict, schema_name: str) -> Dict:
        """Generate request body schema for resource creation."""
        properties = {}
        required = []

        for attr in resource_entity.get('attributes', []):
            # Skip primary key (auto-generated)
            if attr.get('is_primary_key'):
                continue

            # Skip auto-generated fields
            if attr['english'] in ['CreatedAt', 'UpdatedAt', 'DeletedAt']:
                continue

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

            # Assume non-nullable fields are required (simplified)
            # In practice, you'd check nullable flag
            if attr['english'].endswith('ID') or attr['japanese'].endswith('名'):
                required.append(prop_name)

        return {
            'type': 'object',
            'required': required,
            'properties': properties
        }

    def _generate_update_schema(self, resource_entity: Dict, schema_name: str) -> Dict:
        """Generate request body schema for resource update (all fields optional)."""
        properties = {}

        for attr in resource_entity.get('attributes', []):
            # Skip primary key
            if attr.get('is_primary_key'):
                continue

            # Skip auto-generated fields
            if attr['english'] in ['CreatedAt', 'UpdatedAt', 'DeletedAt']:
                continue

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

        return {
            'type': 'object',
            'properties': properties,
            'description': '更新したいフィールドのみ指定'
        }

    def _get_primary_key_attribute(self, resource_entity: Dict) -> Optional[Dict]:
        """Get primary key attribute from resource entity."""
        for attr in resource_entity.get('attributes', []):
            if attr.get('is_primary_key'):
                return attr
        return None

    def _map_sql_type_to_openapi(self, sql_type: str) -> str:
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

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert PascalCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert PascalCase to camelCase."""
        if not text:
            return text
        return text[0].lower() + text[1:]

    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in text.split('_'))

    @staticmethod
    def _pluralize(text: str) -> str:
        """Simple English pluralization."""
        if text.endswith('y') and text[-2] not in 'aeiou':
            return text[:-1] + 'ies'
        elif text.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return text + 'es'
        else:
            return text + 's'
