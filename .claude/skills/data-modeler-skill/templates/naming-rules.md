# 命名規則（Naming Rules）

データモデリングにおける命名規則を定義します。

## 基本方針

- 英語名を使用（国際化対応）
- 意味が明確な名前を付ける
- 略語は極力避ける（一般的なものを除く）
- 一貫性を保つ

## エンティティ名（論理モデル）

### 形式

- **英語**: PascalCase（単数形）
- **日本語**: 漢字・ひらがな（単数形）

### ルール

1. 単数形を使用
   - ✅ `Customer`（顧客）
   - ❌ `Customers`（顧客たち）

2. 明確で具体的な名前
   - ✅ `InvoiceSend`（請求書送付）
   - ❌ `Event1`（イベント1）

3. 省略形を避ける
   - ✅ `Customer`（顧客）
   - ❌ `Cust`（顧客）

### リソースエンティティの例

- `Customer` - 顧客
- `Product` - 商品
- `Employee` - 社員
- `Department` - 部署
- `Contract` - 契約
- `Project` - プロジェクト
- `Account` - 口座

### イベントエンティティの例

動詞 + 名詞の形式を推奨

- `OrderPlace` - 注文
- `PaymentMake` - 入金
- `InvoiceSend` - 請求書送付
- `ShipmentExecute` - 出荷
- `EmployeeTransfer` - 社員異動
- `ProductRegister` - 商品登録
- `ContractSign` - 契約締結

### 交差エンティティの例

関連する2つのエンティティを結合、または独自の名前

- `Enrollment` - 履修（Student + Course）
- `OrderDetail` - 注文明細（Order + Product）
- `Assignment` - 配属（Employee + Department）
- `Membership` - 会員資格（User + Group）

## テーブル名（DDL/RDBMS実装時）

### 形式

- **大文字スネークケース（UPPER_SNAKE_CASE）**

### 例

```
CUSTOMER
INVOICE_SEND
ORDER_DETAIL
PAYMENT_MAKE
PROJECT_START
PERSON_ASSIGN
```

## カラム名（DDL/RDBMS実装時）

### 重要: 小文字snake_caseを使用

DDL生成時、カラム名は**必ず小文字のsnake_case**を使用すること。

| 論理モデル（PascalCase） | DDLカラム名（snake_case） |
|------------------------|--------------------------|
| CustomerID | customer_id |
| ProjectName | project_name |
| CreatedAt | created_at |
| StartDateTime | start_date_time |
| ParentOrganizationID | parent_organization_id |

### 主キー

**形式**: `{テーブル名}_id`（小文字snake_case）

**例:**
```sql
customer_id
invoice_id
event_id
project_id
```

### 外部キー

**形式**: 参照先のテーブルの主キー名をそのまま使用

**例:**
```sql
-- CUSTOMERテーブル
customer_id (PK)

-- INVOICE_SENDテーブル
event_id (PK)
customer_id (FK) ← 参照先の主キー名と同じ
```

### 日時属性

**形式**: `{意味}_date_time` または `{意味}_at`

**イベントの場合（必須）:**
```sql
send_date_time     -- 送付日時
payment_date_time  -- 入金日時
order_date_time    -- 注文日時
start_date_time    -- 開始日時
```

**リソースの場合（システム用途）:**
```sql
created_at   -- 作成日時
updated_at   -- 更新日時（※ビジネスイベントは別途定義すべき）
```

### 金額・数量

**金額:**
```sql
amount        -- 金額
total_amount  -- 合計金額
unit_price    -- 単価
```

**数量:**
```sql
quantity  -- 数量
count     -- 個数
```

### フラグ・ステータス

**フラグ（真偽値）:**
```sql
is_active     -- アクティブか
is_deleted    -- 削除済みか（※イベントモデルでは非推奨）
has_discount  -- 割引があるか
```

**ステータス（列挙型）:**
```sql
status          -- ステータス
order_status    -- 注文ステータス
payment_status  -- 支払いステータス
```

## よくある属性名の例

### 個人情報

```sql
name / full_name  -- 氏名
first_name        -- 名
last_name         -- 姓
email             -- メールアドレス
phone / phone_number  -- 電話番号
address           -- 住所
postal_code / zip_code  -- 郵便番号
birth_date        -- 生年月日
```

### 組織・場所

```sql
company_name      -- 会社名
department_name   -- 部署名
office_name       -- 事業所名
location          -- 所在地
```

### 金銭・数値

```sql
price       -- 価格
cost        -- 原価
amount      -- 金額
quantity    -- 数量
rate        -- 率（例: 税率、割引率）
percentage  -- パーセンテージ
```

### 日時

```sql
date              -- 日付
date_time         -- 日時
time              -- 時刻
start_date / start_date_time  -- 開始日時
end_date / end_date_time      -- 終了日時
created_at        -- 作成日時
updated_at        -- 更新日時
```

### コード・ID

```sql
code           -- コード
number         -- 番号（例: 注文番号、請求書番号）
employee_code  -- 社員コード
product_code   -- 商品コード
```

## 禁止事項

### ❌ 避けるべき命名

1. **CamelCaseのカラム名（DDL生成時）**
   - ❌ `CustomerID`, `ProjectName`, `CreatedAt`
   - ✅ `customer_id`, `project_name`, `created_at`

2. **意味不明な略語**
   - `cust`, `prod`, `emp` など
   - 例外: 業界標準の略語（`url`, `id`等）

3. **数値での区別**
   - `Product1`, `Product2`
   - `Event1`, `Event2`

4. **型の接頭辞**
   - `tbl_customer` (テーブルを表す接頭辞)
   - `int_customer_id` (型を表す接頭辞)

5. **予約語**
   - SQL予約語（`order`, `user`, `group`等）は避けるか、エスケープする

6. **複数形**
   - ❌ `Customers`
   - ✅ `Customer`

## DDL生成時のデフォルト設定

```yaml
# テーブル名
table_naming_style: "UPPER_SNAKE_CASE"  # → CUSTOMER, PROJECT_START

# カラム名（重要: 必ずsnake_case）
column_naming_style: "snake_case"  # → customer_id, project_name

# 主キーの命名
primary_key_suffix: "_id"  # → customer_id, project_id

# 外部キーの命名
foreign_key_suffix: "_id"  # → customer_id

# 日時カラムの命名
datetime_suffix: "_at" または "_date_time"  # → created_at, start_date_time

# 制約の命名
constraint_style: "snake_case"  # → fk_project_customer, idx_project_customer
```

## チェックリスト

命名時に以下を確認：

- [ ] エンティティ名は単数形
- [ ] 論理モデルの英語名がPascalCase
- [ ] **DDLカラム名が小文字snake_case**
- [ ] 主キーは`{テーブル名}_id`形式
- [ ] 外部キーは参照先の主キー名と一致
- [ ] イベントの日時属性が明確
- [ ] 予約語を避けている
- [ ] プロジェクト内で一貫性がある
- [ ] 意味が明確で理解しやすい

## 参考資料

- ISO/IEC 11179 - データ要素の命名規則
- SQL標準仕様
- 各言語のコーディング規約（Java, C#, Python等）
