# イミュータブルモデルのクエリパターン

## 基本原則

イミュータブルモデルでは「現在の状態」をイベントから集約で算出する。
クエリは複雑になるが、生成AIでサポート可能な強力なパターン。

## パターン1: 最新状態の取得

### ウィンドウ関数でランク付け
```sql
WITH LatestEvent AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY ResourceID ORDER BY EventDateTime DESC) AS rn
    FROM EventTable
)
SELECT * FROM LatestEvent WHERE rn = 1
```

### 例: 最新のリスク評価
```sql
WITH LatestRiskEvaluate AS (
    SELECT
        ProjectID,
        RiskRank,
        EvaluateDateTime,
        ROW_NUMBER() OVER (PARTITION BY ProjectID ORDER BY EvaluateDateTime DESC) AS rn
    FROM RISK_EVALUATE
)
SELECT
    p.ProjectName,
    lre.RiskRank AS "最新リスクランク"
FROM PROJECT p
LEFT JOIN LatestRiskEvaluate lre ON p.ProjectID = lre.ProjectID AND lre.rn = 1
```

## パターン2: イベント集約

### 集約関数で状態を算出
```sql
SELECT
    ResourceID,
    COUNT(*) AS EventCount,
    SUM(Amount) AS TotalAmount,
    MAX(EventDateTime) AS LatestEventDateTime
FROM EventTable
GROUP BY ResourceID
```

### 例: 入金状況の集約
```sql
SELECT
    i.InvoiceID,
    i.Amount AS "請求金額",
    COALESCE(SUM(p.PaymentAmount), 0) AS "入金済み額",
    i.Amount - COALESCE(SUM(p.PaymentAmount), 0) AS "未入金額"
FROM INVOICE i
LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
GROUP BY i.InvoiceID, i.Amount
```

## パターン3: イベント履歴の追跡

### 時系列でのイベント取得
```sql
SELECT
    EventDateTime,
    EventType,
    Details
FROM EventTable
WHERE ResourceID = ?
ORDER BY EventDateTime
```

### 例: リスク推移の追跡
```sql
SELECT
    p.ProjectName,
    re.RiskRank,
    re.EvaluateDateTime,
    per.Name AS "評価者"
FROM RISK_EVALUATE re
JOIN PROJECT p ON re.ProjectID = p.ProjectID
JOIN PERSON per ON re.EvaluatedBy = per.PersonID
ORDER BY re.EvaluateDateTime
```

## パターン4: 交代イベントの考慮

### NOT EXISTSで交代済みを除外
```sql
SELECT * FROM AssignEvent ae
WHERE NOT EXISTS (
    SELECT 1 FROM ReplaceEvent re
    WHERE re.ResourceID = ae.ResourceID
      AND re.OldPersonID = ae.PersonID
      AND re.ReplaceDateTime > ae.AssignDateTime
)
```

### 例: 現在の担当者一覧
```sql
WITH CurrentAssignments AS (
    SELECT
        pa.ProjectID,
        pa.PersonID,
        pa.RoleID,
        pa.AssignDateTime
    FROM PERSON_ASSIGN pa
    WHERE NOT EXISTS (
        SELECT 1 FROM PERSON_REPLACE pr
        WHERE pr.ProjectID = pa.ProjectID
          AND pr.OldPersonID = pa.PersonID
          AND pr.RoleID = pa.RoleID
          AND pr.ReplaceDateTime > pa.AssignDateTime
    )
)
SELECT
    p.ProjectName,
    per.Name AS "担当者名",
    r.RoleName AS "役割"
FROM CurrentAssignments ca
JOIN PROJECT p ON ca.ProjectID = p.ProjectID
JOIN PERSON per ON ca.PersonID = per.PersonID
JOIN ROLE r ON ca.RoleID = r.RoleID
```

## パターン5: タグ方式の多対多

### STRING_AGGで集約
```sql
SELECT
    ResourceID,
    STRING_AGG(TagName, ', ') AS Tags
FROM Resource
LEFT JOIN Junction ON Resource.ID = Junction.ResourceID
LEFT JOIN Tag ON Junction.TagID = Tag.ID
GROUP BY ResourceID
```

### 例: プロジェクトのタグ情報
```sql
SELECT
    p.ProjectName,
    STRING_AGG(DISTINCT dt.DevelopmentTypeName, ', ') AS "開発種別",
    STRING_AGG(DISTINCT dm.DevelopmentMethodName, ', ') AS "開発方式"
FROM PROJECT p
LEFT JOIN PROJECT_DEVELOPMENT_TYPE pdt ON p.ProjectID = pdt.ProjectID
LEFT JOIN DEVELOPMENT_TYPE dt ON pdt.DevelopmentTypeID = dt.DevelopmentTypeID
LEFT JOIN PROJECT_DEVELOPMENT_METHOD pdm ON p.ProjectID = pdm.ProjectID
LEFT JOIN DEVELOPMENT_METHOD dm ON pdm.DevelopmentMethodID = dm.DevelopmentMethodID
GROUP BY p.ProjectID, p.ProjectName
```

## パターン6: 条件付き集約

### CASE文で分類
```sql
SELECT
    ResourceID,
    SUM(CASE WHEN Status = '完了' THEN 1 ELSE 0 END) AS CompletedCount,
    SUM(CASE WHEN Status = '進行中' THEN 1 ELSE 0 END) AS InProgressCount
FROM EventTable
GROUP BY ResourceID
```

### 例: 業界別プロジェクトサマリー
```sql
SELECT
    i.IndustryName,
    COUNT(DISTINCT p.ProjectID) AS "プロジェクト数",
    SUM(CASE WHEN pc.CompleteDateTime IS NOT NULL THEN 1 ELSE 0 END) AS "完了",
    SUM(CASE WHEN ps.StartDateTime IS NOT NULL AND pc.CompleteDateTime IS NULL THEN 1 ELSE 0 END) AS "進行中"
FROM INDUSTRY i
JOIN CUSTOMER c ON i.IndustryID = c.IndustryID
JOIN PROJECT p ON c.CustomerID = p.CustomerID
LEFT JOIN PROJECT_START ps ON p.ProjectID = ps.ProjectID
LEFT JOIN PROJECT_COMPLETE pc ON p.ProjectID = pc.ProjectID
GROUP BY i.IndustryID, i.IndustryName
```

## パターン7: 再帰CTE

### 階層構造の取得
```sql
WITH RECURSIVE Hierarchy AS (
    -- ベースケース
    SELECT ID, Name, ParentID, 1 AS Level
    FROM Table
    WHERE ParentID IS NULL

    UNION ALL

    -- 再帰ケース
    SELECT t.ID, t.Name, t.ParentID, h.Level + 1
    FROM Table t
    JOIN Hierarchy h ON t.ParentID = h.ID
)
SELECT * FROM Hierarchy
```

### 例: 組織階層の取得
```sql
WITH RECURSIVE OrgHierarchy AS (
    -- ベースケース: 参画している組織
    SELECT
        oj.ProjectID,
        o.OrganizationID,
        o.OrganizationName,
        o.ParentOrganizationID,
        1 AS Level,
        o.OrganizationName AS Path
    FROM ORGANIZATION_JOIN oj
    JOIN ORGANIZATION o ON oj.OrganizationID = o.OrganizationID

    UNION ALL

    -- 再帰ケース: 親組織を遡る
    SELECT
        oh.ProjectID,
        parent.OrganizationID,
        parent.OrganizationName,
        parent.ParentOrganizationID,
        oh.Level + 1,
        parent.OrganizationName || ' > ' || oh.Path
    FROM OrgHierarchy oh
    JOIN ORGANIZATION parent ON oh.ParentOrganizationID = parent.OrganizationID
)
SELECT
    p.ProjectName,
    oh.OrganizationName,
    oh.Level,
    oh.Path AS "組織階層パス"
FROM OrgHierarchy oh
JOIN PROJECT p ON oh.ProjectID = p.ProjectID
ORDER BY oh.Level DESC
```

## パターン8: タイムライン統合

### UNION ALLで全イベント統合
```sql
SELECT EventDateTime, 'Type1' AS EventType, Details FROM Event1
UNION ALL
SELECT EventDateTime, 'Type2' AS EventType, Details FROM Event2
UNION ALL
SELECT EventDateTime, 'Type3' AS EventType, Details FROM Event3
ORDER BY EventDateTime
```

### 例: プロジェクトの全イベントタイムライン
```sql
SELECT
    p.ProjectName,
    'プロジェクト開始' AS "イベント種別",
    ps.StartDateTime AS "発生日時",
    per.Name AS "関連人物"
FROM PROJECT_START ps
JOIN PROJECT p ON ps.ProjectID = p.ProjectID
JOIN PERSON per ON ps.RegisteredBy = per.PersonID

UNION ALL

SELECT
    p.ProjectName,
    '担当者アサイン',
    pa.AssignDateTime,
    per.Name
FROM PERSON_ASSIGN pa
JOIN PROJECT p ON pa.ProjectID = p.ProjectID
JOIN PERSON per ON pa.PersonID = per.PersonID

UNION ALL

SELECT
    p.ProjectName,
    'リスク評価',
    re.EvaluateDateTime,
    per.Name
FROM RISK_EVALUATE re
JOIN PROJECT p ON re.ProjectID = p.ProjectID
JOIN PERSON per ON re.EvaluatedBy = per.PersonID

ORDER BY "発生日時"
```

## クエリ設計の Tips

1. **WITH句を活用** - 複雑なクエリをステップに分解
2. **ウィンドウ関数** - 最新状態の取得に必須
3. **LEFT JOIN** - イベント未発生も考慮
4. **NOT EXISTS** - 交代・削除済みの除外
5. **STRING_AGG** - タグ方式の集約
6. **コメント** - クエリの意図を明記

## 実用的なユースケース

### ダッシュボード用
- プロジェクト一覧と現在の状態
- 業界別サマリー
- 担当者の稼働状況

### 分析用
- リスク推移
- 支援実施履歴
- 担当者交代履歴

### 詳細表示用
- プロジェクトのタイムライン
- 組織階層
- タグ情報
