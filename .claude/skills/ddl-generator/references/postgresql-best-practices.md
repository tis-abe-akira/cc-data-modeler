# PostgreSQL DDL生成のベストプラクティス

## テーブル命名規則

- リソーステーブル: 単数形の大文字スネークケース（例: `PROJECT`, `CUSTOMER`）
- イベントテーブル: アクション_対象形式（例: `PROJECT_START`, `INVOICE_SEND`）
- ジャンクションテーブル: エンティティ1_エンティティ2形式（例: `PROJECT_DEVELOPMENT_TYPE`）

## カラム命名規則

**重要: カラム名はすべて小文字のsnake_caseを使用**

- 主キー: `{テーブル名}_id`（例: `project_id`, `customer_id`）
- 外部キー: 参照先の主キー名と同じ（例: `customer_id`）
- 一般カラム: 小文字snake_case（例: `project_name`, `created_at`）

### CamelCase → snake_case 変換ルール

| モデル定義（CamelCase） | DDLカラム名（snake_case） |
|------------------------|--------------------------|
| ProjectID | project_id |
| ProjectName | project_name |
| CustomerID | customer_id |
| CreatedAt | created_at |
| StartDateTime | start_date_time |
| ParentOrganizationID | parent_organization_id |

## 主キー

すべてのテーブルに主キーを設定：

### リソース・イベントテーブル
```sql
resource_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

### ジャンクションテーブル
```sql
PRIMARY KEY (project_id, development_type_id)
```

## 外部キー制約

必ず外部キー制約を設定：

```sql
CONSTRAINT fk_project_customer FOREIGN KEY (customer_id)
    REFERENCES CUSTOMER(customer_id) ON DELETE RESTRICT
```

- 命名: `fk_{テーブル名}_{参照先または列名}`（小文字）
- 削除時動作: `ON DELETE RESTRICT`（デフォルト、データ整合性を保護）

## データ型

### 推奨マッピング
- `INT` → `INTEGER`
- `VARCHAR(N)` → `VARCHAR(N)`
- `DECIMAL(M,N)` → `DECIMAL(M,N)` または `NUMERIC(M,N)`
- `DATE` → `DATE`
- `TIMESTAMP` → `TIMESTAMP WITH TIME ZONE`
- `TEXT` → `TEXT`
- `BOOLEAN` → `BOOLEAN`

### 日時型
イベントの日時属性は必ず `TIMESTAMP WITH TIME ZONE` を使用：

```sql
event_date_time TIMESTAMP WITH TIME ZONE NOT NULL
```

### デフォルト値
作成日時には現在時刻をデフォルト設定：

```sql
created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
```

## コメント

すべてのテーブル・カラムに日本語コメントを付与：

```sql
COMMENT ON TABLE PROJECT IS 'プロジェクト';
COMMENT ON COLUMN PROJECT.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT.project_name IS 'プロジェクト名';
```

## インデックス

パフォーマンス最適化のためのインデックス作成：

### 必須インデックス
1. 外部キー列
2. 日時列（イベントテーブル）
3. よく検索される列

### 命名規則
```sql
idx_{テーブル名}_{列名}
```

### 例
```sql
CREATE INDEX idx_project_customer ON PROJECT(customer_id);
CREATE INDEX idx_project_start_datetime ON PROJECT_START(start_date_time);
```

## DDL構造

### ファイル構成
1. ヘッダーコメント
2. リソーステーブル
3. ジャンクションテーブル
4. イベントテーブル
5. インデックス

### セクション分け
```sql
-- ================================================
-- リソーステーブル
-- ================================================

-- ================================================
-- ジャンクションテーブル（多対多関係）
-- ================================================

-- ================================================
-- イベントテーブル
-- ================================================

-- ================================================
-- インデックス（パフォーマンス最適化）
-- ================================================
```

## 特殊ケース

### 予約語との衝突
PostgreSQLの予約語（USER等）は別名を使用：

```sql
-- ❌ USER
-- ✅ USER_ACCOUNT
```

### 自己参照
自己参照の外部キーは後から追加可能：

```sql
CREATE TABLE ORGANIZATION (
    organization_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_organization_id INTEGER,
    -- 他の列...
);

-- 外部キー制約を後から追加
ALTER TABLE ORGANIZATION ADD CONSTRAINT fk_organization_parent
    FOREIGN KEY (parent_organization_id)
    REFERENCES ORGANIZATION(organization_id) ON DELETE RESTRICT;
```

## 完全な例

```sql
-- ================================================
-- リソーステーブル
-- ================================================

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

-- ================================================
-- イベントテーブル
-- ================================================

CREATE TABLE PROJECT_START (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id INTEGER NOT NULL,
    start_date_time TIMESTAMP WITH TIME ZONE NOT NULL,
    registered_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_project_start_project FOREIGN KEY (project_id)
        REFERENCES PROJECT(project_id) ON DELETE RESTRICT
);

COMMENT ON TABLE PROJECT_START IS 'プロジェクト開始';
COMMENT ON COLUMN PROJECT_START.event_id IS 'イベントID';
COMMENT ON COLUMN PROJECT_START.project_id IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT_START.start_date_time IS '開始日時';
COMMENT ON COLUMN PROJECT_START.registered_by IS '登録者';
COMMENT ON COLUMN PROJECT_START.created_at IS '作成日時';

-- ================================================
-- インデックス
-- ================================================

CREATE INDEX idx_project_customer ON PROJECT(customer_id);
CREATE INDEX idx_project_start_project ON PROJECT_START(project_id);
CREATE INDEX idx_project_start_datetime ON PROJECT_START(start_date_time);
```
