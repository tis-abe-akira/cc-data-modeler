"""
Event Entity to API Endpoint Mapper

This module converts event entities from entities_classified.json to OpenAPI endpoint definitions.
Implements pattern matching for various event types (Start, Complete, Assign, Replace, etc.)
and generates appropriate HTTP methods, paths, and schemas.
"""

import re
from typing import Dict, List, Optional, Tuple
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
    request_body_schema: Optional[Dict]
    response_schema: Optional[Dict]
    requires_idempotency_key: bool = True


class EventMapper:
    """Maps event entities to API endpoints."""

    # Event pattern definitions
    PATTERNS = {
        'Start': r'^(.+)Start$',
        'Complete': r'^(.+)Complete$',
        'Finish': r'^(.+)Finish$',
        'Cancel': r'^(.+)Cancel$',
        'Abort': r'^(.+)Abort$',
        'Assign': r'^(.+)Assign$',
        'Replace': r'^(.+)Replace$',
        'Evaluate': r'^(.+)Evaluate$',
        'Assess': r'^(.+)Assess$',
        'Approve': r'^(.+)Approve$',
        'Reject': r'^(.+)Reject$',
        'Create': r'^(.+)Create$',
        'Update': r'^(.+)Update$',
    }

    def __init__(self):
        """Initialize EventMapper."""
        pass

    def map_event_to_endpoint(self, event_entity: Dict) -> EndpointDefinition:
        """
        Map an event entity to an API endpoint definition.

        Args:
            event_entity: Event entity from entities_classified.json

        Returns:
            EndpointDefinition object
        """
        english_name = event_entity['english']
        japanese_name = event_entity['japanese']

        # Try to match event pattern
        for pattern_name, pattern_regex in self.PATTERNS.items():
            match = re.match(pattern_regex, english_name)
            if match:
                resource_name = match.group(1)
                return self._create_endpoint_for_pattern(
                    pattern_name,
                    resource_name,
                    japanese_name,
                    event_entity
                )

        # Fallback: generic event endpoint
        return self._create_generic_event_endpoint(english_name, japanese_name, event_entity)

    def _create_endpoint_for_pattern(
        self,
        pattern: str,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint definition for a specific pattern."""

        # Dispatch to pattern-specific methods
        pattern_methods = {
            'Start': self._create_start_endpoint,
            'Complete': self._create_complete_endpoint,
            'Finish': self._create_complete_endpoint,  # Same as Complete
            'Cancel': self._create_cancel_endpoint,
            'Abort': self._create_cancel_endpoint,  # Same as Cancel
            'Assign': self._create_assign_endpoint,
            'Replace': self._create_replace_endpoint,
            'Evaluate': self._create_evaluate_endpoint,
            'Assess': self._create_evaluate_endpoint,  # Same as Evaluate
            'Approve': self._create_approve_endpoint,
            'Reject': self._create_reject_endpoint,
            'Create': self._create_create_endpoint,
            'Update': self._create_update_endpoint,
        }

        method = pattern_methods.get(pattern)
        if method:
            return method(resource, japanese_name, event_entity)

        # Fallback
        return self._create_generic_event_endpoint(
            event_entity['english'],
            japanese_name,
            event_entity
        )

    def _create_start_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Start pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))
        action = 'start'

        path = f"/api/{resource_plural}/{{id}}/{action}"
        method = "POST"
        operation_id = f"{action}{resource}"
        summary = f"{resource}を開始する"
        description = f"{japanese_name}イベントを記録します。\n\n" \
                     f"このエンドポイントは{resource}リソースの開始を記録するビジネスイベントです。"

        tags = [self._to_pascal_case(resource_plural)]

        # Generate request body schema
        request_body_schema = self._generate_command_schema(event_entity, f"{resource}StartCommand")

        # Generate response schema
        response_schema = self._generate_response_schema(event_entity, f"{resource}StartResponse")

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

    def _create_complete_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Complete/Finish pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))
        action = 'complete' if 'Complete' in event_entity['english'] else 'finish'

        path = f"/api/{resource_plural}/{{id}}/{action}"
        method = "POST"
        operation_id = f"{action}{resource}"
        summary = f"{resource}を完了する"
        description = f"{japanese_name}イベントを記録します。"

        tags = [self._to_pascal_case(resource_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}{action.capitalize()}Command"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}{action.capitalize()}Response"
        )

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

    def _create_cancel_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Cancel/Abort pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))
        action = 'cancel' if 'Cancel' in event_entity['english'] else 'abort'

        path = f"/api/{resource_plural}/{{id}}/{action}"
        method = "POST"
        operation_id = f"{action}{resource}"
        summary = f"{resource}をキャンセルする"
        description = f"{japanese_name}イベントを記録します。\n\n" \
                     f"注意: 通常、キャンセル理由（reason）が必須です。"

        tags = [self._to_pascal_case(resource_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}{action.capitalize()}Command"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}{action.capitalize()}Response"
        )

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

    def _create_assign_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Assign pattern."""
        # Extract subject from resource name
        # E.g., "Person" from "PersonAssign"
        subject = resource
        subject_plural = self._pluralize(self._to_snake_case(subject))

        # Infer the parent resource (e.g., "Project" for "PersonAssign")
        # This requires looking at entity attributes (ProjectID, etc.)
        parent_resource = self._infer_parent_resource(event_entity)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))

        # Use semantic naming for members
        if subject.lower() == 'person':
            subject_plural = 'members'

        path = f"/api/{parent_resource_plural}/{{id}}/{subject_plural}"
        method = "POST"
        operation_id = f"assign{subject}To{parent_resource}"
        summary = f"{parent_resource}に{subject}をアサインする"
        description = f"{japanese_name}を記録します。"

        tags = [self._to_pascal_case(parent_resource_plural), self._to_pascal_case(subject_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{subject}AssignCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{subject}AssignResponse"
        )

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

    def _create_replace_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Replace pattern."""
        subject = resource
        subject_plural = self._pluralize(self._to_snake_case(subject))

        parent_resource = self._infer_parent_resource(event_entity)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))

        # Use semantic naming
        if subject.lower() == 'person':
            subject_plural = 'members'
            subject_singular = 'member'
        else:
            subject_singular = self._to_snake_case(subject)

        path = f"/api/{parent_resource_plural}/{{id}}/{subject_plural}/{{{subject_singular}Id}}/replace"
        method = "PUT"
        operation_id = f"replace{subject}In{parent_resource}"
        summary = f"{parent_resource}の{subject}を交代させる"
        description = f"{japanese_name}イベントを記録します。\n\n" \
                     f"注意: 新しい{subject}がnullの場合、離脱として扱います。"

        tags = [self._to_pascal_case(parent_resource_plural), self._to_pascal_case(subject_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{subject}ReplaceCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{subject}ReplaceResponse"
        )

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

    def _create_evaluate_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Evaluate/Assess pattern."""
        # Extract evaluation subject (e.g., "Risk" from "RiskEvaluate")
        evaluation_subject = resource
        evaluation_subject_plural = self._pluralize(self._to_snake_case(evaluation_subject))

        # Infer parent resource
        parent_resource = self._infer_parent_resource(event_entity)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))

        action = 'evaluate' if 'Evaluate' in event_entity['english'] else 'assess'

        path = f"/api/{parent_resource_plural}/{{id}}/{evaluation_subject_plural}"
        method = "POST"
        operation_id = f"{action}{evaluation_subject}For{parent_resource}"
        summary = f"{parent_resource}の{evaluation_subject}を評価する"
        description = f"{japanese_name}イベントを記録します。"

        tags = [self._to_pascal_case(parent_resource_plural), self._to_pascal_case(evaluation_subject_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{evaluation_subject}{action.capitalize()}Command"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{evaluation_subject}{action.capitalize()}Response"
        )

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

    def _create_approve_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Approve pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}/{{id}}/approve"
        method = "POST"
        operation_id = f"approve{resource}"
        summary = f"{resource}を承認する"
        description = f"{japanese_name}イベントを記録します。"

        tags = [self._to_pascal_case(resource_plural), "Approvals"]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}ApproveCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}ApproveResponse"
        )

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

    def _create_reject_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Reject pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}/{{id}}/reject"
        method = "POST"
        operation_id = f"reject{resource}"
        summary = f"{resource}を却下する"
        description = f"{japanese_name}イベントを記録します。\n\n" \
                     f"注意: 通常、却下理由（reason）が必須です。"

        tags = [self._to_pascal_case(resource_plural), "Approvals"]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}RejectCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}RejectResponse"
        )

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

    def _create_create_endpoint(
        self,
        resource: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Create pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}"
        method = "POST"
        operation_id = f"create{resource}"
        summary = f"新しい{resource}を作成する"
        description = f"{japanese_name}を記録します。"

        tags = [self._to_pascal_case(resource_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}CreateCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}CreateResponse"
        )

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
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create endpoint for Update pattern."""
        resource_plural = self._pluralize(self._to_snake_case(resource))

        path = f"/api/{resource_plural}/{{id}}"
        method = "PATCH"
        operation_id = f"update{resource}"
        summary = f"{resource}情報を部分更新する"
        description = f"{japanese_name}を記録します。\n\n" \
                     f"注意: イミュータブルデータモデルでは、可能な限り特定のアクションイベント（Start, Complete など）を使用することを推奨します。"

        tags = [self._to_pascal_case(resource_plural)]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{resource}UpdateCommand"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{resource}UpdateResponse"
        )

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

    def _create_generic_event_endpoint(
        self,
        english_name: str,
        japanese_name: str,
        event_entity: Dict
    ) -> EndpointDefinition:
        """Create generic event endpoint for unmatched patterns."""
        parent_resource = self._infer_parent_resource(event_entity)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))

        path = f"/api/{parent_resource_plural}/{{id}}/events"
        method = "POST"
        operation_id = f"record{english_name}"
        summary = f"{japanese_name}を記録する"
        description = f"{japanese_name}イベントを記録します。"

        tags = [self._to_pascal_case(parent_resource_plural), "Events"]

        request_body_schema = self._generate_command_schema(
            event_entity,
            f"{english_name}Command"
        )
        response_schema = self._generate_response_schema(
            event_entity,
            f"{english_name}Response"
        )

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

    def _generate_command_schema(self, event_entity: Dict, schema_name: str) -> Dict:
        """Generate Command schema from event entity attributes."""
        properties = {}
        required = []

        for attr in event_entity.get('attributes', []):
            # Skip primary key and auto-generated fields
            if attr.get('is_primary_key') or attr['english'] in ['CreatedAt', 'UpdatedAt']:
                continue

            # Skip foreign key to parent resource (it's in the path)
            if attr['english'].endswith('ID') and self._is_foreign_key_to_parent(attr, event_entity):
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

            properties[prop_name] = prop_def

            # Assume all non-nullable fields are required (simplified)
            required.append(prop_name)

        return {
            'type': 'object',
            'required': required,
            'properties': properties
        }

    def _generate_response_schema(self, event_entity: Dict, schema_name: str) -> Dict:
        """Generate Response schema from event entity attributes."""
        properties = {}

        for attr in event_entity.get('attributes', []):
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

            properties[prop_name] = prop_def

        # Add createdAt for event recording timestamp
        properties['createdAt'] = {
            'type': 'string',
            'format': 'date-time',
            'description': 'イベント記録日時'
        }

        return {
            'type': 'object',
            'properties': properties
        }

    def _infer_parent_resource(self, event_entity: Dict) -> str:
        """Infer parent resource from entity attributes (e.g., ProjectID → Project)."""
        for attr in event_entity.get('attributes', []):
            if attr['english'].endswith('ID') and not attr.get('is_primary_key'):
                # First foreign key is likely the parent resource
                return attr['english'][:-2]  # Remove 'ID' suffix

        # Fallback: extract from entity name
        english_name = event_entity['english']
        for pattern_regex in self.PATTERNS.values():
            match = re.match(pattern_regex, english_name)
            if match:
                return match.group(1)

        return 'Resource'  # Ultimate fallback

    def _is_foreign_key_to_parent(self, attr: Dict, event_entity: Dict) -> bool:
        """Check if attribute is a foreign key to the parent resource."""
        parent_resource = self._infer_parent_resource(event_entity)
        return attr['english'] == f"{parent_resource}ID"

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
