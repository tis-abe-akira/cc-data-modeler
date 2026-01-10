-- ================================================
-- イミュータブルデータモデル クエリ例集
-- プロジェクト記録システム
-- 複雑だけど強力！生成AIでサポート可能なクエリ集
-- ================================================

-- ================================================
-- 【クエリ1】プロジェクト一覧と現在の状態
-- イミュータブルモデルの特徴: イベントから現在の状態を集約
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    c.CustomerName AS "顧客名",
    i.IndustryName AS "業界",
    p.PlannedStartDate AS "計画開始日",
    p.PlannedEndDate AS "計画終了日",
    ps.StartDateTime AS "実際の開始日時",
    pc.CompleteDateTime AS "完了日時",
    CASE
        WHEN pc.CompleteDateTime IS NOT NULL THEN '完了'
        WHEN ps.StartDateTime IS NOT NULL THEN '進行中'
        ELSE '未開始'
    END AS "状態",
    pc.ActualEffort AS "実績工数"
FROM
    PROJECT p
    INNER JOIN CUSTOMER c ON p.CustomerID = c.CustomerID
    LEFT JOIN INDUSTRY i ON c.IndustryID = i.IndustryID
    LEFT JOIN PROJECT_START ps ON p.ProjectID = ps.ProjectID
    LEFT JOIN PROJECT_COMPLETE pc ON p.ProjectID = pc.ProjectID
ORDER BY
    p.ProjectID;

-- ================================================
-- 【クエリ2】プロジェクトの現在の担当者一覧
-- イベントから最新のアサイン状態を取得（交代を考慮）
-- ================================================
WITH LatestAssignment AS (
    SELECT
        pa.ProjectID,
        pa.PersonID,
        pa.RoleID,
        pa.AssignDateTime,
        ROW_NUMBER() OVER (PARTITION BY pa.ProjectID, pa.RoleID ORDER BY pa.AssignDateTime DESC) AS rn
    FROM
        PERSON_ASSIGN pa
    WHERE
        NOT EXISTS (
            -- 交代イベントがない担当者のみ（交代されていない）
            SELECT 1
            FROM PERSON_REPLACE pr
            WHERE pr.ProjectID = pa.ProjectID
              AND pr.OldPersonID = pa.PersonID
              AND pr.RoleID = pa.RoleID
              AND pr.ReplaceDateTime > pa.AssignDateTime
        )
)
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    per.Name AS "担当者名",
    r.RoleName AS "役割",
    la.AssignDateTime AS "アサイン日時"
FROM
    LatestAssignment la
    INNER JOIN PROJECT p ON la.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON la.PersonID = per.PersonID
    INNER JOIN ROLE r ON la.RoleID = r.RoleID
WHERE
    la.rn = 1
ORDER BY
    p.ProjectID, r.RoleID;

-- ================================================
-- 【クエリ3】プロジェクトのリスク推移
-- イミュータブルモデルの特徴: 時系列でリスク評価の変化を追跡
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    re.RiskRank AS "リスクランク",
    re.EvaluateDateTime AS "評価日時",
    per.Name AS "評価者",
    CASE WHEN re.IsSystemProposed THEN 'システム提案' ELSE '手動' END AS "提案元",
    CASE WHEN re.IsManualAdjusted THEN '調整あり' ELSE '調整なし' END AS "手動調整"
FROM
    RISK_EVALUATE re
    INNER JOIN PROJECT p ON re.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON re.EvaluatedBy = per.PersonID
ORDER BY
    p.ProjectID, re.EvaluateDateTime;

-- ================================================
-- 【クエリ4】プロジェクトの最新リスク評価
-- 各プロジェクトの最新のリスクランクのみ取得
-- ================================================
WITH LatestRiskEvaluate AS (
    SELECT
        ProjectID,
        RiskRank,
        EvaluateDateTime,
        EvaluatedBy,
        IsSystemProposed,
        IsManualAdjusted,
        ROW_NUMBER() OVER (PARTITION BY ProjectID ORDER BY EvaluateDateTime DESC) AS rn
    FROM
        RISK_EVALUATE
)
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    c.CustomerName AS "顧客名",
    lre.RiskRank AS "最新リスクランク",
    lre.EvaluateDateTime AS "評価日時",
    per.Name AS "評価者",
    CASE
        WHEN pc.CompleteDateTime IS NOT NULL THEN '完了'
        WHEN ps.StartDateTime IS NOT NULL THEN '進行中'
        ELSE '未開始'
    END AS "状態"
FROM
    PROJECT p
    INNER JOIN CUSTOMER c ON p.CustomerID = c.CustomerID
    LEFT JOIN LatestRiskEvaluate lre ON p.ProjectID = lre.ProjectID AND lre.rn = 1
    LEFT JOIN PERSON per ON lre.EvaluatedBy = per.PersonID
    LEFT JOIN PROJECT_START ps ON p.ProjectID = ps.ProjectID
    LEFT JOIN PROJECT_COMPLETE pc ON p.ProjectID = pc.ProjectID
ORDER BY
    CASE lre.RiskRank
        WHEN '高' THEN 1
        WHEN '中' THEN 2
        WHEN '低' THEN 3
        ELSE 4
    END,
    p.ProjectID;

-- ================================================
-- 【クエリ5】支援実施履歴とその効果
-- イミュータブルモデルの特徴: 支援イベントの記録
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    st.SupportTypeName AS "支援タイプ",
    per.Name AS "支援担当者",
    se.ExecuteDateTime AS "実施日時",
    se.SupportContent AS "支援内容",
    se.Outcome AS "成果",
    se.Memo AS "メモ"
FROM
    SUPPORT_EXECUTE se
    INNER JOIN PROJECT p ON se.ProjectID = p.ProjectID
    INNER JOIN SUPPORT_TYPE st ON se.SupportTypeID = st.SupportTypeID
    INNER JOIN PERSON per ON se.SupportPersonID = per.PersonID
ORDER BY
    se.ExecuteDateTime DESC;

-- ================================================
-- 【クエリ6】プロジェクトのタグ情報（開発種別・方式・工程）
-- タグ方式の多対多関係から情報を集約
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    STRING_AGG(DISTINCT dt.DevelopmentTypeName, ', ') AS "開発種別",
    STRING_AGG(DISTINCT dm.DevelopmentMethodName, ', ') AS "開発方式",
    STRING_AGG(DISTINCT tp.TargetPhaseName, ', ') AS "対象工程"
FROM
    PROJECT p
    LEFT JOIN PROJECT_DEVELOPMENT_TYPE pdt ON p.ProjectID = pdt.ProjectID
    LEFT JOIN DEVELOPMENT_TYPE dt ON pdt.DevelopmentTypeID = dt.DevelopmentTypeID
    LEFT JOIN PROJECT_DEVELOPMENT_METHOD pdm ON p.ProjectID = pdm.ProjectID
    LEFT JOIN DEVELOPMENT_METHOD dm ON pdm.DevelopmentMethodID = dm.DevelopmentMethodID
    LEFT JOIN PROJECT_TARGET_PHASE ptp ON p.ProjectID = ptp.ProjectID
    LEFT JOIN TARGET_PHASE tp ON ptp.TargetPhaseID = tp.TargetPhaseID
GROUP BY
    p.ProjectID, p.ProjectName
ORDER BY
    p.ProjectID;

-- ================================================
-- 【クエリ7】参画組織とその階層
-- 自己参照テーブルから組織階層を取得
-- ================================================
WITH RECURSIVE OrgHierarchy AS (
    -- ベースケース: 参画している組織
    SELECT
        oj.ProjectID,
        o.OrganizationID,
        o.OrganizationName,
        o.OrganizationType,
        o.ParentOrganizationID,
        1 AS Level,
        o.OrganizationName AS Path
    FROM
        ORGANIZATION_JOIN oj
        INNER JOIN ORGANIZATION o ON oj.OrganizationID = o.OrganizationID

    UNION ALL

    -- 再帰ケース: 親組織を遡る
    SELECT
        oh.ProjectID,
        parent.OrganizationID,
        parent.OrganizationName,
        parent.OrganizationType,
        parent.ParentOrganizationID,
        oh.Level + 1,
        parent.OrganizationName || ' > ' || oh.Path
    FROM
        OrgHierarchy oh
        INNER JOIN ORGANIZATION parent ON oh.ParentOrganizationID = parent.OrganizationID
)
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    oh.OrganizationName AS "組織名",
    oh.OrganizationType AS "組織種別",
    oh.Level AS "階層レベル",
    oh.Path AS "組織階層パス"
FROM
    OrgHierarchy oh
    INNER JOIN PROJECT p ON oh.ProjectID = p.ProjectID
ORDER BY
    p.ProjectID, oh.Level DESC;

-- ================================================
-- 【クエリ8】担当者交代の履歴
-- イミュータブルモデルの特徴: 交代イベントで履歴を追跡
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    r.RoleName AS "役割",
    old_per.Name AS "旧担当者",
    new_per.Name AS "新担当者",
    pr.ReplaceDateTime AS "交代日時",
    reg_per.Name AS "登録者"
FROM
    PERSON_REPLACE pr
    INNER JOIN PROJECT p ON pr.ProjectID = p.ProjectID
    INNER JOIN ROLE r ON pr.RoleID = r.RoleID
    INNER JOIN PERSON old_per ON pr.OldPersonID = old_per.PersonID
    INNER JOIN PERSON new_per ON pr.NewPersonID = new_per.PersonID
    INNER JOIN PERSON reg_per ON pr.RegisteredBy = reg_per.PersonID
ORDER BY
    pr.ReplaceDateTime DESC;

-- ================================================
-- 【クエリ9】業界別プロジェクトサマリー
-- 業界ごとのプロジェクト数・状態・リスク分布
-- ================================================
WITH ProjectStatus AS (
    SELECT
        p.ProjectID,
        p.CustomerID,
        CASE
            WHEN pc.CompleteDateTime IS NOT NULL THEN '完了'
            WHEN ps.StartDateTime IS NOT NULL THEN '進行中'
            ELSE '未開始'
        END AS Status
    FROM
        PROJECT p
        LEFT JOIN PROJECT_START ps ON p.ProjectID = ps.ProjectID
        LEFT JOIN PROJECT_COMPLETE pc ON p.ProjectID = pc.ProjectID
),
LatestRisk AS (
    SELECT
        ProjectID,
        RiskRank,
        ROW_NUMBER() OVER (PARTITION BY ProjectID ORDER BY EvaluateDateTime DESC) AS rn
    FROM
        RISK_EVALUATE
)
SELECT
    i.IndustryName AS "業界",
    COUNT(DISTINCT p.ProjectID) AS "プロジェクト数",
    SUM(CASE WHEN ps.Status = '完了' THEN 1 ELSE 0 END) AS "完了",
    SUM(CASE WHEN ps.Status = '進行中' THEN 1 ELSE 0 END) AS "進行中",
    SUM(CASE WHEN ps.Status = '未開始' THEN 1 ELSE 0 END) AS "未開始",
    SUM(CASE WHEN lr.RiskRank = '高' THEN 1 ELSE 0 END) AS "高リスク",
    SUM(CASE WHEN lr.RiskRank = '中' THEN 1 ELSE 0 END) AS "中リスク",
    SUM(CASE WHEN lr.RiskRank = '低' THEN 1 ELSE 0 END) AS "低リスク"
FROM
    INDUSTRY i
    INNER JOIN CUSTOMER c ON i.IndustryID = c.IndustryID
    INNER JOIN PROJECT p ON c.CustomerID = p.CustomerID
    LEFT JOIN ProjectStatus ps ON p.ProjectID = ps.ProjectID
    LEFT JOIN LatestRisk lr ON p.ProjectID = lr.ProjectID AND lr.rn = 1
GROUP BY
    i.IndustryID, i.IndustryName
ORDER BY
    "プロジェクト数" DESC;

-- ================================================
-- 【クエリ10】担当者の稼働状況（現在進行中のプロジェクト）
-- 各担当者が現在参画しているプロジェクト一覧
-- ================================================
WITH ActiveProjects AS (
    SELECT
        p.ProjectID,
        p.ProjectName
    FROM
        PROJECT p
        INNER JOIN PROJECT_START ps ON p.ProjectID = ps.ProjectID
        LEFT JOIN PROJECT_COMPLETE pc ON p.ProjectID = pc.ProjectID
    WHERE
        pc.CompleteDateTime IS NULL
),
CurrentAssignments AS (
    SELECT
        pa.ProjectID,
        pa.PersonID,
        pa.RoleID
    FROM
        PERSON_ASSIGN pa
    WHERE
        NOT EXISTS (
            SELECT 1
            FROM PERSON_REPLACE pr
            WHERE pr.ProjectID = pa.ProjectID
              AND pr.OldPersonID = pa.PersonID
              AND pr.RoleID = pa.RoleID
              AND pr.ReplaceDateTime > pa.AssignDateTime
        )
)
SELECT
    per.PersonID,
    per.Name AS "担当者名",
    COUNT(DISTINCT ca.ProjectID) AS "稼働プロジェクト数",
    STRING_AGG(ap.ProjectName || '(' || r.RoleName || ')', ', ') AS "プロジェクト（役割）"
FROM
    PERSON per
    LEFT JOIN CurrentAssignments ca ON per.PersonID = ca.PersonID
    LEFT JOIN ActiveProjects ap ON ca.ProjectID = ap.ProjectID
    LEFT JOIN ROLE r ON ca.RoleID = r.RoleID
GROUP BY
    per.PersonID, per.Name
ORDER BY
    "稼働プロジェクト数" DESC, per.Name;

-- ================================================
-- 【クエリ11】プロジェクトのタイムライン（全イベント統合）
-- 全イベントテーブルをUNIONして時系列表示
-- ================================================
SELECT
    p.ProjectID,
    p.ProjectName AS "プロジェクト名",
    'プロジェクト開始' AS "イベント種別",
    ps.StartDateTime AS "発生日時",
    per.Name AS "関連人物",
    NULL AS "詳細情報"
FROM
    PROJECT_START ps
    INNER JOIN PROJECT p ON ps.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON ps.RegisteredBy = per.PersonID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    '組織参画',
    oj.JoinDateTime,
    o.OrganizationName,
    o.OrganizationType
FROM
    ORGANIZATION_JOIN oj
    INNER JOIN PROJECT p ON oj.ProjectID = p.ProjectID
    INNER JOIN ORGANIZATION o ON oj.OrganizationID = o.OrganizationID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    '担当者アサイン',
    pa.AssignDateTime,
    per.Name,
    r.RoleName
FROM
    PERSON_ASSIGN pa
    INNER JOIN PROJECT p ON pa.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON pa.PersonID = per.PersonID
    INNER JOIN ROLE r ON pa.RoleID = r.RoleID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    '担当者交代',
    pr.ReplaceDateTime,
    old_per.Name || ' → ' || new_per.Name,
    r.RoleName
FROM
    PERSON_REPLACE pr
    INNER JOIN PROJECT p ON pr.ProjectID = p.ProjectID
    INNER JOIN PERSON old_per ON pr.OldPersonID = old_per.PersonID
    INNER JOIN PERSON new_per ON pr.NewPersonID = new_per.PersonID
    INNER JOIN ROLE r ON pr.RoleID = r.RoleID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    'リスク評価',
    re.EvaluateDateTime,
    per.Name,
    'リスクランク: ' || re.RiskRank
FROM
    RISK_EVALUATE re
    INNER JOIN PROJECT p ON re.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON re.EvaluatedBy = per.PersonID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    '支援実施',
    se.ExecuteDateTime,
    per.Name,
    st.SupportTypeName
FROM
    SUPPORT_EXECUTE se
    INNER JOIN PROJECT p ON se.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON se.SupportPersonID = per.PersonID
    INNER JOIN SUPPORT_TYPE st ON se.SupportTypeID = st.SupportTypeID

UNION ALL

SELECT
    p.ProjectID,
    p.ProjectName,
    'プロジェクト完了',
    pc.CompleteDateTime,
    per.Name,
    '実績工数: ' || pc.ActualEffort::TEXT
FROM
    PROJECT_COMPLETE pc
    INNER JOIN PROJECT p ON pc.ProjectID = p.ProjectID
    INNER JOIN PERSON per ON pc.RegisteredBy = per.PersonID

ORDER BY
    ProjectID, "発生日時";
