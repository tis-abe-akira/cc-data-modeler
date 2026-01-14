"""
Nablarch/Spring拡張機能

OpenAPI仕様書にNablarch/Spring向けのメタデータを追加する後処理モジュール
"""

from typing import Dict
from pathlib import Path
import sys

# nablarch_utils をインポート
sys.path.insert(0, str(Path(__file__).parent))
from nablarch_utils import DomainInferrer, PackageNameInferrer, DomainConstraintInferrer


class NablarchEnhancer:
    """
    Nablarch/Springメタデータ用のPost-processing拡張機能

    OpenAPI仕様書に以下の拡張を追加：
    1. ドメインアノテーション（x-field-extra-annotation）
    2. Tags構造の更新（[operationId, packageName]）
    3. 詳細な制約情報をdescriptionに追加
    """

    def __init__(self):
        """初期化"""
        pass

    def enhance(self, openapi_spec: Dict, entities_classified: Dict, model: Dict) -> Dict:
        """
        OpenAPI仕様書にNablarchメタデータを追加

        Args:
            openapi_spec: 生成されたOpenAPI仕様書（dict）
            entities_classified: エンティティ分類情報（dict）
            model: 完全なデータモデル（dict）

        Returns:
            拡張されたOpenAPI仕様書（dict）
        """
        # Phase 2: ドメインアノテーションと制約情報を追加
        self._add_domain_annotations(openapi_spec, entities_classified, model)

        # Phase 3: Tags構造を更新
        self._update_tags_structure(openapi_spec, entities_classified)

        return openapi_spec

    def _add_domain_annotations(self, openapi_spec: Dict, entities_classified: Dict, model: Dict) -> None:
        """
        全スキーマプロパティにx-field-extra-annotationと制約情報を追加

        処理内容：
        1. 全スキーマの全プロパティを走査
        2. 各プロパティに対して：
           - ドメイン名を推論（プロパティ名がcamelCaseのドメイン名）
           - フィールド情報を取得（PascalCase変換して検索）
           - 制約情報を推論（DomainConstraintInferrer）
           - x-field-extra-annotationを追加
           - descriptionを詳細な制約情報で拡張
        """
        # フィールド情報マップを構築
        field_info_map = self._build_field_info_map(entities_classified, model)

        # componentsスキーマを取得
        schemas = openapi_spec.get('components', {}).get('schemas', {})

        for schema_name, schema in schemas.items():
            if schema.get('type') != 'object':
                continue

            properties = schema.get('properties', {})

            for prop_name, prop_def in properties.items():
                # プロパティ名（camelCase）がそのままドメイン名
                domain_name = prop_name

                # プロパティ名をPascalCaseに変換してフィールド情報を検索
                pascal_case_name = self._camel_to_pascal(prop_name)
                field_info = field_info_map.get(pascal_case_name, {})

                # デフォルト値
                field_type = field_info.get('type', 'VARCHAR(255)')
                japanese_name = field_info.get('japanese', prop_name)
                is_primary_key = field_info.get('is_primary_key', False)
                nullable = field_info.get('nullable', False)

                # 制約情報を推論
                constraints = DomainConstraintInferrer.infer_constraints(
                    field_name=pascal_case_name if pascal_case_name else prop_name,
                    sql_type=field_type,
                    japanese_name=japanese_name,
                    nullable=nullable,
                    is_primary_key=is_primary_key
                )

                # x-field-extra-annotationを追加
                annotation = f'@nablarch.core.validation.ee.Domain("{domain_name}")'
                prop_def['x-field-extra-annotation'] = annotation

                # descriptionを詳細な制約情報で拡張
                enhanced_desc = self._build_enhanced_description(
                    japanese_name, domain_name, constraints
                )
                prop_def['description'] = enhanced_desc

    def _camel_to_pascal(self, camel_case: str) -> str:
        """
        camelCaseをPascalCaseに変換

        Args:
            camel_case: camelCase形式の文字列（例: projectName, projectID）

        Returns:
            PascalCase形式の文字列（例: ProjectName, ProjectID）
        """
        if not camel_case:
            return ''
        return camel_case[0].upper() + camel_case[1:]

    def _update_tags_structure(self, openapi_spec: Dict, entities_classified: Dict) -> None:
        """
        tagsを[operationId, packageName]フォーマットに更新

        処理内容：
        1. 全pathsの全メソッドを走査
        2. 各operationに対して：
           - operationIdを取得
           - pathからパッケージ名を推論
           - tagsを[operationId, packageName]に更新

        Before:
          tags: [Projects]

        After:
          tags: [listProjects, projects]
        """
        paths = openapi_spec.get('paths', {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                # operationIdを取得
                operation_id = operation.get('operationId')
                if not operation_id:
                    continue

                # pathからパッケージ名を推論
                package_name = self._infer_package_from_operation(
                    operation_id, path, entities_classified
                )

                # tagsを[operationId, packageName]フォーマットに更新
                operation['tags'] = [operation_id, package_name]

    def _enhance_descriptions(self, openapi_spec: Dict) -> None:
        """
        descriptionを詳細な制約情報で拡張

        Phase 2で実装予定（_add_domain_annotationsと統合される可能性あり）
        """
        pass

    def _build_field_info_map(self, entities_classified: Dict, model: Dict) -> Dict:
        """
        エンティティ情報からフィールド定義マップを構築

        Args:
            entities_classified: エンティティ分類情報
            model: 完全なデータモデル

        Returns:
            フィールド名（PascalCase）をキーとするフィールド情報のマップ
            例: {
                "ProjectID": {"japanese": "プロジェクトID", "english": "ProjectID",
                             "type": "INT", "is_primary_key": True, "nullable": False},
                "ProjectName": {"japanese": "プロジェクト名", "english": "ProjectName",
                               "type": "VARCHAR(200)", "is_primary_key": False, "nullable": False}
            }
        """
        field_map = {}

        # model.jsonからエンティティ情報を取得（entities_classifiedも同じ構造）
        entities = model.get('entities', [])

        for entity in entities:
            attributes = entity.get('attributes', [])
            for attr in attributes:
                field_name = attr.get('english', '')
                if not field_name:
                    continue

                # フィールド情報を格納
                field_map[field_name] = {
                    'japanese': attr.get('japanese', ''),
                    'english': field_name,
                    'type': attr.get('type', 'VARCHAR(255)'),
                    'is_primary_key': attr.get('is_primary_key', False),
                    # nullable情報がない場合はデフォルトでFalse（NOT NULL）とする
                    # ただし、主キーと作成日時フィールドは特別扱い
                    'nullable': attr.get('nullable', False)
                }

        return field_map

    def _build_enhanced_description(self, japanese_name: str, domain_name: str,
                                    constraints: Dict) -> str:
        """
        詳細な制約情報を含むdescriptionを構築

        Args:
            japanese_name: 日本語項目名
            domain_name: ドメイン名
            constraints: 制約情報（DomainConstraintInferrer.infer_constraints() の返り値）

        Returns:
            詳細な制約情報を含むdescription文字列

        Example:
            項目名: 会社名
            ドメイン: companyName
            制約:
              - 型: 文字列
              - 最大長: 256文字
              - 文字種: システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号）
              - 必須: はい
        """
        lines = [
            f"項目名: {japanese_name}",
            f"ドメイン: {domain_name}",
            "制約:"
        ]

        # 型情報
        if 'type' in constraints:
            lines.append(f"  - 型: {constraints['type']}")

        # 長さ制約
        if 'max_length' in constraints:
            lines.append(f"  - 最大長: {constraints['max_length']}文字")

        # 数値制約（DECIMAL用）
        if 'integer_digits' in constraints and 'decimal_digits' in constraints:
            lines.append(f"  - 整数部: 最大{constraints['integer_digits']}桁")
            lines.append(f"  - 小数部: {constraints['decimal_digits']}桁")

        # 文字種制約
        if 'charset' in constraints:
            lines.append(f"  - 文字種: {constraints['charset']}")

        # フォーマット制約
        if 'format_description' in constraints:
            lines.append(f"  - フォーマット: {constraints['format_description']}")
        elif 'pattern' in constraints:
            lines.append(f"  - パターン: {constraints.get('format_description', '正規表現')}")

        # 必須/任意
        required_text = "はい" if constraints.get('required', False) else "いいえ"
        lines.append(f"  - 必須: {required_text}")

        return "\n".join(lines)

    def _infer_package_from_operation(self, operation_id: str, path: str,
                                      entities_classified: Dict) -> str:
        """
        operationIdとpathからパッケージ名を推論

        Args:
            operation_id: オペレーションID（例: startProject）
            path: APIパス（例: /api/projects/{id}/start）
            entities_classified: エンティティ分類情報

        Returns:
            パッケージ名（例: projects）

        Phase 3で実装予定
        """
        # 暫定実装: pathから推論
        if '/api/' in path:
            parts = path.split('/')
            if len(parts) > 2:
                return parts[2]  # /api/projects/{id} → projects
        return 'common'
