"""
Nablarch/Spring拡張用のユーティリティクラス

このモジュールは以下の機能を提供：
- ドメイン名推論（フィールド名 → camelCase）
- パッケージ名推論（エンティティ名 → lowercase plural）
- 制約情報推論（SQL型 → バリデーション制約）
"""

import re
from typing import Dict, Optional


class DomainInferrer:
    """フィールド属性からNablarchドメイン名を推論"""

    @staticmethod
    def infer_domain_name(field_name: str, field_type: str = '', japanese_name: str = '') -> str:
        """
        フィールド名からドメイン名を推論

        ルール:
        1. PascalCaseのフィールド名をcamelCaseに変換
        2. IDフィールドは"ID"を大文字のまま保持

        Args:
            field_name: PascalCase形式のフィールド名（例: CompanyName, ProjectID）
            field_type: SQL型（未使用、後方互換性のため残す）
            japanese_name: 日本語名（未使用、後方互換性のため残す）

        Returns:
            camelCase形式のドメイン名

        Examples:
            >>> DomainInferrer.infer_domain_name('CompanyName')
            'companyName'
            >>> DomainInferrer.infer_domain_name('ProjectID')
            'projectID'
            >>> DomainInferrer.infer_domain_name('StartDateTime')
            'startDateTime'
        """
        if not field_name:
            return ''

        # IDフィールドの特別処理
        if field_name.endswith('ID'):
            base = field_name[:-2]  # 'ID'を除去
            if not base:  # フィールド名が'ID'だけの場合
                return 'id'
            camel_base = base[0].lower() + base[1:] if base else ""
            return f"{camel_base}ID"

        # 通常のcamelCase変換
        camel_case = field_name[0].lower() + field_name[1:]
        return camel_case


class PackageNameInferrer:
    """エンティティ名からパッケージ名を推論"""

    @staticmethod
    def infer_package_name(entity_name: str, entity_classification: str = 'resource') -> str:
        """
        エンティティからパッケージ名を推論

        ルール:
        1. イベントの場合: リソースを抽出（ProjectStart → Project）
        2. snake_caseに変換
        3. 複数形化
        4. 小文字で返す

        Args:
            entity_name: PascalCase形式のエンティティ名（例: Project, ProjectStart）
            entity_classification: 'resource' | 'event' | 'junction'

        Returns:
            lowercase plural形式のパッケージ名

        Examples:
            >>> PackageNameInferrer.infer_package_name('Project', 'resource')
            'projects'
            >>> PackageNameInferrer.infer_package_name('ProjectStart', 'event')
            'projects'
            >>> PackageNameInferrer.infer_package_name('PersonAssign', 'event')
            'persons'
        """
        if not entity_name:
            return ''

        # イベントの場合、リソース名を抽出
        if entity_classification == 'event':
            resource_name = PackageNameInferrer._extract_resource_from_event(entity_name)
        else:
            resource_name = entity_name

        # snake_caseに変換
        snake_case = PackageNameInferrer._to_snake_case(resource_name)

        # 複数形化
        plural = PackageNameInferrer._pluralize(snake_case)

        return plural.lower()

    @staticmethod
    def _extract_resource_from_event(event_name: str) -> str:
        """イベント名からリソース名を抽出"""
        patterns = [
            r'^(.+)(Start|Complete|Finish|Cancel|Evaluate|Assess|Approve|Reject)$',
            r'^(.+)Assign$',
            r'^(.+)Replace$',
        ]

        for pattern in patterns:
            match = re.match(pattern, event_name)
            if match:
                return match.group(1)

        # パターンにマッチしない場合はそのまま返す
        return event_name

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """PascalCaseをsnake_caseに変換"""
        # 連続する大文字の処理（例: ProjectID → project_id）
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # 小文字と大文字の境界に_を挿入
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _pluralize(word: str) -> str:
        """英単語を複数形化（簡易版）"""
        if not word:
            return word

        # 既に複数形の場合はそのまま
        if word.endswith('s'):
            return word

        # 不規則変化（よく使われるもののみ）
        irregular = {
            'person': 'persons',
            'child': 'children',
            'man': 'men',
            'woman': 'women',
        }

        if word in irregular:
            return irregular[word]

        # -y で終わる場合 → -ies
        if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'

        # -s, -x, -z, -ch, -sh で終わる場合 → -es
        if word.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return word + 'es'

        # デフォルト: -s を追加
        return word + 's'


class DomainConstraintInferrer:
    """DB定義から詳細な制約情報を推論"""

    @staticmethod
    def infer_constraints(field_name: str, sql_type: str, japanese_name: str = '',
                         nullable: bool = True, is_primary_key: bool = False) -> Dict:
        """
        フィールド情報から制約を推論

        Args:
            field_name: フィールド名（PascalCase）
            sql_type: SQL型（例: VARCHAR(256), DECIMAL(15,2), INT）
            japanese_name: 日本語項目名
            nullable: NULL許可フラグ
            is_primary_key: 主キーフラグ

        Returns:
            制約情報の辞書
            {
                'type': '文字列' | '数値' | '日時' | 'ブール値',
                'max_length': int,
                'precision': int,  # DECIMAL用
                'scale': int,      # DECIMAL用
                'integer_digits': int,  # DECIMAL用
                'decimal_digits': int,  # DECIMAL用
                'format': 'email' | 'uri' | 'date' | 'date-time',
                'format_description': str,
                'charset': 'システム許容文字' | 'ASCII文字',
                'required': bool,
                'pattern': str  # 正規表現パターン
            }
        """
        constraints = {}

        # 1. SQL型から基本情報を抽出
        constraints.update(DomainConstraintInferrer._parse_sql_type(sql_type))

        # 2. フィールド名からフォーマット制約を推論
        constraints.update(DomainConstraintInferrer._infer_format(field_name))

        # 3. 文字種制約を推論
        constraints['charset'] = DomainConstraintInferrer._infer_charset(field_name, japanese_name)

        # 4. 必須/任意を判定
        constraints['required'] = not nullable and not is_primary_key

        return constraints

    @staticmethod
    def _parse_sql_type(sql_type: str) -> Dict:
        """SQL型から制約を抽出"""
        if not sql_type:
            return {'type': '文字列'}

        sql_type_upper = sql_type.upper()

        # VARCHAR(n)
        if match := re.match(r'VARCHAR\((\d+)\)', sql_type_upper):
            return {
                'type': '文字列',
                'max_length': int(match.group(1))
            }

        # DECIMAL(p,s) または NUMERIC(p,s)
        if match := re.match(r'(?:DECIMAL|NUMERIC)\((\d+),(\d+)\)', sql_type_upper):
            precision = int(match.group(1))
            scale = int(match.group(2))
            return {
                'type': '数値（DECIMAL）',
                'precision': precision,
                'scale': scale,
                'integer_digits': precision - scale,
                'decimal_digits': scale
            }

        # INT, BIGINT, INTEGER, SMALLINT
        if sql_type_upper in ['INT', 'BIGINT', 'INTEGER', 'SMALLINT']:
            return {'type': '整数'}

        # TIMESTAMP, DATETIME
        if sql_type_upper in ['TIMESTAMP', 'DATETIME']:
            return {'type': '日時', 'format': 'date-time'}

        # DATE
        if sql_type_upper == 'DATE':
            return {'type': '日付', 'format': 'date'}

        # BOOLEAN, BOOL
        if sql_type_upper in ['BOOLEAN', 'BOOL']:
            return {'type': 'ブール値'}

        # TEXT
        if sql_type_upper == 'TEXT':
            return {'type': '文字列'}

        # デフォルト
        return {'type': '文字列'}

    @staticmethod
    def _infer_format(field_name: str) -> Dict:
        """フィールド名からフォーマット制約を推論"""
        if not field_name:
            return {}

        name_lower = field_name.lower()

        # メールアドレス
        if 'email' in name_lower or 'mail' in name_lower:
            return {
                'format': 'email',
                'format_description': 'メールアドレス形式（RFC 5322準拠）'
            }

        # URL
        if 'url' in name_lower or 'uri' in name_lower:
            return {
                'format': 'uri',
                'format_description': 'URL形式'
            }

        # 電話番号
        if 'phone' in name_lower or 'tel' in name_lower:
            return {
                'pattern': r'^\d{2,4}-?\d{2,4}-?\d{4}$',
                'format_description': '電話番号形式（ハイフンあり/なし）'
            }

        # 郵便番号
        if 'postal' in name_lower or 'zip' in name_lower:
            return {
                'pattern': r'^\d{3}-?\d{4}$',
                'format_description': '郵便番号形式（7桁、ハイフンあり/なし）'
            }

        return {}

    @staticmethod
    def _infer_charset(field_name: str, japanese_name: str) -> str:
        """文字種制約を推論"""
        if not field_name:
            return 'ASCII文字（英数字、記号）'

        name_lower = field_name.lower()

        # ID系、コード系 → 英数字のみ
        if name_lower.endswith('id') or name_lower.endswith('code'):
            return 'ASCII文字（英数字、記号）'

        # メールアドレス、URL → ASCII
        if any(kw in name_lower for kw in ['email', 'mail', 'url', 'uri']):
            return 'ASCII文字'

        # 日本語項目名がある → システム許容文字
        if japanese_name and any(ord(c) > 127 for c in japanese_name):
            return 'システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号）'

        # デフォルト: ASCII
        return 'ASCII文字（英数字、記号）'
