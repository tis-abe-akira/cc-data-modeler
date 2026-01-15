-- ================================================
-- イミュータブルデータモデル DDL
-- プロジェクト記録システム
-- 生成日時: 2026-01-15
-- ================================================

-- ================================================
-- リソーステーブル
-- ================================================

-- プロジェクトテーブル
CREATE TABLE PROJECT (
    project_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    customer_id INTEGER NOT NULL,
    estimated_effort DECIMAL(10,2),
    planned_start_date DATE,
    planned_end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE PROJECT IS 'プロジェクト';
COMMENT ON COLUMN PROJECT.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT.project_name IS 'プロジェクト名';
COMMENT ON COLUMN PROJECT.customer_id IS '顧客ID';
COMMENT ON COLUMN PROJECT.estimated_effort IS '受注規模';
COMMENT ON COLUMN PROJECT.planned_start_date IS '計画開始日';
COMMENT ON COLUMN PROJECT.planned_end_date IS '計画終了日';
COMMENT ON COLUMN PROJECT.created_at IS '作成日時';

-- 人テーブル
CREATE TABLE PERSON (
    person_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE PERSON IS '人';
COMMENT ON COLUMN PERSON.person_id IS '人ID';
COMMENT ON COLUMN PERSON.name IS '氏名';
COMMENT ON COLUMN PERSON.email IS 'メールアドレス';
COMMENT ON COLUMN PERSON.created_at IS '作成日時';

-- 組織テーブル
CREATE TABLE ORGANIZATION (
    organization_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(100) NOT NULL,
    organization_type VARCHAR(50),
    parent_organization_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_organization_parent FOREIGN KEY (parent_organization_id)
        REFERENCES ORGANIZATION(organization_id) ON DELETE RESTRICT
);

COMMENT ON TABLE ORGANIZATION IS '組織';
COMMENT ON COLUMN ORGANIZATION.organization_id IS '組織ID';
COMMENT ON COLUMN ORGANIZATION.organization_name IS '組織名';
COMMENT ON COLUMN ORGANIZATION.organization_type IS '組織種別';
COMMENT ON COLUMN ORGANIZATION.parent_organization_id IS '親組織ID';
COMMENT ON COLUMN ORGANIZATION.created_at IS '作成日時';

-- 顧客テーブル
CREATE TABLE CUSTOMER (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    industry_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE CUSTOMER IS '顧客';
COMMENT ON COLUMN CUSTOMER.customer_id IS '顧客ID';
COMMENT ON COLUMN CUSTOMER.customer_name IS '顧客名';
COMMENT ON COLUMN CUSTOMER.industry_id IS '業界ID';
COMMENT ON COLUMN CUSTOMER.created_at IS '作成日時';

-- 業界テーブル
CREATE TABLE INDUSTRY (
    industry_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE INDUSTRY IS '業界';
COMMENT ON COLUMN INDUSTRY.industry_id IS '業界ID';
COMMENT ON COLUMN INDUSTRY.industry_name IS '業界名';
COMMENT ON COLUMN INDUSTRY.created_at IS '作成日時';

-- 役割テーブル
CREATE TABLE ROLE (
    role_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ROLE IS '役割';
COMMENT ON COLUMN ROLE.role_id IS '役割ID';
COMMENT ON COLUMN ROLE.role_name IS '役割名';
COMMENT ON COLUMN ROLE.created_at IS '作成日時';

-- 支援タイプテーブル
CREATE TABLE SUPPORT_TYPE (
    support_type_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    support_type_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE SUPPORT_TYPE IS '支援タイプ';
COMMENT ON COLUMN SUPPORT_TYPE.support_type_id IS '支援タイプID';
COMMENT ON COLUMN SUPPORT_TYPE.support_type_name IS '支援タイプ名';
COMMENT ON COLUMN SUPPORT_TYPE.description IS '説明';
COMMENT ON COLUMN SUPPORT_TYPE.created_at IS '作成日時';

-- ユーザーテーブル
CREATE TABLE USER_ACCOUNT (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    person_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_person FOREIGN KEY (person_id)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE USER_ACCOUNT IS 'ユーザー';
COMMENT ON COLUMN USER_ACCOUNT.user_id IS 'ユーザーID';
COMMENT ON COLUMN USER_ACCOUNT.person_id IS '人ID';
COMMENT ON COLUMN USER_ACCOUNT.username IS 'ユーザー名';
COMMENT ON COLUMN USER_ACCOUNT.created_at IS '作成日時';

-- 開発種別テーブル
CREATE TABLE DEVELOPMENT_TYPE (
    development_type_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    development_type_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE DEVELOPMENT_TYPE IS '開発種別';
COMMENT ON COLUMN DEVELOPMENT_TYPE.development_type_id IS '開発種別ID';
COMMENT ON COLUMN DEVELOPMENT_TYPE.development_type_name IS '開発種別名';
COMMENT ON COLUMN DEVELOPMENT_TYPE.description IS '説明';
COMMENT ON COLUMN DEVELOPMENT_TYPE.created_at IS '作成日時';

-- 開発方式テーブル
CREATE TABLE DEVELOPMENT_METHOD (
    development_method_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    development_method_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE DEVELOPMENT_METHOD IS '開発方式';
COMMENT ON COLUMN DEVELOPMENT_METHOD.development_method_id IS '開発方式ID';
COMMENT ON COLUMN DEVELOPMENT_METHOD.development_method_name IS '開発方式名';
COMMENT ON COLUMN DEVELOPMENT_METHOD.description IS '説明';
COMMENT ON COLUMN DEVELOPMENT_METHOD.created_at IS '作成日時';

-- 対象工程テーブル
CREATE TABLE TARGET_PHASE (
    target_phase_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_phase_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE TARGET_PHASE IS '対象工程';
COMMENT ON COLUMN TARGET_PHASE.target_phase_id IS '対象工程ID';
COMMENT ON COLUMN TARGET_PHASE.target_phase_name IS '対象工程名';
COMMENT ON COLUMN TARGET_PHASE.description IS '説明';
COMMENT ON COLUMN TARGET_PHASE.created_at IS '作成日時';

-- 外部キー制約（リソーステーブル）
ALTER TABLE PROJECT ADD CONSTRAINT fk_project_customer
    FOREIGN KEY (customer_id) REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT;

ALTER TABLE CUSTOMER ADD CONSTRAINT fk_customer_industry
    FOREIGN KEY (industry_id) REFERENCES INDUSTRY(industry_id) ON DELETE RESTRICT;

-- ================================================
-- ジャンクションテーブル（多対多関係）
-- ================================================

-- プロジェクト開発種別テーブル
CREATE TABLE PROJECT_DEVELOPMENT_TYPE (
    project_id INTEGER NOT NULL,
    development_type_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, development_type_id),
    CONSTRAINT fk_pdt_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pdt_development_type FOREIGN KEY (development_type_id)
        REFERENCES DEVELOPMENT_TYPE(development_type_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_DEVELOPMENT_TYPE IS 'プロジェクト開発種別';
COMMENT ON COLUMN PROJECT_DEVELOPMENT_TYPE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_DEVELOPMENT_TYPE.development_type_id IS '開発種別ID';

-- プロジェクト開発方式テーブル
CREATE TABLE PROJECT_DEVELOPMENT_METHOD (
    project_id INTEGER NOT NULL,
    development_method_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, development_method_id),
    CONSTRAINT fk_pdm_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pdm_development_method FOREIGN KEY (development_method_id)
        REFERENCES DEVELOPMENT_METHOD(development_method_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_DEVELOPMENT_METHOD IS 'プロジェクト開発方式';
COMMENT ON COLUMN PROJECT_DEVELOPMENT_METHOD.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_DEVELOPMENT_METHOD.development_method_id IS '開発方式ID';

-- プロジェクト対象工程テーブル
CREATE TABLE PROJECT_TARGET_PHASE (
    project_id INTEGER NOT NULL,
    target_phase_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, target_phase_id),
    CONSTRAINT fk_ptp_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_ptp_target_phase FOREIGN KEY (target_phase_id)
        REFERENCES TARGET_PHASE(target_phase_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_TARGET_PHASE IS 'プロジェクト対象工程';
COMMENT ON COLUMN PROJECT_TARGET_PHASE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_TARGET_PHASE.target_phase_id IS '対象工程ID';

-- ================================================
-- イベントテーブル
-- ================================================

-- プロジェクト開始イベント
CREATE TABLE PROJECT_START (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    start_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    registered_by INTEGER NOT NULL,
    CONSTRAINT fk_project_start_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_start_person FOREIGN KEY (registered_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_START IS 'プロジェクト開始イベント';
COMMENT ON COLUMN PROJECT_START.event_id IS 'イベントID';
COMMENT ON COLUMN PROJECT_START.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_START.start_date_time IS '開始日時';
COMMENT ON COLUMN PROJECT_START.registered_by IS '登録者ID';

-- 組織参画イベント
CREATE TABLE ORGANIZATION_JOIN (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    join_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    registered_by INTEGER NOT NULL,
    CONSTRAINT fk_organization_join_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_organization_join_org FOREIGN KEY (organization_id)
        REFERENCES ORGANIZATION(organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_organization_join_person FOREIGN KEY (registered_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE ORGANIZATION_JOIN IS '組織参画イベント';
COMMENT ON COLUMN ORGANIZATION_JOIN.event_id IS 'イベントID';
COMMENT ON COLUMN ORGANIZATION_JOIN.project_id IS 'プロジェクトID';
COMMENT ON COLUMN ORGANIZATION_JOIN.organization_id IS '組織ID';
COMMENT ON COLUMN ORGANIZATION_JOIN.join_date_time IS '参画日時';
COMMENT ON COLUMN ORGANIZATION_JOIN.registered_by IS '登録者ID';

-- 担当者アサインイベント
CREATE TABLE PERSON_ASSIGN (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assign_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    registered_by INTEGER NOT NULL,
    CONSTRAINT fk_person_assign_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_assign_person FOREIGN KEY (person_id)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_assign_role FOREIGN KEY (role_id)
        REFERENCES ROLE(role_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_assign_registered FOREIGN KEY (registered_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PERSON_ASSIGN IS '担当者アサインイベント';
COMMENT ON COLUMN PERSON_ASSIGN.event_id IS 'イベントID';
COMMENT ON COLUMN PERSON_ASSIGN.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PERSON_ASSIGN.person_id IS '人ID';
COMMENT ON COLUMN PERSON_ASSIGN.role_id IS '役割ID';
COMMENT ON COLUMN PERSON_ASSIGN.assign_date_time IS 'アサイン日時';
COMMENT ON COLUMN PERSON_ASSIGN.registered_by IS '登録者ID';

-- 担当者交代イベント
CREATE TABLE PERSON_REPLACE (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    old_person_id INTEGER NOT NULL,
    new_person_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    replace_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    registered_by INTEGER NOT NULL,
    CONSTRAINT fk_person_replace_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_replace_old FOREIGN KEY (old_person_id)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_replace_new FOREIGN KEY (new_person_id)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_replace_role FOREIGN KEY (role_id)
        REFERENCES ROLE(role_id) ON DELETE RESTRICT,
    CONSTRAINT fk_person_replace_registered FOREIGN KEY (registered_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PERSON_REPLACE IS '担当者交代イベント';
COMMENT ON COLUMN PERSON_REPLACE.event_id IS 'イベントID';
COMMENT ON COLUMN PERSON_REPLACE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PERSON_REPLACE.old_person_id IS '旧担当者ID';
COMMENT ON COLUMN PERSON_REPLACE.new_person_id IS '新担当者ID';
COMMENT ON COLUMN PERSON_REPLACE.role_id IS '役割ID';
COMMENT ON COLUMN PERSON_REPLACE.replace_date_time IS '交代日時';
COMMENT ON COLUMN PERSON_REPLACE.registered_by IS '登録者ID';

-- リスク評価イベント
CREATE TABLE RISK_EVALUATE (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    risk_rank VARCHAR(20),
    evaluate_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    evaluated_by INTEGER NOT NULL,
    is_system_proposed BOOLEAN DEFAULT FALSE,
    is_manual_adjusted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_risk_evaluate_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_risk_evaluate_person FOREIGN KEY (evaluated_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE RISK_EVALUATE IS 'リスク評価イベント';
COMMENT ON COLUMN RISK_EVALUATE.event_id IS 'イベントID';
COMMENT ON COLUMN RISK_EVALUATE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN RISK_EVALUATE.risk_rank IS 'リスクランク';
COMMENT ON COLUMN RISK_EVALUATE.evaluate_date_time IS '評価日時';
COMMENT ON COLUMN RISK_EVALUATE.evaluated_by IS '評価者ID';
COMMENT ON COLUMN RISK_EVALUATE.is_system_proposed IS 'システム提案フラグ';
COMMENT ON COLUMN RISK_EVALUATE.is_manual_adjusted IS '手動調整フラグ';

-- 支援実施イベント
CREATE TABLE SUPPORT_EXECUTE (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    support_type_id INTEGER NOT NULL,
    support_person_id INTEGER NOT NULL,
    execute_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    support_content TEXT,
    outcome TEXT,
    memo TEXT,
    CONSTRAINT fk_support_execute_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_support_execute_type FOREIGN KEY (support_type_id)
        REFERENCES SUPPORT_TYPE(support_type_id) ON DELETE RESTRICT,
    CONSTRAINT fk_support_execute_person FOREIGN KEY (support_person_id)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE SUPPORT_EXECUTE IS '支援実施イベント';
COMMENT ON COLUMN SUPPORT_EXECUTE.event_id IS 'イベントID';
COMMENT ON COLUMN SUPPORT_EXECUTE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN SUPPORT_EXECUTE.support_type_id IS '支援タイプID';
COMMENT ON COLUMN SUPPORT_EXECUTE.support_person_id IS '支援担当者ID';
COMMENT ON COLUMN SUPPORT_EXECUTE.execute_date_time IS '実施日時';
COMMENT ON COLUMN SUPPORT_EXECUTE.support_content IS '支援内容';
COMMENT ON COLUMN SUPPORT_EXECUTE.outcome IS '成果';
COMMENT ON COLUMN SUPPORT_EXECUTE.memo IS 'メモ';

-- プロジェクト完了イベント
CREATE TABLE PROJECT_COMPLETE (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    complete_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_effort DECIMAL(10,2),
    registered_by INTEGER NOT NULL,
    CONSTRAINT fk_project_complete_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT,
    CONSTRAINT fk_project_complete_person FOREIGN KEY (registered_by)
        REFERENCES PERSON(person_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_COMPLETE IS 'プロジェクト完了イベント';
COMMENT ON COLUMN PROJECT_COMPLETE.event_id IS 'イベントID';
COMMENT ON COLUMN PROJECT_COMPLETE.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_COMPLETE.complete_date_time IS '完了日時';
COMMENT ON COLUMN PROJECT_COMPLETE.actual_effort IS '実績工数';
COMMENT ON COLUMN PROJECT_COMPLETE.registered_by IS '登録者ID';

-- ================================================
-- インデックス（パフォーマンス最適化）
-- ================================================

-- プロジェクトインデックス
CREATE INDEX idx_project_customer ON PROJECT(customer_id);
CREATE INDEX idx_project_start_date ON PROJECT(planned_start_date);
CREATE INDEX idx_project_end_date ON PROJECT(planned_end_date);

-- 組織インデックス
CREATE INDEX idx_organization_parent ON ORGANIZATION(parent_organization_id);

-- 顧客インデックス
CREATE INDEX idx_customer_industry ON CUSTOMER(industry_id);

-- ユーザーインデックス
CREATE INDEX idx_user_person ON USER_ACCOUNT(person_id);

-- プロジェクト開始イベントインデックス
CREATE INDEX idx_project_start_project ON PROJECT_START(project_id);
CREATE INDEX idx_project_start_datetime ON PROJECT_START(start_date_time);

-- 組織参画イベントインデックス
CREATE INDEX idx_organization_join_project ON ORGANIZATION_JOIN(project_id);
CREATE INDEX idx_organization_join_org ON ORGANIZATION_JOIN(organization_id);
CREATE INDEX idx_organization_join_datetime ON ORGANIZATION_JOIN(join_date_time);

-- 担当者アサインイベントインデックス
CREATE INDEX idx_person_assign_project ON PERSON_ASSIGN(project_id);
CREATE INDEX idx_person_assign_person ON PERSON_ASSIGN(person_id);
CREATE INDEX idx_person_assign_datetime ON PERSON_ASSIGN(assign_date_time);

-- 担当者交代イベントインデックス
CREATE INDEX idx_person_replace_project ON PERSON_REPLACE(project_id);
CREATE INDEX idx_person_replace_old ON PERSON_REPLACE(old_person_id);
CREATE INDEX idx_person_replace_new ON PERSON_REPLACE(new_person_id);
CREATE INDEX idx_person_replace_datetime ON PERSON_REPLACE(replace_date_time);

-- リスク評価イベントインデックス
CREATE INDEX idx_risk_evaluate_project ON RISK_EVALUATE(project_id);
CREATE INDEX idx_risk_evaluate_datetime ON RISK_EVALUATE(evaluate_date_time);

-- 支援実施イベントインデックス
CREATE INDEX idx_support_execute_project ON SUPPORT_EXECUTE(project_id);
CREATE INDEX idx_support_execute_type ON SUPPORT_EXECUTE(support_type_id);
CREATE INDEX idx_support_execute_person ON SUPPORT_EXECUTE(support_person_id);
CREATE INDEX idx_support_execute_datetime ON SUPPORT_EXECUTE(execute_date_time);

-- プロジェクト完了イベントインデックス
CREATE INDEX idx_project_complete_project ON PROJECT_COMPLETE(project_id);
CREATE INDEX idx_project_complete_datetime ON PROJECT_COMPLETE(complete_date_time);
