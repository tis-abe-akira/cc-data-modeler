#!/usr/bin/env python3
"""
Diagram Generator - Knowledge Source
Mermaid形式のER図を生成
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List


def convert_cardinality(cardinality: str) -> str:
    """カーディナリティをMermaid記法に変換"""
    mapping = {
        "1:1": "||--||",
        "1:N": "||--o{",
        "M:N": "}o--o{",
        "1:0..1": "||--o|"
    }
    return mapping.get(cardinality, "||--o{")


def infer_type(attribute_name: str) -> str:
    """属性名から型を推論"""
    attr_lower = attribute_name.lower()
    
    if "id" in attr_lower or "番号" in attribute_name:
        return "int"
    elif "日時" in attribute_name or "datetime" in attr_lower:
        return "datetime"
    elif "日" in attribute_name or "date" in attr_lower:
        return "date"
    elif "金額" in attribute_name or "amount" in attr_lower or "価格" in attribute_name:
        return "float"
    elif "フラグ" in attribute_name or "flag" in attr_lower:
        return "boolean"
    else:
        return "string"


def generate_mermaid_diagram(model: dict) -> str:
    """
    データモデルからMermaid ER図を生成
    """
    
    lines = ["erDiagram"]
    
    # 関連を追加
    print("\n📐 関連を生成中...")
    for rel in model['relationships']:
        from_entity = rel['from_entity'].replace(" ", "_").upper()
        to_entity = rel['to_entity'].replace(" ", "_").upper()
        rel_type = rel['relationship_type']
        cardinality = rel['cardinality']
        
        card_notation = convert_cardinality(cardinality)
        line = f"    {from_entity} {card_notation} {to_entity} : {rel_type}"
        lines.append(line)
        print(f"   {from_entity} → {to_entity}")
    
    # リソースエンティティ定義を追加
    print("\n📋 リソースエンティティを生成中...")
    for resource in model['entities']['resources']:
        entity_name = resource['english'].replace(" ", "_").upper()
        print(f"   {entity_name}")
        
        lines.append(f"    {entity_name} {{")
        
        # 主キー
        pk_name = f"{resource['english']}ID"
        lines.append(f"        int {pk_name} PK")
        
        # 属性
        for attr in resource.get('attributes', []):
            if attr.endswith("ID") or "ID" in attr:
                continue  # IDは別途処理
            attr_type = infer_type(attr)
            attr_name = attr.replace(" ", "")
            lines.append(f"        {attr_type} {attr_name}")
        
        lines.append("    }")
    
    # イベントエンティティ定義を追加
    print("\n📋 イベントエンティティを生成中...")
    for event in model['entities']['events']:
        entity_name = event['english'].replace(" ", "_").upper()
        print(f"   {entity_name} (日時属性: {event['datetime_attribute']})")
        
        lines.append(f"    {entity_name} {{")
        
        # 主キー（イベントはEventIDを使用）
        lines.append(f"        int EventID PK")
        
        # 関連リソースへの外部キー
        if 'related_resource' in event:
            fk_name = f"{event['related_resource']}ID"
            lines.append(f"        int {fk_name} FK")
        
        # 日時属性（必須）
        datetime_attr = event['datetime_attribute'].replace(" ", "")
        lines.append(f"        datetime {datetime_attr}")
        
        # その他の属性
        for attr in event.get('attributes', []):
            if attr == event['datetime_attribute']:
                continue  # 既に追加済み
            if attr.endswith("ID") or "ID" in attr:
                continue
            attr_type = infer_type(attr)
            attr_name = attr.replace(" ", "")
            lines.append(f"        {attr_type} {attr_name}")
        
        lines.append("    }")
    
    # 交差エンティティ定義を追加
    if model.get('cross_entities'):
        print("\n📋 交差エンティティを生成中...")
        for cross in model['cross_entities']:
            entity_name = cross['name'].replace(" ", "_").upper()
            print(f"   {entity_name}")
            
            lines.append(f"    {entity_name} {{")
            
            # 複合主キー（接続する両エンティティのID）
            for connected in cross['connects']:
                fk_name = f"{connected}ID"
                lines.append(f"        int {fk_name} PK,FK")
            
            # その他の属性
            for attr in cross.get('attributes', []):
                if attr.endswith("ID"):
                    continue
                attr_type = infer_type(attr)
                attr_name = attr.replace(" ", "")
                lines.append(f"        {attr_type} {attr_name}")
            
            lines.append("    }")
    
    return "\n".join(lines)


def main():
    """メイン処理"""
    
    blackboard_path = Path("/tmp/data-modeler-blackboard")
    
    # 前段階の出力を読み込み
    input_file = blackboard_path / "model.json"
    
    if not input_file.exists():
        print("❌ エラー: model.jsonが存在しません")
        print("   relationship-analyzerを先に実行してください")
        return 1
    
    with open(input_file, "r", encoding="utf-8") as f:
        model = json.load(f)
    
    print("📥 入力:")
    print(f"   - リソース: {len(model['entities']['resources'])}個")
    print(f"   - イベント: {len(model['entities']['events'])}個")
    print(f"   - 関連: {len(model['relationships'])}個")
    
    # ER図生成
    print("\n" + "=" * 60)
    print("Mermaid ER図を生成中...")
    print("=" * 60)
    
    diagram = generate_mermaid_diagram(model)
    
    # 結果をブラックボードに保存
    output_file = blackboard_path / "diagram.mmd"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(diagram)
    
    print(f"\n✅ ER図生成完了:")
    print(f"   - 出力先: {output_file}")
    
    # ER図を表示
    print("\n" + "=" * 60)
    print("生成されたER図:")
    print("=" * 60)
    print(diagram)
    print("=" * 60)
    
    # 状態を更新
    state_file = blackboard_path / "state.yaml"
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    
    if "diagram_generation" not in state.get("completed_phases", []):
        state.setdefault("completed_phases", []).append("diagram_generation")
    state["current_phase"] = "completed"
    state["next_action"] = "none"
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    
    print(f"\n🎉 すべてのフェーズが完了しました！")
    print(f"\n📊 完了したフェーズ: {', '.join(state['completed_phases'])}")
    
    return 0


if __name__ == "__main__":
    exit(main())
