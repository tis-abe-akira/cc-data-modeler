---
name: relationship-analyzer
description: エンティティ間の関連を分析し、カーディナリティと交差エンティティを決定します
version: 1.0.0
parent_skill: data-modeler
---

# Relationship Analyzer Knowledge Source

エンティティ間の関連を分析し、適切なカーディナリティと交差エンティティを決定します。

## 処理内容

1. リソース間の関連を分析
2. イベントと関連リソースの紐付け
3. カーディナリティの決定（1:1, 1:N, M:N）
4. 多対多の関係に交差エンティティを導入
5. 外部キー制約の定義

## 交差エンティティの導入基準

### 多対多の関係

**導入が必要なケース:**
- 学生 ↔ 講義（履修関係）
- 商品 ↔ 注文（注文明細）
- 医師 ↔ 患者（診察記録）

**交差エンティティ:**
- 履修
- 注文明細
- 診察

### 依存度が強すぎる場合

リソース同士の依存が強く、関連自体が重要な情報を持つ場合も交差エンティティを導入します。

**例: 社員と部署**
- 単純な関連: 社員 → 部署（1:N）
- 交差エンティティ導入: 社員 → 所属 → 部署
  - 所属には「配属日」「役職」などの属性を持たせる

## 入力

- `/tmp/data-modeler-blackboard/entities_classified.json`

## 出力

- `/tmp/data-modeler-blackboard/model.json`

```json
{
  "entities": {
    "resources": [...],
    "events": [...]
  },
  "relationships": [
    {
      "id": "rel_001",
      "from_entity": "Customer",
      "to_entity": "Invoice",
      "cardinality": "1:N",
      "relationship_type": "has",
      "foreign_key": {
        "table": "Invoice",
        "column": "CustomerID",
        "references": "Customer.CustomerID"
      }
    }
  ],
  "cross_entities": [
    {
      "name": "OrderDetail",
      "japanese": "注文明細",
      "connects": ["Order", "Product"],
      "attributes": ["数量", "単価", "小計"],
      "reason": "注文と商品の多対多関係を解消"
    }
  ]
}
```

## カーディナリティの決定

### 1:1（一対一）
- 社員 ← → 社員証
- 国 ← → 首都

### 1:N（一対多）
- 顧客 → 注文（1人の顧客は複数の注文を持つ）
- 部署 → 社員（1つの部署に複数の社員が所属）

### M:N（多対多）→ 交差エンティティで解消
- 学生 ← 履修 → 講義
- 商品 ← 注文明細 → 注文

## イベントとリソースの関連

イベントは必ず関連するリソースを参照します。

**例: 請求書送付イベント**
```
InvoiceSend (イベント)
  ├─ CustomerID (FK) → Customer
  ├─ InvoiceNumber (FK) → Invoice
  └─ SendDateTime (日時属性)
```

## 実装例

```python
def analyze_relationships(classified_entities: dict) -> dict:
    """
    エンティティ間の関連を分析
    """
    
    prompt = f"""
以下の分類済みエンティティに対して、関連を分析してください。

【エンティティ】
{json.dumps(classified_entities, ensure_ascii=False, indent=2)}

【分析項目】
1. リソース間の関連とカーディナリティ
2. イベントと関連リソースの紐付け
3. 多対多の関係に対する交差エンティティの提案
4. 外部キー制約の定義

【交差エンティティ導入基準】
- 多対多の関係がある場合
- 関連自体が重要な属性を持つ場合

【出力形式】
{{
  "relationships": [...],
  "cross_entities": [...]
}}
"""
    
    # Claude APIで処理
    return result
```

## 検証項目

- [ ] すべてのイベントが関連リソースを持つ
- [ ] 多対多の関係が交差エンティティで解消されている
- [ ] 外部キー制約が適切に定義されている
- [ ] 循環参照が発生していない
