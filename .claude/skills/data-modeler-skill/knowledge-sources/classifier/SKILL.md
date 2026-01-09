---
name: classifier
description: 抽出されたエンティティをリソースとイベントに分類します
version: 1.0.0
parent_skill: data-modeler
---

# Classifier Knowledge Source

抽出されたエンティティ候補を「リソース」と「イベント」に分類します。

## イミュータブルデータモデルにおける分類基準

### リソース（Resource）
- 時間経過で状態が変化しうるもの
- 継続的に存在するもの
- 例: 顧客、商品、社員、契約

### イベント（Event）
- 特定時点で発生した事実
- 一度発生したら変更されないもの
- **必ず1つの日時属性を持つ**
- 例: 注文、入金、出荷、請求書送付

## 分類のポイント

1. **日時属性の有無**
   - 「〜日時」「〜日」を持つ → イベント候補
   - 例: 注文日時、入金日、送付日時

2. **動詞との関連**
   - 動詞から派生 → イベント候補
   - 例: 送付する → 送付イベント

3. **更新の性質**
   - 作成後に更新される → リソース
   - 作成後は不変 → イベント

## 入力

- `/tmp/data-modeler-blackboard/entities_raw.json`

## 出力

- `/tmp/data-modeler-blackboard/entities_classified.json`

```json
{
  "resources": [
    {
      "japanese": "顧客",
      "english": "Customer",
      "attributes": ["顧客ID", "顧客名", "住所", "電話番号", "メールアドレス"],
      "note": "請求書を受け取る主体"
    }
  ],
  "events": [
    {
      "japanese": "請求書送付",
      "english": "InvoiceSend",
      "datetime_attribute": "送付日時",
      "attributes": ["送付日時", "送付方法", "送付先"],
      "related_resource": "Customer",
      "note": "顧客に請求書を送る行為"
    }
  ],
  "cross_entities": []
}
```

## 実装例

```python
def classify_entities(raw_entities: dict) -> dict:
    """
    エンティティをリソースとイベントに分類
    """
    
    prompt = f"""
以下のエンティティ候補を、イミュータブルデータモデルの原則に基づいて
リソースとイベントに分類してください。

【エンティティ候補】
{json.dumps(raw_entities, ensure_ascii=False, indent=2)}

【分類基準】
1. リソース: 継続的に存在し、状態が変化しうるもの
2. イベント: 特定時点で発生した事実、不変
3. イベントには必ず1つの日時属性を持たせる

【出力形式】
{{
  "resources": [...],
  "events": [...],
  "cross_entities": []
}}
"""
    
    # Claude APIで処理
    return classified_result
```

## 隠れたイベントの検出

リソースに「更新日時」などがある場合、背後にイベントが隠れている可能性があります。

### 例

**リソース: 社員情報**
- 属性: 社員ID, 氏名, 部署, 役職, 更新日時

↓ 分析

**隠れたイベント発見: 社員異動イベント**
- 属性: 異動日時, 社員ID, 異動前部署, 異動後部署

このような隠れたイベントを積極的に抽出します。
