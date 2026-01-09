#!/usr/bin/env python3
"""
Classifier - Knowledge Source
エンティティをリソースとイベントに分類
"""

import json
import yaml
from pathlib import Path


def classify_entities(raw_entities: dict) -> dict:
    """
    エンティティをリソースとイベントに分類
    
    実際の実装では、Claude APIを呼び出して分類します。
    """
    
    classification_prompt = f"""
以下のエンティティ候補を、イミュータブルデータモデルの原則に基づいて
リソースとイベントに分類してください。

【エンティティ候補】
{json.dumps(raw_entities, ensure_ascii=False, indent=2)}

【分類基準】

1. **リソース（Resource）**
   - 継続的に存在するもの
   - 時間経過で状態が変化しうるもの
   - 例: 顧客、商品、社員、契約

2. **イベント（Event）**
   - 特定時点で発生した事実
   - 一度発生したら変更されない
   - **必ず1つの日時属性を持つ**（重要）
   - 例: 注文、入金、出荷、送付

3. **隠れたイベントの検出**
   - リソースに「更新日時」がある場合、背後にイベントが隠れている可能性
   - 例: 社員情報の更新日時 → 社員異動イベント

【出力形式】
必ず以下のJSON形式で出力してください。

{{
  "resources": [
    {{
      "japanese": "顧客",
      "english": "Customer",
      "attributes": ["顧客ID", "顧客名", "住所"],
      "note": "分類理由"
    }}
  ],
  "events": [
    {{
      "japanese": "請求書送付",
      "english": "InvoiceSend",
      "datetime_attribute": "送付日時",
      "attributes": ["送付日時", "送付方法"],
      "related_resource": "Customer",
      "note": "分類理由"
    }}
  ],
  "hidden_events": [
    {{
      "japanese": "発見された隠れたイベント名",
      "english": "HiddenEvent",
      "datetime_attribute": "イベント日時",
      "trigger_resource": "元のリソース名",
      "note": "検出理由"
    }}
  ]
}}
"""
    
    print("=" * 60)
    print("エンティティ分類中...")
    print("=" * 60)
    
    # サンプル実装
    result = {
        "resources": [
            {
                "japanese": "顧客",
                "english": "Customer",
                "attributes": ["顧客ID", "顧客名", "住所", "電話番号", "メールアドレス"],
                "note": "請求書を受け取る主体、継続的に存在する"
            }
        ],
        "events": [
            {
                "japanese": "請求書送付",
                "english": "InvoiceSend",
                "datetime_attribute": "送付日時",
                "attributes": ["送付日時", "送付方法", "請求書番号"],
                "related_resource": "Customer",
                "note": "特定時点で発生した送付行為"
            },
            {
                "japanese": "確認状送付",
                "english": "ConfirmationSend",
                "datetime_attribute": "送付日時",
                "attributes": ["送付日時", "送付方法"],
                "related_resource": "Customer",
                "note": "未入金時に発生する送付行為"
            },
            {
                "japanese": "入金",
                "english": "Payment",
                "datetime_attribute": "入金日時",
                "attributes": ["入金日時", "入金額", "入金方法"],
                "related_resource": "Customer",
                "note": "特定時点で発生した支払い行為"
            }
        ],
        "hidden_events": []
    }
    
    return result


def main():
    """メイン処理"""
    
    blackboard_path = Path("/tmp/data-modeler-blackboard")
    
    # 前段階の出力を読み込み
    input_file = blackboard_path / "entities_raw.json"
    
    if not input_file.exists():
        print("❌ エラー: entities_raw.jsonが存在しません")
        print("   entity-extractorを先に実行してください")
        return 1
    
    with open(input_file, "r", encoding="utf-8") as f:
        raw_entities = json.load(f)
    
    print(f"📥 入力: {len(raw_entities.get('noun_candidates', []))}個の名詞候補")
    
    # 分類実行
    result = classify_entities(raw_entities)
    
    # 結果をブラックボードに保存
    output_file = blackboard_path / "entities_classified.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分類完了:")
    print(f"   - リソース: {len(result['resources'])}個")
    print(f"   - イベント: {len(result['events'])}個")
    print(f"   - 隠れたイベント: {len(result.get('hidden_events', []))}個")
    print(f"   - 出力先: {output_file}")
    
    # 詳細表示
    print("\n📋 リソース:")
    for r in result['resources']:
        print(f"   - {r['japanese']} ({r['english']})")
    
    print("\n📋 イベント:")
    for e in result['events']:
        print(f"   - {e['japanese']} ({e['english']}) - 日時属性: {e['datetime_attribute']}")
    
    # 状態を更新
    state_file = blackboard_path / "state.yaml"
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    
    if "classification" not in state.get("completed_phases", []):
        state.setdefault("completed_phases", []).append("classification")
    state["current_phase"] = "relationship_analysis"
    state["next_action"] = "relationship-analyzer"
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    
    print(f"\n📊 次のフェーズ: {state['current_phase']}")
    print(f"   実行するKnowledge Source: {state['next_action']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
