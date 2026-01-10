# イミュータブルデータモデルの設計原則

## 基本概念

イミュータブルデータモデルは、データを「リソース」と「イベント」に分離して管理するパターン。

### リソーステーブル
- エンティティの基本情報を保存
- IDと最小限の属性のみ
- 状態を持たない（状態はイベントから算出）

### イベントテーブル
- 時系列で発生した事実を記録
- 絶対に削除・更新しない（追記のみ）
- 必ず日時属性を持つ

### ジャンクションテーブル
- 多対多関係を解消
- タグ方式で柔軟な分類を実現

## エンティティタイプ

### Resource（リソース）
- 基本情報のみ保存
- 状態は保持しない
- 例: Customer, Project, Person

### Event（イベント）
- 時系列で発生した事実
- `datetime_attribute`で日時フィールドを指定
- 例: ProjectStart, Payment, RiskEvaluate

### Junction（ジャンクション）
- 多対多関係の解消
- 複合主キー
- 例: ProjectDevelopmentType

## 設計パターン

### イベント経由の多対多
リソース間の関係をイベントで記録することで、履歴を保持しながら多対多を実現。

例: 担当者アサイン
- PersonAssign イベントで「いつ誰がどのプロジェクトにアサインされたか」を記録
- PersonReplace イベントで交代履歴も記録

### タグ方式
静的な多対多関係はジャンクションテーブルで実現。

例: プロジェクトと開発種別
- ProjectDevelopmentType ジャンクションで複数タグ付け可能

### 自己参照
階層構造を表現。

例: 組織階層
- Organization.ParentOrganizationID で親組織を参照

## 状態の算出

イミュータブルモデルでは「現在の状態」をイベントから集約で算出する。

### 基本パターン
```sql
-- 最新の状態を取得
WITH LatestEvent AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ResourceID ORDER BY EventDateTime DESC) AS rn
    FROM EventTable
)
SELECT * FROM LatestEvent WHERE rn = 1
```

### 交代を考慮したパターン
```sql
-- アサイン状態を取得（交代イベントを除外）
SELECT * FROM PersonAssign pa
WHERE NOT EXISTS (
    SELECT 1 FROM PersonReplace pr
    WHERE pr.ProjectID = pa.ProjectID
      AND pr.OldPersonID = pa.PersonID
      AND pr.ReplaceDateTime > pa.AssignDateTime
)
```

### 集約パターン
```sql
-- 入金状況を集約
SELECT
    InvoiceID,
    Amount AS TotalAmount,
    COALESCE(SUM(PaymentAmount), 0) AS PaidAmount,
    Amount - COALESCE(SUM(PaymentAmount), 0) AS UnpaidAmount
FROM Invoice
LEFT JOIN Payment USING (InvoiceID)
GROUP BY InvoiceID, Amount
```
