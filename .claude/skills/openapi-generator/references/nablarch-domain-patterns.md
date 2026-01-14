# Nablarch/Spring メタデータ拡張パターン

このドキュメントは、OpenAPI Generatorに実装されたNablarch/Spring統合パターンのリファレンスです。

## 概要

OpenAPI GeneratorにNablarch/Springフレームワーク統合パターンを追加する拡張機能を実装しました。

参考リポジトリ: https://github.com/tis-abe-akira/spring-rest-api

### 拡張内容

1. **ドメインバリデーションアノテーション**: 全プロパティに`x-field-extra-annotation`を追加
2. **詳細な制約情報**: DB定義から推論した制約情報をdescriptionに追加
3. **Tags構造拡張**: tags を`[operationId, packageName]`フォーマットに更新

---

## 使用方法

### 基本的な使い方

```bash
# Nablarch拡張なし（デフォルト）
python openapi_generator.py project-record-system

# Nablarch拡張あり
python openapi_generator.py project-record-system --enable-nablarch
```

### 出力例

**拡張前**:
```yaml
ProjectName:
  type: string
  description: プロジェクト名
```

**拡張後**:
```yaml
projectName:
  type: string
  description: |
    項目名: プロジェクト名
    ドメイン: projectName
    制約:
      - 型: 文字列
      - 最大長: 200文字
      - 文字種: システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号）
      - 必須: はい
  x-field-extra-annotation: '@nablarch.core.validation.ee.Domain("projectName")'
```

---

## ドメイン名推論パターン

### アルゴリズム

フィールド名（PascalCase）をcamelCaseに変換してドメイン名を推論します。

**ルール**:
1. 先頭文字を小文字に変換
2. IDフィールドは"ID"を大文字のまま保持

### 推論例

| フィールド名（PascalCase） | ドメイン名（camelCase） | 説明 |
|------------------------|---------------------|------|
| CompanyName | companyName | 通常のcamelCase変換 |
| ProjectID | projectID | 大文字ID保持 |
| EmailAddress | emailAddress | 通常のcamelCase変換 |
| StartDateTime | startDateTime | 通常のcamelCase変換 |
| ContractAmount | contractAmount | 通常のcamelCase変換 |
| ID | id | 単独のIDは小文字 |

### 実装コード

```python
class DomainInferrer:
    @staticmethod
    def infer_domain_name(field_name: str) -> str:
        if not field_name:
            return ''

        # IDフィールドの特別処理
        if field_name.endswith('ID'):
            base = field_name[:-2]
            if not base:
                return 'id'
            camel_base = base[0].lower() + base[1:] if base else ""
            return f"{camel_base}ID"

        # 通常のcamelCase変換
        return field_name[0].lower() + field_name[1:]
```

---

## パッケージ名推論パターン

### アルゴリズム

エンティティ名からパッケージ名を推論します。

**ルール**:
1. イベントの場合: リソース名を抽出（例: ProjectStart → Project）
2. snake_caseに変換
3. 複数形化
4. 小文字で返す

### 推論例

| エンティティ名 | 分類 | 抽出されたリソース | パッケージ名 |
|-----------|------|-----------------|------------|
| Project | resource | Project | projects |
| ProjectStart | event | Project | projects |
| PersonAssign | event | Person | persons |
| Customer | resource | Customer | customers |
| RiskEvaluate | event | Risk | risks |

### イベント名パターン

以下のサフィックスパターンでリソース名を抽出:

- **Start/Complete/Finish/Cancel**: ProjectStart → Project
- **Evaluate/Assess**: RiskEvaluate → Risk
- **Approve/Reject**: ApprovalApprove → Approval
- **Assign**: PersonAssign → Person
- **Replace**: PersonReplace → Person

### 実装コード

```python
class PackageNameInferrer:
    @staticmethod
    def infer_package_name(entity_name: str, entity_classification: str = 'resource') -> str:
        if entity_classification == 'event':
            resource_name = PackageNameInferrer._extract_resource_from_event(entity_name)
        else:
            resource_name = entity_name

        snake_case = PackageNameInferrer._to_snake_case(resource_name)
        plural = PackageNameInferrer._pluralize(snake_case)
        return plural.lower()
```

---

## 制約情報推論パターン

### アルゴリズム

DB定義（SQL型、nullable制約）とフィールド名から、詳細なバリデーション制約を推論します。

**推論レベル**:
1. **基本情報**: SQL型 → 型、長さ、精度
2. **フォーマット推論**: フィールド名 → email、URL、電話番号等
3. **文字種制約**: 日本語名、ID/Code → 許容文字種
4. **必須/任意**: nullable、is_primary_key → 必須フラグ

### SQL型パターン

#### VARCHAR(n)

| SQL型 | 推論される制約 |
|-------|-------------|
| VARCHAR(256) | 型: 文字列、最大長: 256文字 |
| VARCHAR(100) | 型: 文字列、最大長: 100文字 |

#### DECIMAL(p,s)

| SQL型 | 推論される制約 |
|-------|-------------|
| DECIMAL(15,2) | 型: 数値（DECIMAL）、整数部: 最大13桁、小数部: 2桁 |
| DECIMAL(10,2) | 型: 数値（DECIMAL）、整数部: 最大8桁、小数部: 2桁 |

#### INT/BIGINT

| SQL型 | 推論される制約 |
|-------|-------------|
| INT | 型: 整数 |
| BIGINT | 型: 整数 |

#### TIMESTAMP/DATE

| SQL型 | 推論される制約 |
|-------|-------------|
| TIMESTAMP | 型: 日時、フォーマット: date-time |
| DATE | 型: 日付、フォーマット: date |

#### BOOLEAN

| SQL型 | 推論される制約 |
|-------|-------------|
| BOOLEAN | 型: ブール値 |

### フォーマット推論パターン

フィールド名から特定のフォーマットを推論します。

| フィールド名パターン | 推論されるフォーマット | 制約説明 |
|----------------|---------------------|---------|
| *Email*, *Mail* | email | メールアドレス形式（RFC 5322準拠） |
| *URL*, *URI* | uri | URL形式 |
| *Phone*, *Tel* | パターン: `^\d{2,4}-?\d{2,4}-?\d{4}$` | 電話番号形式（ハイフンあり/なし） |
| *Postal*, *Zip* | パターン: `^\d{3}-?\d{4}$` | 郵便番号形式（7桁、ハイフンあり/なし） |

### 文字種制約パターン

| 条件 | 推論される文字種 |
|------|---------------|
| フィールド名が*ID、*Code | ASCII文字（英数字、記号） |
| フィールド名が*Email、*URL | ASCII文字 |
| 日本語項目名がある | システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号） |
| その他 | ASCII文字（英数字、記号） |

### 必須/任意判定パターン

```python
required = not nullable and not is_primary_key
```

| nullable | is_primary_key | 必須 | 理由 |
|----------|---------------|------|------|
| False | False | はい | 非NULL制約あり |
| True | False | いいえ | NULL許可 |
| False | True | いいえ | 主キーはリクエストに含めない |
| True | True | いいえ | 主キーはリクエストに含めない |

### 制約情報の例

#### 例1: 会社名（VARCHAR(256)、日本語）

```yaml
companyName:
  type: string
  description: |
    項目名: 会社名
    ドメイン: companyName
    制約:
      - 型: 文字列
      - 最大長: 256文字
      - 文字種: システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号）
      - 必須: はい
  x-field-extra-annotation: '@nablarch.core.validation.ee.Domain("companyName")'
```

#### 例2: メールアドレス（VARCHAR(64)、フォーマット推論）

```yaml
emailAddress:
  type: string
  description: |
    項目名: メールアドレス
    ドメイン: emailAddress
    制約:
      - 型: 文字列
      - 最大長: 64文字
      - 文字種: ASCII文字
      - フォーマット: メールアドレス形式（RFC 5322準拠）
      - 必須: はい
  x-field-extra-annotation: '@nablarch.core.validation.ee.Domain("emailAddress")'
```

#### 例3: 契約金額（DECIMAL(15,2)）

```yaml
contractAmount:
  type: number
  description: |
    項目名: 契約金額
    ドメイン: contractAmount
    制約:
      - 型: 数値（DECIMAL）
      - 整数部: 最大13桁
      - 小数部: 2桁
      - 必須: はい
  x-field-extra-annotation: '@nablarch.core.validation.ee.Domain("contractAmount")'
```

#### 例4: 電話番号（VARCHAR(15)、パターン推論）

```yaml
phoneNumber:
  type: string
  description: |
    項目名: 電話番号
    ドメイン: phoneNumber
    制約:
      - 型: 文字列
      - 最大長: 15文字
      - パターン: 電話番号形式（ハイフンあり/なし）
      - 必須: いいえ
  x-field-extra-annotation: '@nablarch.core.validation.ee.Domain("phoneNumber")'
```

---

## Tags構造パターン

### 変更内容

tagsを`[operationId, packageName]`フォーマットに更新します。

**変更前**:
```yaml
/api/projects:
  get:
    operationId: listProjects
    tags:
      - Projects
```

**変更後**:
```yaml
/api/projects:
  get:
    operationId: listProjects
    tags:
      - listProjects  # tags[0]: operationId（Controller識別子）
      - projects      # tags[1]: パッケージ名（コード生成用）
```

### 用途

- **tags[0]**: Controller名の識別子（operationId）
- **tags[1]**: パッケージ名（コード生成時のパッケージ配置）

### イベント操作の例

イベント操作もリソースパッケージにマップされます。

```yaml
/api/projects/{id}/start:
  post:
    operationId: startProject
    tags:
      - startProject  # operationId
      - projects      # リソースパッケージ（ProjectStart → projects）
```

```yaml
/api/persons/{id}/assign:
  post:
    operationId: assignPersonToProject
    tags:
      - assignPersonToProject  # operationId
      - projects               # リソースパッケージ
```

---

## 実装アーキテクチャ

### Post-Processing拡張パターン

Nablarchメタデータはコア OpenAPI生成後の**後処理ステップ**として追加されます。

```
OpenAPI生成フロー:
1. 基本OpenAPI仕様を生成
2. paths、schemas、tagsを構築
3. ★ Nablarch拡張フェーズ（--enable-nablarchフラグ時のみ）
   - スキーマプロパティにx-field-extra-annotationを追加
   - descriptionに詳細な制約情報を追加
   - tags構造を[operationId, packageName]に更新
4. openapi.yamlを出力
```

### モジュール構成

```
.claude/skills/openapi-generator/scripts/
├── openapi_generator.py    # メイン生成エンジン（機能フラグ統合）
├── nablarch_enhancer.py    # Nablarch拡張エンジン
├── nablarch_utils.py       # ユーティリティクラス
│   ├── DomainInferrer
│   ├── PackageNameInferrer
│   └── DomainConstraintInferrer
└── test_nablarch_utils.py  # ユニットテスト（32テストケース）
```

### NablarchEnhancerクラス

```python
class NablarchEnhancer:
    def enhance(self, openapi_spec, entities_classified, model):
        """Nablarchメタデータを追加"""
        # Phase 2: ドメインアノテーションと制約情報を追加
        self._add_domain_annotations(openapi_spec, entities_classified, model)

        # Phase 3: Tags構造を更新
        self._update_tags_structure(openapi_spec, entities_classified)

        return openapi_spec
```

---

## テスト結果

### ユニットテスト

32個のユニットテストが全てパスしています。

```bash
$ python test_nablarch_utils.py
Ran 32 tests in 0.001s
OK
```

**テストカバレッジ**:
- DomainInferrer: 5テスト
- PackageNameInferrer: 9テスト
- DomainConstraintInferrer: 18テスト

### 統合テスト（project-record-system）

**プロジェクト**: 18エンティティ（11リソース、7イベント）

**結果**:
- ✅ 全スキーマプロパティ（約150プロパティ）にx-field-extra-annotationが追加
- ✅ 全プロパティに詳細な制約情報を含むdescriptionが追加
- ✅ 全50エンドポイント（84操作）のtagsが[operationId, packageName]フォーマットに更新
- ✅ 全イベント操作がリソースパッケージに正しくマップ

---

## 制限事項と将来の拡張

### 現在の制限事項

1. **ドメイン名の衝突**: 同じドメイン名だが異なる検証ルールを持つ複数のフィールドがある場合、手動調整が必要
2. **複雑なイベント名**: パターンマッチングで認識されないイベント名は"common"パッケージにマップされる
3. **nullable情報**: model.jsonにnullable情報がない場合、デフォルトでFalse（NOT NULL）として扱われる

### 将来の拡張候補

1. **DomainBean.java生成**: ドメイン定義をJavaクラスとして出力
2. **カスタムドメインマッピング**: ユーザー定義のドメイン名マッピング設定
3. **追加のバリデーションルール**: 最小値/最大値、正規表現パターンの詳細化
4. **Spring Controller生成**: OpenAPI仕様書からSpring REST Controllerのスケルトンコード生成

---

## 参考資料

- [spring-rest-api リポジトリ](https://github.com/tis-abe-akira/spring-rest-api)
- [Nablarch Framework ドキュメント](https://nablarch.github.io/docs/5u21/doc/)
- [OpenAPI 3.1.0 Specification](https://spec.openapis.org/oas/v3.1.0)
- [RFC 7807: Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)

---

## 更新履歴

### 2026-01-12
- 初版作成
- Phase 1〜3の実装完了
  - ドメイン名推論
  - パッケージ名推論
  - 制約情報推論
  - Tags構造更新
- ユニットテスト（32テストケース）全パス
- project-record-systemでの統合テスト成功
