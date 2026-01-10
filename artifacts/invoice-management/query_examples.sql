-- ================================================
-- イミュータブルデータモデル クエリ例集
-- 複雑だけど強力！生成AIでサポート可能なクエリ集
-- ================================================

-- ================================================
-- 【クエリ1】未入金請求書の一覧
-- イミュータブルモデルの特徴: 入金イベントの有無で判定
-- ================================================
SELECT
    i.InvoiceID,
    i.InvoiceNumber AS "請求番号",
    c.Name AS "顧客名",
    i.IssueDate AS "発行日",
    i.DueDate AS "支払期日",
    i.Amount AS "請求金額",
    COALESCE(SUM(p.PaymentAmount), 0) AS "入金済み額",
    i.Amount - COALESCE(SUM(p.PaymentAmount), 0) AS "未入金額",
    CASE
        WHEN CURRENT_DATE > i.DueDate THEN '期日超過'
        ELSE '期日内'
    END AS "状態"
FROM
    INVOICE i
    INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
    LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
GROUP BY
    i.InvoiceID, i.InvoiceNumber, c.Name, i.IssueDate, i.DueDate, i.Amount
HAVING
    i.Amount - COALESCE(SUM(p.PaymentAmount), 0) > 0
ORDER BY
    i.DueDate;

-- ================================================
-- 【クエリ2】確認状送付が必要な請求書
-- 条件: 期日超過 & 未入金 & まだ確認状を送っていない
-- ================================================
WITH UnpaidInvoices AS (
    SELECT
        i.InvoiceID,
        i.InvoiceNumber,
        c.Name AS CustomerName,
        i.DueDate,
        i.Amount,
        COALESCE(SUM(p.PaymentAmount), 0) AS PaidAmount
    FROM
        INVOICE i
        INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
        LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
    WHERE
        i.DueDate < CURRENT_DATE
    GROUP BY
        i.InvoiceID, i.InvoiceNumber, c.Name, i.DueDate, i.Amount
    HAVING
        i.Amount - COALESCE(SUM(p.PaymentAmount), 0) > 0
)
SELECT
    u.InvoiceID,
    u.InvoiceNumber AS "請求番号",
    u.CustomerName AS "顧客名",
    u.DueDate AS "支払期日",
    CURRENT_DATE - u.DueDate AS "超過日数",
    u.Amount AS "請求金額",
    u.PaidAmount AS "入金済み額",
    u.Amount - u.PaidAmount AS "未入金額"
FROM
    UnpaidInvoices u
WHERE
    NOT EXISTS (
        SELECT 1
        FROM CONFIRMATION_SEND cs
        WHERE cs.InvoiceID = u.InvoiceID
    )
ORDER BY
    u.DueDate;

-- ================================================
-- 【クエリ3】入金状況サマリー（顧客別）
-- イミュータブルモデルの特徴: 集約で現在の状態を計算
-- ================================================
SELECT
    c.CustomerID,
    c.Name AS "顧客名",
    COUNT(DISTINCT i.InvoiceID) AS "請求書数",
    SUM(i.Amount) AS "請求総額",
    COALESCE(SUM(p.PaymentAmount), 0) AS "入金総額",
    SUM(i.Amount) - COALESCE(SUM(p.PaymentAmount), 0) AS "未入金総額",
    ROUND(
        COALESCE(SUM(p.PaymentAmount), 0) * 100.0 / NULLIF(SUM(i.Amount), 0),
        2
    ) AS "入金率(%)"
FROM
    CUSTOMER c
    INNER JOIN INVOICE i ON c.CustomerID = i.CustomerID
    LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
GROUP BY
    c.CustomerID, c.Name
ORDER BY
    "未入金総額" DESC;

-- ================================================
-- 【クエリ4】イベント履歴（時系列）
-- イミュータブルモデルの真骨頂: すべてのイベントが記録されている
-- ================================================
WITH AllEvents AS (
    -- 請求書送付イベント
    SELECT
        i.InvoiceID,
        i.InvoiceNumber,
        c.Name AS CustomerName,
        '請求書送付' AS EventType,
        isnd.SendDateTime AS EventDateTime,
        isnd.SendMethod AS Detail,
        NULL::NUMERIC AS Amount
    FROM
        INVOICE_SEND isnd
        INNER JOIN INVOICE i ON isnd.InvoiceID = i.InvoiceID
        INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID

    UNION ALL

    -- 入金イベント
    SELECT
        i.InvoiceID,
        i.InvoiceNumber,
        c.Name AS CustomerName,
        '入金' AS EventType,
        p.PaymentDateTime AS EventDateTime,
        p.PaymentMethod AS Detail,
        p.PaymentAmount AS Amount
    FROM
        PAYMENT p
        INNER JOIN INVOICE i ON p.InvoiceID = i.InvoiceID
        INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID

    UNION ALL

    -- 確認状送付イベント
    SELECT
        i.InvoiceID,
        i.InvoiceNumber,
        c.Name AS CustomerName,
        '確認状送付' AS EventType,
        cs.SendDateTime AS EventDateTime,
        cs.SendMethod AS Detail,
        NULL::NUMERIC AS Amount
    FROM
        CONFIRMATION_SEND cs
        INNER JOIN INVOICE i ON cs.InvoiceID = i.InvoiceID
        INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
)
SELECT
    InvoiceNumber AS "請求番号",
    CustomerName AS "顧客名",
    EventType AS "イベント種別",
    EventDateTime AS "発生日時",
    Detail AS "詳細",
    Amount AS "金額"
FROM
    AllEvents
ORDER BY
    InvoiceID, EventDateTime;

-- ================================================
-- 【クエリ5】分割払いの検出
-- 複数回の入金イベントがある請求書を特定
-- ================================================
SELECT
    i.InvoiceNumber AS "請求番号",
    c.Name AS "顧客名",
    i.Amount AS "請求金額",
    COUNT(p.PaymentID) AS "入金回数",
    STRING_AGG(
        p.PaymentDateTime::DATE || ': ' || p.PaymentAmount || '円',
        ', '
        ORDER BY p.PaymentDateTime
    ) AS "入金履歴",
    SUM(p.PaymentAmount) AS "入金総額"
FROM
    INVOICE i
    INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
    INNER JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
GROUP BY
    i.InvoiceID, i.InvoiceNumber, c.Name, i.Amount
HAVING
    COUNT(p.PaymentID) > 1
ORDER BY
    COUNT(p.PaymentID) DESC;

-- ================================================
-- 【クエリ6】督促が必要な顧客リスト
-- 期日超過 & 未入金の請求書が多い順
-- ================================================
WITH OverdueUnpaid AS (
    SELECT
        i.CustomerID,
        i.InvoiceID,
        i.Amount,
        COALESCE(SUM(p.PaymentAmount), 0) AS PaidAmount
    FROM
        INVOICE i
        LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
    WHERE
        i.DueDate < CURRENT_DATE
    GROUP BY
        i.CustomerID, i.InvoiceID, i.Amount
    HAVING
        i.Amount - COALESCE(SUM(p.PaymentAmount), 0) > 0
)
SELECT
    c.CustomerID,
    c.Name AS "顧客名",
    c.Phone AS "電話番号",
    COUNT(o.InvoiceID) AS "未入金請求書数",
    SUM(o.Amount - o.PaidAmount) AS "未入金総額",
    MAX(cs.SendDateTime) AS "最終確認状送付日"
FROM
    CUSTOMER c
    INNER JOIN OverdueUnpaid o ON c.CustomerID = o.CustomerID
    LEFT JOIN CONFIRMATION_SEND cs ON o.InvoiceID = cs.InvoiceID
GROUP BY
    c.CustomerID, c.Name, c.Phone
ORDER BY
    "未入金総額" DESC;

-- ================================================
-- 【クエリ7】請求書の詳細ステータス（1件の請求書の全情報）
-- イミュータブルモデル: すべてのイベント履歴から状態を組み立てる
-- ================================================
-- 例: 請求書ID=2 の詳細情報を取得
WITH InvoiceDetail AS (
    SELECT
        i.InvoiceID,
        i.InvoiceNumber,
        c.Name AS CustomerName,
        c.Phone AS CustomerPhone,
        i.IssueDate,
        i.DueDate,
        i.Amount,
        COALESCE(SUM(p.PaymentAmount), 0) AS PaidAmount,
        i.Amount - COALESCE(SUM(p.PaymentAmount), 0) AS UnpaidAmount
    FROM
        INVOICE i
        INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
        LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
    WHERE
        i.InvoiceID = 2
    GROUP BY
        i.InvoiceID, i.InvoiceNumber, c.Name, c.Phone, i.IssueDate, i.DueDate, i.Amount
)
SELECT
    d.*,
    (SELECT SendDateTime FROM INVOICE_SEND WHERE InvoiceID = d.InvoiceID) AS "請求書送付日時",
    (SELECT COUNT(*) FROM PAYMENT WHERE InvoiceID = d.InvoiceID) AS "入金回数",
    (SELECT COUNT(*) FROM CONFIRMATION_SEND WHERE InvoiceID = d.InvoiceID) AS "確認状送付回数",
    CASE
        WHEN d.UnpaidAmount = 0 THEN '入金完了'
        WHEN d.DueDate >= CURRENT_DATE THEN '期日内未入金'
        WHEN EXISTS (SELECT 1 FROM CONFIRMATION_SEND WHERE InvoiceID = d.InvoiceID) THEN '督促済み未入金'
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
