-- ================================================
-- イミュータブルデータモデル DDL
-- 生成日時: 2026-01-10
-- ================================================

-- ================================================
-- リソーステーブル
-- ================================================

-- 顧客テーブル
CREATE TABLE CUSTOMER (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE CUSTOMER IS '顧客';
COMMENT ON COLUMN CUSTOMER.customer_id IS '顧客ID';
COMMENT ON COLUMN CUSTOMER.name IS '顧客名';
COMMENT ON COLUMN CUSTOMER.address IS '住所';
COMMENT ON COLUMN CUSTOMER.phone IS '電話番号';
COMMENT ON COLUMN CUSTOMER.created_at IS '作成日時';

-- 請求書テーブル
CREATE TABLE INVOICE (
    invoice_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    invoice_number VARCHAR(50) NOT NULL,
    issue_date DATE NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    due_date DATE NOT NULL,
    CONSTRAINT fk_invoice_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT
);

COMMENT ON TABLE INVOICE IS '請求書';
COMMENT ON COLUMN INVOICE.invoice_id IS '請求書ID';
COMMENT ON COLUMN INVOICE.customer_id IS '顧客ID';
COMMENT ON COLUMN INVOICE.invoice_number IS '請求番号';
COMMENT ON COLUMN INVOICE.issue_date IS '発行日';
COMMENT ON COLUMN INVOICE.amount IS '請求金額';
COMMENT ON COLUMN INVOICE.due_date IS '支払期日';

-- ================================================
-- イベントテーブル
-- ================================================

-- 請求書送付イベント
CREATE TABLE INVOICE_SEND (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    send_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    send_method VARCHAR(50),
    CONSTRAINT fk_invoice_send_invoice FOREIGN KEY (invoice_id)
        REFERENCES INVOICE(invoice_id) ON DELETE RESTRICT,
    CONSTRAINT fk_invoice_send_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT
);

COMMENT ON TABLE INVOICE_SEND IS '請求書送付イベント';
COMMENT ON COLUMN INVOICE_SEND.event_id IS 'イベントID';
COMMENT ON COLUMN INVOICE_SEND.invoice_id IS '請求書ID';
COMMENT ON COLUMN INVOICE_SEND.customer_id IS '顧客ID';
COMMENT ON COLUMN INVOICE_SEND.send_date_time IS '送付日時';
COMMENT ON COLUMN INVOICE_SEND.send_method IS '送付方法';

-- 入金イベント
CREATE TABLE PAYMENT (
    payment_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    payment_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    payment_amount NUMERIC(10,2) NOT NULL,
    payment_method VARCHAR(50),
    CONSTRAINT fk_payment_invoice FOREIGN KEY (invoice_id)
        REFERENCES INVOICE(invoice_id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PAYMENT IS '入金イベント';
COMMENT ON COLUMN PAYMENT.payment_id IS '入金ID';
COMMENT ON COLUMN PAYMENT.invoice_id IS '請求書ID';
COMMENT ON COLUMN PAYMENT.customer_id IS '顧客ID';
COMMENT ON COLUMN PAYMENT.payment_date_time IS '入金日時';
COMMENT ON COLUMN PAYMENT.payment_amount IS '入金額';
COMMENT ON COLUMN PAYMENT.payment_method IS '入金方法';

-- 確認状送付イベント
CREATE TABLE CONFIRMATION_SEND (
    confirmation_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    send_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    send_method VARCHAR(50),
    CONSTRAINT fk_confirmation_send_invoice FOREIGN KEY (invoice_id)
        REFERENCES INVOICE(invoice_id) ON DELETE RESTRICT,
    CONSTRAINT fk_confirmation_send_customer FOREIGN KEY (customer_id)
        REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT
);

COMMENT ON TABLE CONFIRMATION_SEND IS '確認状送付イベント';
COMMENT ON COLUMN CONFIRMATION_SEND.confirmation_id IS '確認状ID';
COMMENT ON COLUMN CONFIRMATION_SEND.invoice_id IS '請求書ID';
COMMENT ON COLUMN CONFIRMATION_SEND.customer_id IS '顧客ID';
COMMENT ON COLUMN CONFIRMATION_SEND.send_date_time IS '送付日時';
COMMENT ON COLUMN CONFIRMATION_SEND.send_method IS '送付方法';

-- ================================================
-- インデックス（パフォーマンス最適化）
-- ================================================

-- 請求書インデックス
CREATE INDEX idx_invoice_customer ON INVOICE(customer_id);
CREATE INDEX idx_invoice_duedate ON INVOICE(due_date);
CREATE INDEX idx_invoice_number ON INVOICE(invoice_number);

-- 請求書送付イベントインデックス
CREATE INDEX idx_invoice_send_customer ON INVOICE_SEND(customer_id);
CREATE INDEX idx_invoice_send_invoice ON INVOICE_SEND(invoice_id);
CREATE INDEX idx_invoice_send_datetime ON INVOICE_SEND(send_date_time);

-- 入金イベントインデックス
CREATE INDEX idx_payment_customer ON PAYMENT(customer_id);
CREATE INDEX idx_payment_invoice ON PAYMENT(invoice_id);
CREATE INDEX idx_payment_datetime ON PAYMENT(payment_date_time);

-- 確認状送付イベントインデックス
CREATE INDEX idx_confirmation_send_customer ON CONFIRMATION_SEND(customer_id);
CREATE INDEX idx_confirmation_send_invoice ON CONFIRMATION_SEND(invoice_id);
CREATE INDEX idx_confirmation_send_datetime ON CONFIRMATION_SEND(send_date_time);
