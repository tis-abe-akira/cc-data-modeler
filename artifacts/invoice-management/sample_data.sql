-- ================================================
-- サンプルデータINSERT
-- イミュータブルデータモデルのデモ用データ
-- ================================================

-- ================================================
-- リソースデータ投入
-- ================================================

-- 顧客データ（3社）
INSERT INTO CUSTOMER (name, address, phone, created_at) VALUES
('株式会社ABC商事', '東京都渋谷区渋谷1-1-1', '03-1111-1111', '2024-01-10 10:00:00+09'),
('XYZ株式会社', '大阪府大阪市北区梅田2-2-2', '06-2222-2222', '2024-01-15 14:30:00+09'),
('サンプル工業株式会社', '神奈川県横浜市西区みなとみらい3-3-3', '045-3333-3333', '2024-02-01 09:00:00+09');

-- 請求書データ（5件）
INSERT INTO INVOICE (customer_id, invoice_number, issue_date, amount, due_date) VALUES
(1, 'INV-2024-0001', '2024-03-01', 100000.00, '2024-03-31'),
(1, 'INV-2024-0002', '2024-04-01', 150000.00, '2024-04-30'),
(2, 'INV-2024-0003', '2024-03-15', 200000.00, '2024-04-15'),
(2, 'INV-2024-0004', '2024-05-01', 180000.00, '2024-05-31'),
(3, 'INV-2024-0005', '2024-04-10', 250000.00, '2024-05-10');

-- ================================================
-- イベントデータ投入（時系列で発生したイベント）
-- ================================================

-- シナリオ1: 顧客1（ABC商事）の請求書1 → 正常に支払い完了
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(1, 1, '2024-03-01 10:00:00+09', 'メール');

INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(1, 1, '2024-03-25 15:30:00+09', 100000.00, '銀行振込');

-- シナリオ2: 顧客1（ABC商事）の請求書2 → 期日超過 → 確認状送付 → 遅延入金
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(2, 1, '2024-04-01 10:00:00+09', 'メール');

-- 期日（4/30）を過ぎても入金なし → 確認状送付（5/7）
INSERT INTO CONFIRMATION_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(2, 1, '2024-05-07 11:00:00+09', 'メール');

-- 確認状後に入金（5/10）
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(2, 1, '2024-05-10 16:00:00+09', 150000.00, '銀行振込');

-- シナリオ3: 顧客2（XYZ株式会社）の請求書3 → 分割払い（2回に分けて入金）
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(3, 2, '2024-03-15 10:00:00+09', 'メール');

-- 1回目の入金（半額）
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(3, 2, '2024-03-30 14:00:00+09', 100000.00, '銀行振込');

-- 2回目の入金（残額）
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(3, 2, '2024-04-10 14:30:00+09', 100000.00, '銀行振込');

-- シナリオ4: 顧客2（XYZ株式会社）の請求書4 → 期日超過 → まだ未入金
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(4, 2, '2024-05-01 10:00:00+09', 'メール');

-- 期日（5/31）を過ぎたが未入金 → 確認状送付（6/3）
INSERT INTO CONFIRMATION_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(4, 2, '2024-06-03 10:00:00+09', 'メール');

-- シナリオ5: 顧客3（サンプル工業）の請求書5 → 送付したが期日前のためまだ未入金
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(5, 3, '2024-04-10 10:00:00+09', 'メール');

-- まだ期日（5/10）前なので入金イベントなし

-- ================================================
-- データサマリー
-- ================================================
-- リソース:
--   顧客: 3社
--   請求書: 5件
-- イベント:
--   請求書送付: 5件
--   入金: 4件（請求書1,2,3で発生、請求書3は分割2回）
--   確認状送付: 2件（請求書2,4で発生）
--
-- 状態パターン:
--   ✅ 正常支払い: 請求書1
--   ⚠️ 遅延支払い: 請求書2
--   💰 分割支払い: 請求書3
--   ❌ 未入金（督促済み）: 請求書4
--   ⏳ 未入金（期日前）: 請求書5
-- ================================================
