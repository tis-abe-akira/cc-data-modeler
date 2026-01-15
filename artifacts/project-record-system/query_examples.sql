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
    p.project_id,
    p.project_name AS "プロジェクト名",
    c.customer_name AS "顧客名",
    i.industry_name AS "業界",
    p.planned_start_date AS "計画開始日",
    p.planned_end_date AS "計画終了日",
    ps.start_date_time AS "実際の開始日時",
    pc.complete_date_time AS "完了日時",
    CASE
        WHEN pc.complete_date_time IS NOT NULL THEN '完了'
        WHEN ps.start_date_time IS NOT NULL THEN '進行中'
        ELSE '未開始'
    END AS "状態",
    pc.actual_effort AS "実績工数"
FROM
    PROJECT p
    INNER JOIN CUSTOMER c ON p.customer_id = c.customer_id
    LEFT JOIN INDUSTRY i ON c.industry_id = i.industry_id
    LEFT JOIN PROJECT_START ps ON p.project_id = ps.project_id
    LEFT JOIN PROJECT_COMPLETE pc ON p.project_id = pc.project_id
ORDER BY
    p.project_id;

-- ================================================
-- 【クエリ2】プロジェクトの現在の担当者一覧
-- イベントから最新のアサイン状態を取得（交代を考慮）
-- ================================================
WITH LatestAssignment AS (
    SELECT
        pa.project_id,
        pa.person_id,
        pa.role_id,
        pa.assign_date_time,
        ROW_NUMBER() OVER (PARTITION BY pa.project_id, pa.role_id ORDER BY pa.assign_date_time DESC) AS rn
    FROM
        PERSON_ASSIGN pa
    WHERE
        NOT EXISTS (
            -- 交代イベントがない担当者のみ（交代されていない）
            SELECT 1
            FROM PERSON_REPLACE pr
            WHERE pr.project_id = pa.project_id
              AND pr.old_person_id = pa.person_id
              AND pr.role_id = pa.role_id
              AND pr.replace_date_time > pa.assign_date_time
        )
)
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    per.name AS "担当者名",
    r.role_name AS "役割",
    la.assign_date_time AS "アサイン日時"
FROM
    LatestAssignment la
    INNER JOIN PROJECT p ON la.project_id = p.project_id
    INNER JOIN PERSON per ON la.person_id = per.person_id
    INNER JOIN ROLE r ON la.role_id = r.role_id
WHERE
    la.rn = 1
ORDER BY
    p.project_id, r.role_id;

-- ================================================
-- 【クエリ3】プロジェクトのリスク推移
-- イミュータブルモデルの特徴: 時系列でリスク評価の変化を追跡
-- ================================================
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    re.risk_rank AS "リスクランク",
    re.evaluate_date_time AS "評価日時",
    per.name AS "評価者",
    CASE WHEN re.is_system_proposed THEN 'システム提案' ELSE '手動' END AS "提案元",
    CASE WHEN re.is_manual_adjusted THEN '調整あり' ELSE '調整なし' END AS "手動調整"
FROM
    RISK_EVALUATE re
    INNER JOIN PROJECT p ON re.project_id = p.project_id
    INNER JOIN PERSON per ON re.evaluated_by = per.person_id
ORDER BY
    p.project_id, re.evaluate_date_time;

-- ================================================
-- 【クエリ4】プロジェクトの最新リスク評価
-- 各プロジェクトの最新のリスクランクのみ取得
-- ================================================
WITH LatestRiskEvaluate AS (
    SELECT
        project_id,
        risk_rank,
        evaluate_date_time,
        evaluated_by,
        is_system_proposed,
        is_manual_adjusted,
        ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY evaluate_date_time DESC) AS rn
    FROM
        RISK_EVALUATE
)
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    c.customer_name AS "顧客名",
    lre.risk_rank AS "最新リスクランク",
    lre.evaluate_date_time AS "評価日時",
    per.name AS "評価者",
    CASE
        WHEN pc.complete_date_time IS NOT NULL THEN '完了'
        WHEN ps.start_date_time IS NOT NULL THEN '進行中'
        ELSE '未開始'
    END AS "状態"
FROM
    PROJECT p
    INNER JOIN CUSTOMER c ON p.customer_id = c.customer_id
    LEFT JOIN LatestRiskEvaluate lre ON p.project_id = lre.project_id AND lre.rn = 1
    LEFT JOIN PERSON per ON lre.evaluated_by = per.person_id
    LEFT JOIN PROJECT_START ps ON p.project_id = ps.project_id
    LEFT JOIN PROJECT_COMPLETE pc ON p.project_id = pc.project_id
ORDER BY
    CASE lre.risk_rank
        WHEN '高' THEN 1
        WHEN '中' THEN 2
        WHEN '低' THEN 3
        ELSE 4
    END,
    p.project_id;

-- ================================================
-- 【クエリ5】支援実施履歴とその効果
-- イミュータブルモデルの特徴: 支援イベントの記録
-- ================================================
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    st.support_type_name AS "支援タイプ",
    per.name AS "支援担当者",
    se.execute_date_time AS "実施日時",
    se.support_content AS "支援内容",
    se.outcome AS "成果",
    se.memo AS "メモ"
FROM
    SUPPORT_EXECUTE se
    INNER JOIN PROJECT p ON se.project_id = p.project_id
    INNER JOIN SUPPORT_TYPE st ON se.support_type_id = st.support_type_id
    INNER JOIN PERSON per ON se.support_person_id = per.person_id
ORDER BY
    se.execute_date_time DESC;

-- ================================================
-- 【クエリ6】プロジェクトのタグ情報（開発種別・方式・工程）
-- タグ方式の多対多関係から情報を集約
-- ================================================
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    STRING_AGG(DISTINCT dt.development_type_name, ', ') AS "開発種別",
    STRING_AGG(DISTINCT dm.development_method_name, ', ') AS "開発方式",
    STRING_AGG(DISTINCT tp.target_phase_name, ', ') AS "対象工程"
FROM
    PROJECT p
    LEFT JOIN PROJECT_DEVELOPMENT_TYPE pdt ON p.project_id = pdt.project_id
    LEFT JOIN DEVELOPMENT_TYPE dt ON pdt.development_type_id = dt.development_type_id
    LEFT JOIN PROJECT_DEVELOPMENT_METHOD pdm ON p.project_id = pdm.project_id
    LEFT JOIN DEVELOPMENT_METHOD dm ON pdm.development_method_id = dm.development_method_id
    LEFT JOIN PROJECT_TARGET_PHASE ptp ON p.project_id = ptp.project_id
    LEFT JOIN TARGET_PHASE tp ON ptp.target_phase_id = tp.target_phase_id
GROUP BY
    p.project_id, p.project_name
ORDER BY
    p.project_id;

-- ================================================
-- 【クエリ7】参画組織とその階層
-- 自己参照テーブルから組織階層を取得
-- ================================================
WITH RECURSIVE OrgHierarchy AS (
    -- ベースケース: 参画している組織
    SELECT
        oj.project_id,
        o.organization_id,
        o.organization_name,
        o.organization_type,
        o.parent_organization_id,
        1 AS Level,
        o.organization_name AS Path
    FROM
        ORGANIZATION_JOIN oj
        INNER JOIN ORGANIZATION o ON oj.organization_id = o.organization_id

    UNION ALL

    -- 再帰ケース: 親組織を遡る
    SELECT
        oh.project_id,
        parent.organization_id,
        parent.organization_name,
        parent.organization_type,
        parent.parent_organization_id,
        oh.Level + 1,
        parent.organization_name || ' > ' || oh.Path
    FROM
        OrgHierarchy oh
        INNER JOIN ORGANIZATION parent ON oh.parent_organization_id = parent.organization_id
)
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    oh.organization_name AS "組織名",
    oh.organization_type AS "組織種別",
    oh.Level AS "階層レベル",
    oh.Path AS "組織階層パス"
FROM
    OrgHierarchy oh
    INNER JOIN PROJECT p ON oh.project_id = p.project_id
ORDER BY
    p.project_id, oh.Level DESC;

-- ================================================
-- 【クエリ8】担当者交代の履歴
-- イミュータブルモデルの特徴: 交代イベントで履歴を追跡
-- ================================================
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    r.role_name AS "役割",
    old_per.name AS "旧担当者",
    new_per.name AS "新担当者",
    pr.replace_date_time AS "交代日時",
    reg_per.name AS "登録者"
FROM
    PERSON_REPLACE pr
    INNER JOIN PROJECT p ON pr.project_id = p.project_id
    INNER JOIN ROLE r ON pr.role_id = r.role_id
    INNER JOIN PERSON old_per ON pr.old_person_id = old_per.person_id
    INNER JOIN PERSON new_per ON pr.new_person_id = new_per.person_id
    INNER JOIN PERSON reg_per ON pr.registered_by = reg_per.person_id
ORDER BY
    pr.replace_date_time DESC;

-- ================================================
-- 【クエリ9】業界別プロジェクトサマリー
-- 業界ごとのプロジェクト数・状態・リスク分布
-- ================================================
WITH ProjectStatus AS (
    SELECT
        p.project_id,
        p.customer_id,
        CASE
            WHEN pc.complete_date_time IS NOT NULL THEN '完了'
            WHEN ps.start_date_time IS NOT NULL THEN '進行中'
            ELSE '未開始'
        END AS Status
    FROM
        PROJECT p
        LEFT JOIN PROJECT_START ps ON p.project_id = ps.project_id
        LEFT JOIN PROJECT_COMPLETE pc ON p.project_id = pc.project_id
),
LatestRisk AS (
    SELECT
        project_id,
        risk_rank,
        ROW_NUMBER() OVER (PARTITION BY project_id ORDER BY evaluate_date_time DESC) AS rn
    FROM
        RISK_EVALUATE
)
SELECT
    i.industry_name AS "業界",
    COUNT(DISTINCT p.project_id) AS "プロジェクト数",
    SUM(CASE WHEN ps.Status = '完了' THEN 1 ELSE 0 END) AS "完了",
    SUM(CASE WHEN ps.Status = '進行中' THEN 1 ELSE 0 END) AS "進行中",
    SUM(CASE WHEN ps.Status = '未開始' THEN 1 ELSE 0 END) AS "未開始",
    SUM(CASE WHEN lr.risk_rank = '高' THEN 1 ELSE 0 END) AS "高リスク",
    SUM(CASE WHEN lr.risk_rank = '中' THEN 1 ELSE 0 END) AS "中リスク",
    SUM(CASE WHEN lr.risk_rank = '低' THEN 1 ELSE 0 END) AS "低リスク"
FROM
    INDUSTRY i
    INNER JOIN CUSTOMER c ON i.industry_id = c.industry_id
    INNER JOIN PROJECT p ON c.customer_id = p.customer_id
    LEFT JOIN ProjectStatus ps ON p.project_id = ps.project_id
    LEFT JOIN LatestRisk lr ON p.project_id = lr.project_id AND lr.rn = 1
GROUP BY
    i.industry_id, i.industry_name
ORDER BY
    "プロジェクト数" DESC;

-- ================================================
-- 【クエリ10】担当者の稼働状況（現在進行中のプロジェクト）
-- 各担当者が現在参画しているプロジェクト一覧
-- ================================================
WITH ActiveProjects AS (
    SELECT
        p.project_id,
        p.project_name
    FROM
        PROJECT p
        INNER JOIN PROJECT_START ps ON p.project_id = ps.project_id
        LEFT JOIN PROJECT_COMPLETE pc ON p.project_id = pc.project_id
    WHERE
        pc.complete_date_time IS NULL
),
CurrentAssignments AS (
    SELECT
        pa.project_id,
        pa.person_id,
        pa.role_id
    FROM
        PERSON_ASSIGN pa
    WHERE
        NOT EXISTS (
            SELECT 1
            FROM PERSON_REPLACE pr
            WHERE pr.project_id = pa.project_id
              AND pr.old_person_id = pa.person_id
              AND pr.role_id = pa.role_id
              AND pr.replace_date_time > pa.assign_date_time
        )
)
SELECT
    per.person_id,
    per.name AS "担当者名",
    COUNT(DISTINCT ca.project_id) AS "稼働プロジェクト数",
    STRING_AGG(ap.project_name || '(' || r.role_name || ')', ', ') AS "プロジェクト（役割）"
FROM
    PERSON per
    LEFT JOIN CurrentAssignments ca ON per.person_id = ca.person_id
    LEFT JOIN ActiveProjects ap ON ca.project_id = ap.project_id
    LEFT JOIN ROLE r ON ca.role_id = r.role_id
GROUP BY
    per.person_id, per.name
ORDER BY
    "稼働プロジェクト数" DESC, per.name;

-- ================================================
-- 【クエリ11】プロジェクトのタイムライン（全イベント統合）
-- 全イベントテーブルをUNIONして時系列表示
-- ================================================
SELECT
    p.project_id,
    p.project_name AS "プロジェクト名",
    'プロジェクト開始' AS "イベント種別",
    ps.start_date_time AS "発生日時",
    per.name AS "関連人物",
    NULL AS "詳細情報"
FROM
    PROJECT_START ps
    INNER JOIN PROJECT p ON ps.project_id = p.project_id
    INNER JOIN PERSON per ON ps.registered_by = per.person_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    '組織参画',
    oj.join_date_time,
    o.organization_name,
    o.organization_type
FROM
    ORGANIZATION_JOIN oj
    INNER JOIN PROJECT p ON oj.project_id = p.project_id
    INNER JOIN ORGANIZATION o ON oj.organization_id = o.organization_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    '担当者アサイン',
    pa.assign_date_time,
    per.name,
    r.role_name
FROM
    PERSON_ASSIGN pa
    INNER JOIN PROJECT p ON pa.project_id = p.project_id
    INNER JOIN PERSON per ON pa.person_id = per.person_id
    INNER JOIN ROLE r ON pa.role_id = r.role_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    '担当者交代',
    pr.replace_date_time,
    old_per.name || ' → ' || new_per.name,
    r.role_name
FROM
    PERSON_REPLACE pr
    INNER JOIN PROJECT p ON pr.project_id = p.project_id
    INNER JOIN PERSON old_per ON pr.old_person_id = old_per.person_id
    INNER JOIN PERSON new_per ON pr.new_person_id = new_per.person_id
    INNER JOIN ROLE r ON pr.role_id = r.role_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    'リスク評価',
    re.evaluate_date_time,
    per.name,
    'リスクランク: ' || re.risk_rank
FROM
    RISK_EVALUATE re
    INNER JOIN PROJECT p ON re.project_id = p.project_id
    INNER JOIN PERSON per ON re.evaluated_by = per.person_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    '支援実施',
    se.execute_date_time,
    per.name,
    st.support_type_name
FROM
    SUPPORT_EXECUTE se
    INNER JOIN PROJECT p ON se.project_id = p.project_id
    INNER JOIN PERSON per ON se.support_person_id = per.person_id
    INNER JOIN SUPPORT_TYPE st ON se.support_type_id = st.support_type_id

UNION ALL

SELECT
    p.project_id,
    p.project_name,
    'プロジェクト完了',
    pc.complete_date_time,
    per.name,
    '実績工数: ' || pc.actual_effort::TEXT
FROM
    PROJECT_COMPLETE pc
    INNER JOIN PROJECT p ON pc.project_id = p.project_id
    INNER JOIN PERSON per ON pc.registered_by = per.person_id

ORDER BY
    project_id, "発生日時";
