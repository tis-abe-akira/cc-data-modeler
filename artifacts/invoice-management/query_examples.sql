-- ================================================
-- イミュータブルデータモデル クエリ例集
-- 複雑だけど強力！生成AIでサポート可能なクエリ集
-- ================================================

-- ================================================
-- 【クエリ1】未入金請求書の一覧
-- イミュータブルモデルの特徴: 入金イベントの有無で判定
-- ================================================
SELECT
    i.invoice_id,
    i.invoice_number AS "請求番号",
    c.name AS "顧客名",
    i.issue_date AS "発行日",
    i.due_date AS "支払期日",
    i.amount AS "請求金額",
    COALESCE(SUM(p.payment_amount), 0) AS "入金済み額",
    i.amount - COALESCE(SUM(p.payment_amount), 0) AS "未入金額",
    CASE
        WHEN CURRENT_DATE > i.due_date THEN '期日超過'
        ELSE '期日内'
    END AS "状態"
FROM
    INVOICE i
    INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id
    LEFT JOIN PAYMENT p ON i.invoice_id = p.invoice_id
GROUP BY
    i.invoice_id, i.invoice_number, c.name, i.issue_date, i.due_date, i.amount
HAVING
    i.amount - COALESCE(SUM(p.payment_amount), 0) > 0
ORDER BY
    i.due_date;

-- ================================================
-- 【クエリ2】確認状送付が必要な請求書
-- 条件: 期日超過 & 未入金 & まだ確認状を送っていない
-- ================================================
WITH UnpaidInvoices AS (
    SELECT
        i.invoice_id,
        i.invoice_number,
        c.name AS customer_name,
        i.due_date,
        i.amount,
        COALESCE(SUM(p.payment_amount), 0) AS paid_amount
    FROM
        INVOICE i
        INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id
        LEFT JOIN PAYMENT p ON i.invoice_id = p.invoice_id
    WHERE
        i.due_date < CURRENT_DATE
    GROUP BY
        i.invoice_id, i.invoice_number, c.name, i.due_date, i.amount
    HAVING
        i.amount - COALESCE(SUM(p.payment_amount), 0) > 0
)
SELECT
    u.invoice_id,
    u.invoice_number AS "請求番号",
    u.customer_name AS "顧客名",
    u.due_date AS "支払期日",
    CURRENT_DATE - u.due_date AS "超過日数",
    u.amount AS "請求金額",
    u.paid_amount AS "入金済み額",
    u.amount - u.paid_amount AS "未入金額"
FROM
    UnpaidInvoices u
WHERE
    NOT EXISTS (
        SELECT 1
        FROM CONFIRMATION_SEND cs
        WHERE cs.invoice_id = u.invoice_id
    )
ORDER BY
    u.due_date;

-- ================================================
-- 【クエリ3】入金状況サマリー（顧客別）
-- イミュータブルモデルの特徴: 集約で現在の状態を計算
-- ================================================
SELECT
    c.customer_id,
    c.name AS "顧客名",
    COUNT(DISTINCT i.invoice_id) AS "請求書数",
    SUM(i.amount) AS "請求総額",
    COALESCE(SUM(p.payment_amount), 0) AS "入金総額",
    SUM(i.amount) - COALESCE(SUM(p.payment_amount), 0) AS "未入金総額",
    ROUND(
        COALESCE(SUM(p.payment_amount), 0) * 100.0 / NULLIF(SUM(i.amount), 0),
        2
    ) AS "入金率(%)"
FROM
    CUSTOMER c
    INNER JOIN INVOICE i ON c.customer_id = i.customer_id
    LEFT JOIN PAYMENT p ON i.invoice_id = p.invoice_id
GROUP BY
    c.customer_id, c.name
ORDER BY
    "未入金総額" DESC;

-- ================================================
-- 【クエリ4】イベント履歴（時系列）
-- イミュータブルモデルの真骨頂: すべてのイベントが記録されている
-- ================================================
WITH AllEvents AS (
    -- 請求書送付イベント
    SELECT
        i.invoice_id,
        i.invoice_number,
        c.name AS customer_name,
        '請求書送付' AS event_type,
        isnd.send_date_time AS event_date_time,
        isnd.send_method AS detail,
        NULL::NUMERIC AS amount
    FROM
        INVOICE_SEND isnd
        INNER JOIN INVOICE i ON isnd.invoice_id = i.invoice_id
        INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id

    UNION ALL

    -- 入金イベント
    SELECT
        i.invoice_id,
        i.invoice_number,
        c.name AS customer_name,
        '入金' AS event_type,
        p.payment_date_time AS event_date_time,
        p.payment_method AS detail,
        p.payment_amount AS amount
    FROM
        PAYMENT p
        INNER JOIN INVOICE i ON p.invoice_id = i.invoice_id
        INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id

    UNION ALL

    -- 確認状送付イベント
    SELECT
        i.invoice_id,
        i.invoice_number,
        c.name AS customer_name,
        '確認状送付' AS event_type,
        cs.send_date_time AS event_date_time,
        cs.send_method AS detail,
        NULL::NUMERIC AS amount
    FROM
        CONFIRMATION_SEND cs
        INNER JOIN INVOICE i ON cs.invoice_id = i.invoice_id
        INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id
)
SELECT
    invoice_number AS "請求番号",
    customer_name AS "顧客名",
    event_type AS "イベント種別",
    event_date_time AS "発生日時",
    detail AS "詳細",
    amount AS "金額"
FROM
    AllEvents
ORDER BY
    invoice_id, event_date_time;

-- ================================================
-- 【クエリ5】分割払いの検出
-- 複数回の入金イベントがある請求書を特定
-- ================================================
SELECT
    i.invoice_number AS "請求番号",
    c.name AS "顧客名",
    i.amount AS "請求金額",
    COUNT(p.payment_id) AS "入金回数",
    STRING_AGG(
        p.payment_date_time::DATE || ': ' || p.payment_amount || '円',
        ', '
        ORDER BY p.payment_date_time
    ) AS "入金履歴",
    SUM(p.payment_amount) AS "入金総額"
FROM
    INVOICE i
    INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id
    INNER JOIN PAYMENT p ON i.invoice_id = p.invoice_id
GROUP BY
    i.invoice_id, i.invoice_number, c.name, i.amount
HAVING
    COUNT(p.payment_id) > 1
ORDER BY
    COUNT(p.payment_id) DESC;

-- ================================================
-- 【クエリ6】督促が必要な顧客リスト
-- 期日超過 & 未入金の請求書が多い順
-- ================================================
WITH OverdueUnpaid AS (
    SELECT
        i.customer_id,
        i.invoice_id,
        i.amount,
        COALESCE(SUM(p.payment_amount), 0) AS paid_amount
    FROM
        INVOICE i
        LEFT JOIN PAYMENT p ON i.invoice_id = p.invoice_id
    WHERE
        i.due_date < CURRENT_DATE
    GROUP BY
        i.customer_id, i.invoice_id, i.amount
    HAVING
        i.amount - COALESCE(SUM(p.payment_amount), 0) > 0
)
SELECT
    c.customer_id,
    c.name AS "顧客名",
    c.phone AS "電話番号",
    COUNT(o.invoice_id) AS "未入金請求書数",
    SUM(o.amount - o.paid_amount) AS "未入金総額",
    MAX(cs.send_date_time) AS "最終確認状送付日"
FROM
    CUSTOMER c
    INNER JOIN OverdueUnpaid o ON c.customer_id = o.customer_id
    LEFT JOIN CONFIRMATION_SEND cs ON o.invoice_id = cs.invoice_id
GROUP BY
    c.customer_id, c.name, c.phone
ORDER BY
    "未入金総額" DESC;

-- ================================================
-- 【クエリ7】請求書の詳細ステータス（1件の請求書の全情報）
-- イミュータブルモデル: すべてのイベント履歴から状態を組み立てる
-- ================================================
-- 例: 請求書ID=2 の詳細情報を取得
WITH InvoiceDetail AS (
    SELECT
        i.invoice_id,
        i.invoice_number,
        c.name AS customer_name,
        c.phone AS customer_phone,
        i.issue_date,
        i.due_date,
        i.amount,
        COALESCE(SUM(p.payment_amount), 0) AS paid_amount,
        i.amount - COALESCE(SUM(p.payment_amount), 0) AS unpaid_amount
    FROM
        INVOICE i
        INNER JOIN CUSTOMER c ON i.customer_id = c.customer_id
        LEFT JOIN PAYMENT p ON i.invoice_id = p.invoice_id
    WHERE
        i.invoice_id = 2
    GROUP BY
        i.invoice_id, i.invoice_number, c.name, c.phone, i.issue_date, i.due_date, i.amount
)
SELECT
    d.*,
    (SELECT send_date_time FROM INVOICE_SEND WHERE invoice_id = d.invoice_id) AS "請求書送付日時",
    (SELECT COUNT(*) FROM PAYMENT WHERE invoice_id = d.invoice_id) AS "入金回数",
    (SELECT COUNT(*) FROM CONFIRMATION_SEND WHERE invoice_id = d.invoice_id) AS "確認状送付回数",
    CASE
        WHEN d.unpaid_amount = 0 THEN '入金完了'
        WHEN d.due_date >= CURRENT_DATE THEN '期日内未入金'
        WHEN EXISTS (SELECT 1 FROM CONFIRMATION_SEND WHERE invoice_id = d.invoice_id) THEN '督促済み未入金'
        ELSE '期日超過未入金'
    END AS "ステータス"
FROM
    InvoiceDetail d;

-- ================================================
-- 【まとめ】
-- イミュータブルデータモデルの特徴:
-- ✅ すべてのイベントが履歴として残る（監査証跡）
-- ✅ 状態フラグ不要、イベントから現在の状態を計算
-- ✅ 複雑なSQLになるが、生成AIでサポート可能
-- ✅ ビジネスロジックの変更に強い（過去データも再計算可能）
-- ================================================
