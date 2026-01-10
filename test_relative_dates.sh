#!/bin/bash
# 相対日付版サンプルデータのテスト用スクリプト

echo "🔄 既存データをクリアして相対日付版を投入します..."

# コンテナ内でSQLを実行
docker exec cc-data-modeler-postgres psql -U datamodeler -d immutable_model_db << SQL
-- 既存データ削除（外部キー制約があるので順序に注意）
DELETE FROM CONFIRMATION_SEND;
DELETE FROM PAYMENT;
DELETE FROM INVOICE_SEND;
DELETE FROM INVOICE;
DELETE FROM CUSTOMER;

-- シーケンスリセット
ALTER SEQUENCE customer_customerid_seq RESTART WITH 1;
ALTER SEQUENCE invoice_invoiceid_seq RESTART WITH 1;
ALTER SEQUENCE invoice_send_eventid_seq RESTART WITH 1;
ALTER SEQUENCE payment_paymentid_seq RESTART WITH 1;
ALTER SEQUENCE confirmation_send_confirmationid_seq RESTART WITH 1;
SQL

echo "✅ 既存データクリア完了"

# 相対日付版サンプルデータ投入
docker exec -i cc-data-modeler-postgres psql -U datamodeler -d immutable_model_db < /Users/akiraabe/practice/cc-data-modeler/artifacts/sample_data_relative.sql

echo ""
echo "📊 投入結果確認:"
docker exec cc-data-modeler-postgres psql -U datamodeler -d immutable_model_db -c "
SELECT
    'CUSTOMER' AS table_name,
    COUNT(*) AS count
FROM CUSTOMER
UNION ALL
SELECT 'INVOICE', COUNT(*) FROM INVOICE
UNION ALL
SELECT 'INVOICE_SEND', COUNT(*) FROM INVOICE_SEND
UNION ALL
SELECT 'PAYMENT', COUNT(*) FROM PAYMENT
UNION ALL
SELECT 'CONFIRMATION_SEND', COUNT(*) FROM CONFIRMATION_SEND;
"

echo ""
echo "🔍 未入金請求書一覧（期日前/期日超過の状態確認）:"
docker exec cc-data-modeler-postgres psql -U datamodeler -d immutable_model_db -c "
SELECT
    i.InvoiceID,
    i.InvoiceNumber AS \"請求番号\",
    c.Name AS \"顧客名\",
    i.DueDate AS \"支払期日\",
    CASE
        WHEN i.DueDate > CURRENT_DATE THEN '期日前'
        ELSE '期日超過'
    END AS \"状態\",
    COALESCE(SUM(p.PaymentAmount), 0) AS \"入金済み額\",
    i.Amount - COALESCE(SUM(p.PaymentAmount), 0) AS \"未入金額\"
FROM
    INVOICE i
    INNER JOIN CUSTOMER c ON i.CustomerID = c.CustomerID
    LEFT JOIN PAYMENT p ON i.InvoiceID = p.InvoiceID
GROUP BY
    i.InvoiceID, i.InvoiceNumber, c.Name, i.DueDate, i.Amount
HAVING
    i.Amount - COALESCE(SUM(p.PaymentAmount), 0) > 0
ORDER BY
    i.DueDate;
"

echo ""
echo "✅ 相対日付版サンプルデータのテスト完了"
