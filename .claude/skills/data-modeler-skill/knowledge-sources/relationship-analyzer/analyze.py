#!/usr/bin/env python3
"""
Relationship Analyzer - Knowledge Source
エンティティ間の関連を分析
"""

import json
import yaml
from pathlib import Path


def analyze_relationships(classified_entities: dict) -> dict:
    """
    エンティティ間の関連を分析し、カーディナリティと交差エンティティを決定
    """
    
    analysis_prompt = f"""
以下の分類済みエンティティに対して、関連を分析してください。

【エンティティ】
{json.dumps(classified_entities, ensure_ascii=False, indent=2)}

【分析項目】

1. **リソース間の関連**
   - カーディナリティを決定（1:1, 1:N, M:N）
   - 関連の種類を明確化（has, belongs_to, refers_to等）

2. **イベントと関連リソースの紐付け**
   - すべてのイベントは関連するリソースを参照する
   - 外部キーを明示

3. **交差エンティティの導入**
   - 多対多の関係を解消
   - 関連自体が重要な属性を持つ場合に導入

4. **外部キー制約の定義**
   - 参照整合性を保証する制約

【出力形式】
必ず以下のJSON形式で出力してください。

{{
  "entities": {{
    "resources": [...元のリソース情報...],
    "events": [...元のイベント情報...]
  }},
  "relationships": [
    {{
      "id": "rel_001",
      "from_entity": "Customer",
      "to_entity": "Invoice",
      "cardinality": "1:N",
      "relationship_type": "has",
      "foreign_key": {{
        "table": "Invoice",
        "column": "CustomerID",
        "references": "Customer.CustomerID"
      }},
      "note": "1人の顧客は複数の請求書を持つ"
    }}
  ],
  "cross_entities": [
    {{
      "name": "OrderDetail",
      "japanese": "注文明細",
      "english": "OrderDetail",
      "connects": ["Order", "Product"],
      "attributes": ["OrderID", "ProductID", "Quantity", "UnitPrice"],
      "reason": "注文と商品の多対多関係を解消"
    }}
  ]
}}
"""
    
    print("=" * 60)
    print("関連分析中...")
    print("=" * 60)
    
    # サンプル実装
    result = {
        "entities": classified_entities,
        "relationships": [
            {
                "id": "rel_001",
                "from_entity": "Customer",
                "to_entity": "InvoiceSend",
                "cardinality": "1:N",
                "relationship_type": "triggers",
                "foreign_key": {
                    "table": "InvoiceSend",
                    "column": "CustomerID",
                    "references": "Customer.CustomerID"
                },
                "note": "顧客は複数の請求書送付イベントを持つ"
            },
            {
                "id": "rel_002",
                "from_entity": "Customer",
                "to_entity": "Payment",
                "cardinality": "1:N",
                "relationship_type": "makes",
                "foreign_key": {
                    "table": "Payment",
                    "column": "CustomerID",
                    "references": "Customer.CustomerID"
                },
                "note": "顧客は複数の入金を行う"
            },
            {
                "id": "rel_003",
                "from_entity": "Customer",
                "to_entity": "ConfirmationSend",
                "cardinality": "1:N",
                "relationship_type": "receives",
                "foreign_key": {
                    "table": "ConfirmationSend",
                    "column": "CustomerID",
                    "references": "Customer.CustomerID"
                },
                "note": "顧客は複数の確認状送付を受ける"
            }
        ],
        "cross_entities": []
    }
    
    return result


def main():
    """メイン処理"""
    
    blackboard_path = Path("/tmp/data-modeler-blackboard")
    
    # 前段階の出力を読み込み
    input_file = blackboard_path / "entities_classified.json"
    
    if not input_file.exists():
        print("❌ エラー: entities_classified.jsonが存在しません")
        print("   classifierを先に実行してください")
        return 1
    
    with open(input_file, "r", encoding="utf-8") as f:
        classified_entities = json.load(f)
    
    print(f"📥 入力:")
    print(f"   - リソース: {len(classified_entities.get('resources', []))}個")
    print(f"   - イベント: {len(classified_entities.get('events', []))}個")
    
    # 関連分析実行
    result = analyze_relationships(classified_entities)
    
    # 結果をブラックボードに保存
    output_file = blackboard_path / "model.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 関連分析完了:")
    print(f"   - 関連: {len(result['relationships'])}個")
    print(f"   - 交差エンティティ: {len(result.get('cross_entities', []))}個")
    print(f"   - 出力先: {output_file}")
    
    # 詳細表示
    print("\n📋 関連:")
    for rel in result['relationships']:
        print(f"   - {rel['from_entity']} {rel['relationship_type']} {rel['to_entity']} ({rel['cardinality']})")
    
    if result.get('cross_entities'):
        print("\n📋 交差エンティティ:")
        for ce in result['cross_entities']:
            connects = " ↔ ".join(ce['connects'])
            print(f"   - {ce['japanese']} ({ce['name']}): {connects}")
    
    # 状態を更新
    state_file = blackboard_path / "state.yaml"
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    
    if "relationship_analysis" not in state.get("completed_phases", []):
        state.setdefault("completed_phases", []).append("relationship_analysis")
    state["current_phase"] = "diagram_generation"
    state["next_action"] = "diagram-generator"
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    
    print(f"\n📊 次のフェーズ: {state['current_phase']}")
    print(f"   実行するKnowledge Source: {state['next_action']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
