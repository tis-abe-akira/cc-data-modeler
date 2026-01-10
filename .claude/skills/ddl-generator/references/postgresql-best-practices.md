# PostgreSQL DDL生成のベストプラクティス

## テーブル命名規則

- リソーステーブル: 単数形の大文字スネークケース（例: `PROJECT`, `CUSTOMER`）
- イベントテーブル: アクション_対象形式（例: `PROJECT_START`, `INVOICE_SEND`）
- ジャンクションテーブル: エンティティ1_エンティティ2形式（例: `PROJECT_DEVELOPMENT_TYPE`）

## 主キー

すべてのテーブルに主キーを設定：

### リソース・イベントテーブル
```sql
ResourceID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
EventID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

### ジャンクションテーブル
```sql
PRIMARY KEY (ProjectID, DevelopmentTypeID)
```

## 外部キー制約

必ず外部キー制約を設定：

```sql
CONSTRAINT FK_PROJECT_CUSTOMER FOREIGN KEY (CustomerID)
    REFERENCES CUSTOMER(CustomerID) ON DELETE RESTRICT
```

- 命名: `FK_{テーブル名}_{参照先または列名}`
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
EventDateTime TIMESTAMP WITH TIME ZONE NOT NULL
```

### デフォルト値
作成日時には現在時刻をデフォルト設定：

```sql
CreatedAt TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
```

## コメント

すべてのテーブル・カラムに日本語コメントを付与：

```sql
COMMENT ON TABLE PROJECT IS 'プロジェクト';
COMMENT ON COLUMN PROJECT.ProjectID IS 'プロジェクトID';
COMMENT ON COLUMN PROJECT.ProjectName IS 'プロジェクト名';
```

## インデックス

パフォーマンス最適化のためのインデックス作成：

### 必須インデックス
1. 外部キー列
2. 日時列（イベントテーブル）
3. よく検索される列

### 命名規則
```sql
IDX_{テーブル名}_{列名}
```

### 例
```sql
CREATE INDEX IDX_PROJECT_CUSTOMER ON PROJECT(CustomerID);
CREATE INDEX IDX_PROJECT_START_DATETIME ON PROJECT_START(StartDateTime);
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
    OrganizationID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ParentOrganizationID INTEGER,
    -- 他の列...
);

-- 外部キー制約を後から追加
ALTER TABLE ORGANIZATION ADD CONSTRAINT FK_ORGANIZATION_PARENT
    FOREIGN KEY (ParentOrganizationID)
    REFERENCES ORGANIZATION(OrganizationID) ON DELETE RESTRICT;
```
