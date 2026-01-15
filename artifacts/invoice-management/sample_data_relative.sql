-- ================================================
-- サンプルデータINSERT（相対日付版）
-- イミュータブルデータモデルのデモ用データ
-- いつ実行しても意図したシナリオが再現されます
-- ================================================

-- ================================================
-- リソースデータ投入
-- ================================================

-- 顧客データ（3社）
INSERT INTO CUSTOMER (name, address, phone, created_at) VALUES
('株式会社ABC商事', '東京都渋谷区渋谷1-1-1', '03-1111-1111', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('XYZ株式会社', '大阪府大阪市北区梅田2-2-2', '06-2222-2222', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('サンプル工業株式会社', '神奈川県横浜市西区みなとみらい3-3-3', '045-3333-3333', CURRENT_TIMESTAMP - INTERVAL '340 days');

-- 請求書データ（5件）
INSERT INTO INVOICE (customer_id, invoice_number, issue_date, amount, due_date) VALUES
-- 請求書1: 正常支払い済み（60日前発行、30日前期日、すでに支払い済み）
(1, 'INV-DEMO-0001', CURRENT_DATE - INTERVAL '60 days', 100000.00, CURRENT_DATE - INTERVAL '30 days'),

-- 請求書2: 遅延支払い済み（90日前発行、60日前期日、遅延後に支払い済み）
(1, 'INV-DEMO-0002', CURRENT_DATE - INTERVAL '90 days', 150000.00, CURRENT_DATE - INTERVAL '60 days'),

-- 請求書3: 分割払い済み（75日前発行、45日前期日、2回に分けて支払い済み）
(2, 'INV-DEMO-0003', CURRENT_DATE - INTERVAL '75 days', 200000.00, CURRENT_DATE - INTERVAL '45 days'),

-- 請求書4: 未入金・期日超過・督促済み（50日前発行、20日前期日、未入金）
(2, 'INV-DEMO-0004', CURRENT_DATE - INTERVAL '50 days', 180000.00, CURRENT_DATE - INTERVAL '20 days'),

-- 請求書5: 未入金・期日前（10日前発行、20日後期日、まだ期日前）
(3, 'INV-DEMO-0005', CURRENT_DATE - INTERVAL '10 days', 250000.00, CURRENT_DATE + INTERVAL '20 days');

-- ================================================
-- イベントデータ投入（時系列で発生したイベント）
-- ================================================

-- シナリオ1: 顧客1（ABC商事）の請求書1 → 正常に支払い完了
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(1, 1, CURRENT_TIMESTAMP - INTERVAL '60 days', 'メール');

INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(1, 1, CURRENT_TIMESTAMP - INTERVAL '35 days', 100000.00, '銀行振込');

-- シナリオ2: 顧客1（ABC商事）の請求書2 → 期日超過 → 確認状送付 → 遅延入金
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(2, 1, CURRENT_TIMESTAMP - INTERVAL '90 days', 'メール');

-- 期日超過後に確認状送付
INSERT INTO CONFIRMATION_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(2, 1, CURRENT_TIMESTAMP - INTERVAL '53 days', 'メール');

-- 確認状後に入金
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(2, 1, CURRENT_TIMESTAMP - INTERVAL '50 days', 150000.00, '銀行振込');

-- シナリオ3: 顧客2（XYZ株式会社）の請求書3 → 分割払い（2回に分けて入金）
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(3, 2, CURRENT_TIMESTAMP - INTERVAL '75 days', 'メール');

-- 1回目の入金（半額、期日前）
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(3, 2, CURRENT_TIMESTAMP - INTERVAL '50 days', 100000.00, '銀行振込');

-- 2回目の入金（残額、期日前）
INSERT INTO PAYMENT (invoice_id, customer_id, payment_date_time, payment_amount, payment_method) VALUES
(3, 2, CURRENT_TIMESTAMP - INTERVAL '40 days', 100000.00, '銀行振込');

-- シナリオ4: 顧客2（XYZ株式会社）の請求書4 → 期日超過 → 督促済み → まだ未入金
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(4, 2, CURRENT_TIMESTAMP - INTERVAL '50 days', 'メール');

-- 期日超過後に確認状送付
INSERT INTO CONFIRMATION_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(4, 2, CURRENT_TIMESTAMP - INTERVAL '17 days', 'メール');

-- シナリオ5: 顧客3（サンプル工業）の請求書5 → 送付済み → まだ期日前
INSERT INTO INVOICE_SEND (invoice_id, customer_id, send_date_time, send_method) VALUES
(5, 3, CURRENT_TIMESTAMP - INTERVAL '10 days', 'メール');

-- まだ期日前なので入金イベントなし

-- ================================================
-- データサマリー（相対日付版）
-- ================================================
-- リソース:
--   顧客: 3社
--   請求書: 5件
-- イベント:
--   請求書送付: 5件
--   入金: 4件（請求書1,2,3で発生、請求書3は分割2回）
--   確認状送付: 2件（請求書2,4で発生）
--
-- 状態パターン（実行日時に関わらず一定）:
--   ✅ 正常支払い: 請求書1（30日前に期日、35日前に支払い済み）
--   ⚠️ 遅延支払い: 請求書2（60日前に期日、50日前に遅延支払い）
--   💰 分割支払い: 請求書3（45日前に期日、50日前と40日前に分割支払い）
--   ❌ 未入金（督促済み）: 請求書4（20日前に期日超過、未入金）
--   ⏳ 未入金（期日前）: 請求書5（20日後が期日、まだ期日前）
-- ================================================
