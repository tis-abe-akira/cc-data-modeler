# 命名規則（Naming Rules）

データモデリングにおける命名規則を定義します。

## 基本方針

- 英語名を使用（国際化対応）
- 意味が明確な名前を付ける
- 略語は極力避ける（一般的なものを除く）
- 一貫性を保つ

## エンティティ名

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

## テーブル名（RDBMS実装時）

### 形式

- 大文字スネークケース（UPPER_SNAKE_CASE）
- または小文字スネークケース（lower_snake_case）

プロジェクトで統一すること。

### 例

**大文字スネークケース:**
```
CUSTOMER
INVOICE_SEND
ORDER_DETAIL
PAYMENT_MAKE
```

**小文字スネークケース:**
```
customer
invoice_send
order_detail
payment_make
```

## カラム名（属性名）

### 形式

- **英語**: PascalCaseまたはsnake_case
- プロジェクトで統一

### 主キー

**形式**: `{エンティティ名}ID` または `{エンティティ名}_id`

**例:**
```
CustomerID または customer_id
InvoiceID または invoice_id
EventID または event_id
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

**推奨形式**: `{イベント名}DateTime` または `{イベント名}_datetime`

**イベントの場合（必須）:**
```
SendDateTime - 送付日時
PaymentDateTime - 入金日時
OrderDateTime - 注文日時
```

**リソースの場合（システム用途）:**
```
CreatedAt - 作成日時
UpdatedAt - 更新日時（※ビジネスイベントは別途定義すべき）
```

### 金額・数量

**金額:**
```
Amount - 金額
TotalAmount - 合計金額
UnitPrice - 単価
```

**数量:**
```
Quantity - 数量
Count - 個数
```

### フラグ・ステータス

**フラグ（真偽値）:**
```
IsActive - アクティブか
IsDeleted - 削除済みか（※イベントモデルでは非推奨）
HasDiscount - 割引があるか
```

**ステータス（列挙型）:**
```
Status - ステータス
OrderStatus - 注文ステータス
PaymentStatus - 支払いステータス
```

## よくある属性名の例

### 個人情報

```
Name / FullName - 氏名
FirstName - 名
LastName - 姓
Email - メールアドレス
Phone / PhoneNumber - 電話番号
Address - 住所
PostalCode / ZipCode - 郵便番号
BirthDate - 生年月日
```

### 組織・場所

```
CompanyName - 会社名
DepartmentName - 部署名
OfficeName - 事業所名
Location - 所在地
```

### 金銭・数値

```
Price - 価格
Cost - 原価
Amount - 金額
Quantity - 数量
Rate - 率（例: 税率、割引率）
Percentage - パーセンテージ
```

### 日時

```
Date - 日付
DateTime - 日時
Time - 時刻
StartDate / StartDateTime - 開始日時
EndDate / EndDateTime - 終了日時
CreatedAt - 作成日時
UpdatedAt - 更新日時
```

### コード・ID

```
Code - コード
Number - 番号（例: 注文番号、請求書番号）
ID - 識別子
EmployeeCode - 社員コード
ProductCode - 商品コード
```

## 禁止事項

### ❌ 避けるべき命名

1. **意味不明な略語**
   - `cust`, `prod`, `emp` など
   - 例外: 業界標準の略語（`URL`, `ID`等）

2. **数値での区別**
   - `Product1`, `Product2`
   - `Event1`, `Event2`

3. **型の接頭辞**
   - `tbl_customer` (テーブルを表す接頭辞)
   - `int_customer_id` (型を表す接頭辞)

4. **予約語**
   - SQL予約語（`order`, `user`, `group`等）は避けるか、エスケープする

5. **複数形**
   - ❌ `Customers`
   - ✅ `Customer`

## プロジェクト固有のカスタマイズ

この部分は、各プロジェクトの要件に応じてカスタマイズしてください。

### テーブル接頭辞（必要な場合）

```yaml
# 例: マイクロサービスで複数のスキーマを持つ場合
service_prefix: "ord_"  # 注文サービス
# → ord_customer, ord_invoice_send
```

### カラムの命名規則

```yaml
# PascalCase または snake_case を選択
column_naming_style: "snake_case"

# 主キーの命名
primary_key_suffix: "_id"  # → customer_id

# 外部キーの命名
foreign_key_suffix: "_id"  # → customer_id

# 日時カラムの命名
datetime_suffix: "_at"  # → created_at, updated_at
# または
datetime_suffix: "_datetime"  # → send_datetime
```

### 業界特有の用語

プロジェクトで使用する業界特有の用語を定義

```yaml
# 例: 医療システム
domain_terms:
  - Patient: 患者
  - Doctor: 医師
  - Diagnosis: 診断
  - Prescription: 処方

# 例: ECシステム
domain_terms:
  - Cart: カート
  - Checkout: チェックアウト
  - Wishlist: ウィッシュリスト
```

## チェックリスト

命名時に以下を確認：

- [ ] エンティティ名は単数形
- [ ] 英語名がPascalCase
- [ ] 主キーは`{エンティティ名}ID`形式
- [ ] 外部キーは参照先の主キー名と一致
- [ ] イベントの日時属性が明確
- [ ] 予約語を避けている
- [ ] プロジェクト内で一貫性がある
- [ ] 意味が明確で理解しやすい

## 参考資料

- ISO/IEC 11179 - データ要素の命名規則
- SQL標準仕様
- 各言語のコーディング規約（Java, C#, Python等）
