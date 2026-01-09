---
name: entity-extractor
description: ユースケース記述から名詞・動詞を抽出してエンティティ候補を洗い出します
version: 1.0.0
parent_skill: data-modeler
---

# Entity Extractor Knowledge Source

ユースケース記述を分析し、データモデルのエンティティ候補を抽出します。

## 処理内容

1. ユースケース記述から名詞を抽出（エンティティ候補）
2. 動詞を抽出（イベントのヒント）
3. 重複を除去して正規化
4. 英語名を自動生成

## 入力

- `/tmp/data-modeler-blackboard/state.yaml`の`input_usecase`フィールド

## 出力

- `/tmp/data-modeler-blackboard/entities_raw.json`

```json
{
  "noun_candidates": [
    {"japanese": "顧客", "english": "Customer"},
    {"japanese": "請求書", "english": "Invoice"}
  ],
  "verb_candidates": [
    {"japanese": "送付する", "english": "send"},
    {"japanese": "確認する", "english": "confirm"}
  ]
}
```

## 実装スクリプト

以下のPythonスクリプトを使用してエンティティを抽出します。

```python
import json
import yaml
import re
from pathlib import Path

def extract_entities(usecase_text: str) -> dict:
    """
    ユースケース記述からエンティティ候補を抽出
    
    実際の実装では、Claude APIを呼び出して以下のプロンプトで処理します：
    
    - 名詞を抽出（人、物、組織、概念など）
    - 動詞を抽出（業務アクションを示すもの）
    - 英語名を自動生成（PascalCase、単数形）
    """
    
    # Claude APIを使用した抽出ロジック
    prompt = f"""
以下のユースケース記述から、データモデリングに必要なエンティティ候補を抽出してください。

ユースケース:
{usecase_text}

以下の形式でJSON出力してください：
{{
  "noun_candidates": [
    {{"japanese": "名詞", "english": "EnglishName", "note": "説明"}}
  ],
  "verb_candidates": [
    {{"japanese": "動詞", "english": "verb", "note": "説明"}}
  ]
}}

注意事項：
- 英語名はPascalCase（名詞）またはcamelCase（動詞）で
- データとして管理すべき概念を抽出
- 抽象的すぎる概念は除外
"""
    
    # ここではサンプル出力を返す（実際にはClaude APIを呼び出す）
    return {
        "noun_candidates": [],
        "verb_candidates": []
    }

def main():
    blackboard_path = Path("/tmp/data-modeler-blackboard")
    
    # 状態ファイルを読み込み
    with open(blackboard_path / "state.yaml", "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
    
    usecase = state.get("input_usecase", "")
    
    if not usecase:
        print("エラー: ユースケースが指定されていません")
        return
    
    # エンティティ抽出
    result = extract_entities(usecase)
    
    # 結果をブラックボードに保存
    with open(blackboard_path / "entities_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 状態を更新
    state["completed_phases"].append("entity_extraction")
    state["current_phase"] = "classification"
    state["next_action"] = "classifier"
    
    with open(blackboard_path / "state.yaml", "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    
    print(f"✓ エンティティ抽出完了: {len(result['noun_candidates'])}個の名詞、{len(result['verb_candidates'])}個の動詞")

if __name__ == "__main__":
    main()
```

## 使用方法

```bash
# このKnowledge Sourceを直接実行
python knowledge-sources/entity-extractor/extract.py
```

## 抽出のヒント

### 良いエンティティ候補

- 顧客、商品、注文、社員
- 請求書、入金、出荷
- 契約、プロジェクト、タスク

### 除外すべき候補

- システム、データ、情報（抽象的すぎる）
- する、なる、ある（動詞や助動詞）
- これ、それ（指示代名詞）
