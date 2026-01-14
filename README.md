# cc-data-modeler

ユースケース記述からデータベース設計一式を自動生成するClaude Code用スキル集

## 機能

| スキル | 入力 | 出力 |
|--------|------|------|
| `/data-modeler` | 業務要件テキスト | エンティティ分類、ER図 |
| `/usecase-detailer` | 粗いユースケース | API設計向け詳細仕様 |
| `/ddl-generator` | データモデル | PostgreSQL DDL、サンプルデータ、クエリ例 |
| `/openapi-generator` | エンティティ分類 | OpenAPI 3.1.0仕様書 |
| `/postgres-test` | DDL・クエリ | Dockerでの実行検証レポート |

## 処理の流れ

```
業務要件テキスト
    ↓ /data-modeler
エンティティ抽出 → 分類 → 関連分析 → 検証 → ER図
    ↓ /ddl-generator
PostgreSQL DDL + サンプルデータ + クエリ例
    ↓ /openapi-generator
OpenAPI仕様書
    ↓ /postgres-test
実DB上での動作検証
```

## 設計思想

イミュータブルデータモデルに基づく。

- **リソース**: 継続的に存在するもの（顧客、商品など）
- **イベント**: 特定時点で発生した不変の事実（注文、入金など）

イベントは変更せず追記のみ。現在状態はイベントの集約から算出する。

## 成果物

```
artifacts/{プロジェクト名}/
  ├── state.yaml              # 進捗管理
  ├── entities_classified.json # エンティティ分類
  ├── model.json              # データモデル定義
  ├── er_diagram.mmd          # ER図
  ├── schema.sql              # PostgreSQL DDL
  ├── sample_data.sql         # サンプルデータ
  ├── query_examples.sql      # クエリ例
  └── openapi.yaml            # API仕様書
```
