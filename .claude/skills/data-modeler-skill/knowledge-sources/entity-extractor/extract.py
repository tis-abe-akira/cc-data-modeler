#!/usr/bin/env python3
"""
Entity Extractor - Knowledge Source
ユースケース記述からエンティティ候補を抽出
"""

import json
import yaml
import os
from pathlib import Path

def extract_entities_with_claude(usecase_text: str) -> dict:
    """
    Claude APIを使用してエンティティを抽出
    
    実際のClaude Code実行時は、このスクリプト自体がClaude Code環境で
    実行されるため、直接プロンプトを返して処理させることができます。
    """
    
    # Claude Codeに処理を依頼するためのマーカー
    # 実際の実装では、ここでClaude APIを呼び出すか、
    # このスクリプト自体をClaude Codeが解釈して実行します
    
    extraction_prompt = f"""
以下のユースケース記述を分析し、エンティティ候補を抽出してください。

【ユースケース】
{usecase_text}

【抽出ルール】
1. 名詞を抽出（人、物、組織、概念など）
2. 動詞を抽出（業務アクションを示すもの）
3. 英語名を自動生成
   - 名詞: PascalCase、単数形（例: Customer, Invoice）
   - 動詞: camelCase（例: send, confirm）
4. データとして管理すべき概念のみ抽出
5. 抽象的すぎる概念（システム、データ、情報など）は除外

【出力形式】
必ず以下のJSON形式で出力してください。他の説明は不要です。

{{
  "noun_candidates": [
    {{
      "japanese": "顧客",
      "english": "Customer",
      "note": "請求書を受け取る対象"
    }}
  ],
  "verb_candidates": [
    {{
      "japanese": "送付する",
      "english": "send",
      "note": "請求書や確認状を送る行為"
    }}
  ]
}}
"""
    
    print("=" * 60)
    print("エンティティ抽出中...")
    print("=" * 60)
    
    # ここでClaude APIを呼び出す想定
    # 実際のClaude Code環境では、このプロンプトが自動的に処理されます
    
    # サンプル実装: 実際にはClaude APIの応答を使用
    result = {
        "noun_candidates": [
            {"japanese": "顧客", "english": "Customer", "note": "請求書を受け取る主体"},
            {"japanese": "請求書", "english": "Invoice", "note": "顧客に送付される文書"},
            {"japanese": "入金", "english": "Payment", "note": "顧客からの支払い"},
            {"japanese": "確認状", "english": "Confirmation", "note": "未入金時に送付される文書"}
        ],
        "verb_candidates": [
            {"japanese": "送付する", "english": "send", "note": "請求書や確認状を送る"},
            {"japanese": "到来する", "english": "arrive", "note": "期日が来る"},
            {"japanese": "入金する", "english": "pay", "note": "支払いを行う"}
        ]
    }
    
    return result


def main():
    """メイン処理"""
    
    blackboard_path = Path("/tmp/data-modeler-blackboard")
    blackboard_path.mkdir(parents=True, exist_ok=True)
    
    # 状態ファイルを読み込み
    state_file = blackboard_path / "state.yaml"
    
    if not state_file.exists():
        print("❌ エラー: state.yamlが存在しません")
        print("   data-modelerスキルから実行してください")
        return 1
    
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    
    usecase = state.get("input_usecase", "")
    
    if not usecase:
        print("❌ エラー: ユースケースが指定されていません")
        return 1
    
    print(f"📝 ユースケース: {usecase[:100]}...")
    
    # エンティティ抽出
    result = extract_entities_with_claude(usecase)
    
    # 結果をブラックボードに保存
    output_file = blackboard_path / "entities_raw.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ エンティティ抽出完了:")
    print(f"   - 名詞候補: {len(result['noun_candidates'])}個")
    print(f"   - 動詞候補: {len(result['verb_candidates'])}個")
    print(f"   - 出力先: {output_file}")
    
    # 状態を更新
    if "entity_extraction" not in state.get("completed_phases", []):
        state.setdefault("completed_phases", []).append("entity_extraction")
    state["current_phase"] = "classification"
    state["next_action"] = "classifier"
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    
    print(f"\n📊 次のフェーズ: {state['current_phase']}")
    print(f"   実行するKnowledge Source: {state['next_action']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
