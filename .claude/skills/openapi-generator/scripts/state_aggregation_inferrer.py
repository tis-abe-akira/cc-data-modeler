"""
State Aggregation Query Inferrer

This module automatically infers state aggregation query endpoints from event entities.
Implements four patterns:
1. Latest State - Get the most recent event
2. History - Get all events in chronological order
3. Current Assignments - Get current assignments excluding replaced ones
4. Summary - Get aggregated statistics from events
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AggregationEndpointDefinition:
    """Represents a state aggregation query endpoint."""
    path: str
    method: str
    operation_id: str
    summary: str
    description: str
    tags: List[str]
    query_parameters: Optional[List[Dict]] = None
    response_schema: Optional[Dict] = None


class StateAggregationInferrer:
    """Infers state aggregation query endpoints from event entities."""

    def __init__(self):
        """Initialize StateAggregationInferrer."""
        pass

    def infer_aggregation_endpoints(
        self,
        event_entities: List[Dict],
        all_entities: List[Dict]
    ) -> List[AggregationEndpointDefinition]:
        """
        Infer aggregation endpoints from event entities.

        Args:
            event_entities: List of event entities
            all_entities: All entities (for cross-reference)

        Returns:
            List of AggregationEndpointDefinition objects
        """
        endpoints = []

        for event_entity in event_entities:
            # Pattern 1 & 2: Latest State and History (for all events with datetime)
            if self._has_datetime_attribute(event_entity):
                endpoints.extend(self._create_latest_and_history_endpoints(event_entity))

            # Pattern 3: Current Assignments (for Assign/Replace pairs)
            if event_entity['english'].endswith('Assign'):
                corresponding_replace = self._find_replace_for_assign(event_entity, event_entities)
                if corresponding_replace:
                    endpoints.append(
                        self._create_current_assignments_endpoint(event_entity, corresponding_replace)
                    )

            # Pattern 4: Summary (for all events)
            endpoints.append(self._create_summary_endpoint(event_entity))

        return endpoints

    def _has_datetime_attribute(self, event_entity: Dict) -> bool:
        """Check if event entity has a datetime attribute."""
        return event_entity.get('datetime_attribute') is not None

    def _find_replace_for_assign(
        self,
        assign_entity: Dict,
        event_entities: List[Dict]
    ) -> Optional[Dict]:
        """Find corresponding Replace event for an Assign event."""
        # Extract subject from Assign event (e.g., "Person" from "PersonAssign")
        assign_name = assign_entity['english']
        if not assign_name.endswith('Assign'):
            return None

        subject = assign_name[:-6]  # Remove "Assign"
        replace_name = f"{subject}Replace"

        # Find Replace event
        for entity in event_entities:
            if entity['english'] == replace_name:
                return entity

        return None

    def _create_latest_and_history_endpoints(
        self,
        event_entity: Dict
    ) -> List[AggregationEndpointDefinition]:
        """Create Latest State and History endpoints."""
        endpoints = []

        english_name = event_entity['english']
        japanese_name = event_entity['japanese']

        # Infer parent resource and action
        parent_resource, action = self._extract_resource_and_action(english_name)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))
        action_snake = self._to_snake_case(action)

        # Get primary key
        pk_attr = self._get_primary_key_attribute(event_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        # Get datetime attribute
        datetime_attr = event_entity.get('datetime_attribute')
        if not datetime_attr:
            return endpoints

        # 1. Latest State Endpoint
        latest_path = f"/api/{parent_resource_plural}/{{{pk_name}}}/{action_snake}/latest"
        latest_endpoint = AggregationEndpointDefinition(
            path=latest_path,
            method="GET",
            operation_id=f"get{parent_resource}Latest{action}",
            summary=f"{parent_resource}の最新の{japanese_name}情報を取得",
            description=f"{parent_resource}の最新の{japanese_name}情報を取得します。\n\n"
                       f"SQL例:\n"
                       f"```sql\n"
                       f"SELECT * FROM {event_entity['english'].upper()}\n"
                       f"WHERE {parent_resource}ID = ?\n"
                       f"ORDER BY {datetime_attr['english']} DESC\n"
                       f"LIMIT 1;\n"
                       f"```",
            tags=[self._to_pascal_case(parent_resource_plural)],
            response_schema={'$ref': f'#/components/schemas/{english_name}'}
        )
        endpoints.append(latest_endpoint)

        # 2. History Endpoint
        history_path = f"/api/{parent_resource_plural}/{{{pk_name}}}/{action_snake}/history"

        # Add pagination parameters
        history_params = [
            {
                'name': 'limit',
                'in': 'query',
                'required': False,
                'schema': {'type': 'integer', 'minimum': 1, 'maximum': 500, 'default': 50},
                'description': '取得件数'
            },
            {
                'name': 'offset',
                'in': 'query',
                'required': False,
                'schema': {'type': 'integer', 'minimum': 0, 'default': 0},
                'description': 'スキップ件数'
            }
        ]

        history_endpoint = AggregationEndpointDefinition(
            path=history_path,
            method="GET",
            operation_id=f"get{parent_resource}{action}History",
            summary=f"{parent_resource}の{japanese_name}履歴を取得",
            description=f"{parent_resource}の{japanese_name}履歴を時系列順で取得します。\n\n"
                       f"SQL例:\n"
                       f"```sql\n"
                       f"SELECT * FROM {event_entity['english'].upper()}\n"
                       f"WHERE {parent_resource}ID = ?\n"
                       f"ORDER BY {datetime_attr['english']} ASC\n"
                       f"LIMIT ? OFFSET ?;\n"
                       f"```",
            tags=[self._to_pascal_case(parent_resource_plural)],
            query_parameters=history_params,
            response_schema={
                'type': 'object',
                'properties': {
                    'total': {'type': 'integer', 'description': '総件数'},
                    'limit': {'type': 'integer', 'description': '取得件数'},
                    'offset': {'type': 'integer', 'description': 'スキップ件数'},
                    'events': {
                        'type': 'array',
                        'items': {'$ref': f'#/components/schemas/{english_name}'}
                    }
                }
            }
        )
        endpoints.append(history_endpoint)

        return endpoints

    def _create_current_assignments_endpoint(
        self,
        assign_entity: Dict,
        replace_entity: Dict
    ) -> AggregationEndpointDefinition:
        """Create Current Assignments endpoint (excluding replaced ones)."""
        assign_name = assign_entity['english']
        japanese_name = assign_entity['japanese']

        # Extract subject (e.g., "Person" from "PersonAssign")
        subject = assign_name[:-6]  # Remove "Assign"
        subject_plural = self._pluralize(self._to_snake_case(subject))

        # Use semantic naming
        if subject.lower() == 'person':
            subject_plural = 'members'

        # Infer parent resource
        parent_resource = self._infer_parent_resource(assign_entity)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))

        # Get primary key
        pk_attr = self._get_primary_key_attribute(assign_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        path = f"/api/{parent_resource_plural}/{{{pk_name}}}/{subject_plural}/current"

        description = f"{parent_resource}の現在の{subject}アサイン状況を取得します。\n\n" \
                     f"置換済みのアサインを除外した現在のメンバー一覧を返します。\n\n" \
                     f"SQL例:\n" \
                     f"```sql\n" \
                     f"SELECT pa.*, p.*\n" \
                     f"FROM {assign_name.upper()} pa\n" \
                     f"JOIN {subject.upper()} p ON pa.{subject}ID = p.{subject}ID\n" \
                     f"WHERE pa.{parent_resource}ID = ?\n" \
                     f"  AND NOT EXISTS (\n" \
                     f"    SELECT 1 FROM {replace_entity['english'].upper()} pr\n" \
                     f"    WHERE pr.{parent_resource}ID = pa.{parent_resource}ID\n" \
                     f"      AND pr.Old{subject}ID = pa.{subject}ID\n" \
                     f"  );\n" \
                     f"```"

        return AggregationEndpointDefinition(
            path=path,
            method="GET",
            operation_id=f"get{parent_resource}Current{subject}s",
            summary=f"{parent_resource}の現在の{japanese_name}状況を取得",
            description=description,
            tags=[self._to_pascal_case(parent_resource_plural), self._to_pascal_case(subject_plural)],
            response_schema={
                'type': 'object',
                'properties': {
                    f'{parent_resource.lower()}ID': {'type': 'integer'},
                    f'current{subject}s': {
                        'type': 'array',
                        'items': {'$ref': f'#/components/schemas/{assign_name}'}
                    }
                }
            }
        )

    def _create_summary_endpoint(self, event_entity: Dict) -> AggregationEndpointDefinition:
        """Create Summary aggregation endpoint."""
        english_name = event_entity['english']
        japanese_name = event_entity['japanese']

        # Infer parent resource and action
        parent_resource, action = self._extract_resource_and_action(english_name)
        parent_resource_plural = self._pluralize(self._to_snake_case(parent_resource))
        action_snake = self._to_snake_case(action)

        # Get primary key
        pk_attr = self._get_primary_key_attribute(event_entity)
        pk_name = self._to_camel_case(pk_attr['english']) if pk_attr else 'id'

        path = f"/api/{parent_resource_plural}/{{{pk_name}}}/{action_snake}/summary"

        # Get datetime attribute for aggregation
        datetime_attr = event_entity.get('datetime_attribute')
        datetime_field = datetime_attr['english'] if datetime_attr else 'CreatedAt'

        description = f"{parent_resource}の{japanese_name}サマリーを取得します。\n\n" \
                     f"イベントの統計情報を集約して返します。\n\n" \
                     f"SQL例:\n" \
                     f"```sql\n" \
                     f"SELECT\n" \
                     f"  {parent_resource}ID,\n" \
                     f"  COUNT(*) as eventCount,\n" \
                     f"  MAX({datetime_field}) as latestEvent,\n" \
                     f"  MIN({datetime_field}) as firstEvent\n" \
                     f"FROM {english_name.upper()}\n" \
                     f"WHERE {parent_resource}ID = ?\n" \
                     f"GROUP BY {parent_resource}ID;\n" \
                     f"```"

        return AggregationEndpointDefinition(
            path=path,
            method="GET",
            operation_id=f"get{parent_resource}{action}Summary",
            summary=f"{parent_resource}の{japanese_name}サマリーを取得",
            description=description,
            tags=[self._to_pascal_case(parent_resource_plural)],
            response_schema={
                'type': 'object',
                'properties': {
                    f'{parent_resource.lower()}ID': {
                        'type': 'integer',
                        'description': f'{parent_resource}ID'
                    },
                    'eventCount': {
                        'type': 'integer',
                        'description': 'イベント発生回数'
                    },
                    'latestEvent': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '最新イベント日時'
                    },
                    'firstEvent': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': '初回イベント日時'
                    }
                }
            }
        )

    def _extract_resource_and_action(self, event_name: str) -> Tuple[str, str]:
        """
        Extract resource and action from event name.

        E.g., "ProjectStart" → ("Project", "Start")
        """
        # Common patterns
        patterns = [
            r'^(.+)(Start|Complete|Finish|Cancel|Abort|Evaluate|Assess|Approve|Reject|Create|Update)$',
            r'^(.+)Assign$',
            r'^(.+)Replace$',
        ]

        for pattern in patterns:
            match = re.match(pattern, event_name)
            if match:
                if len(match.groups()) == 2:
                    return match.group(1), match.group(2)
                elif len(match.groups()) == 1:
                    # Assign/Replace pattern
                    action = 'Assign' if 'Assign' in event_name else 'Replace'
                    return match.group(1), action

        # Fallback: entire name as resource
        return event_name, 'Event'

    def _infer_parent_resource(self, event_entity: Dict) -> str:
        """Infer parent resource from entity attributes."""
        for attr in event_entity.get('attributes', []):
            if attr['english'].endswith('ID') and not attr.get('is_primary_key'):
                # First foreign key is likely the parent resource
                return attr['english'][:-2]  # Remove 'ID' suffix

        # Fallback
        resource, _ = self._extract_resource_and_action(event_entity['english'])
        return resource

    def _get_primary_key_attribute(self, entity: Dict) -> Optional[Dict]:
        """Get primary key attribute from entity."""
        for attr in entity.get('attributes', []):
            if attr.get('is_primary_key'):
                return attr
        return None

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
