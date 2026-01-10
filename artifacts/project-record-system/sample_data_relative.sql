-- ================================================
-- サンプルデータINSERT（相対日付版）
-- プロジェクト記録システムのデモ用データ
-- いつ実行しても意図したシナリオが再現されます
-- ================================================

-- ================================================
-- リソースデータ投入
-- ================================================

-- 業界データ
INSERT INTO INDUSTRY (IndustryName, CreatedAt) VALUES
('製造業', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('金融業', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('情報通信業', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 顧客データ
INSERT INTO CUSTOMER (CustomerName, IndustryID, CreatedAt) VALUES
('株式会社テックソリューション', 3, CURRENT_TIMESTAMP - INTERVAL '350 days'),
('金融太郎銀行', 2, CURRENT_TIMESTAMP - INTERVAL '345 days'),
('製造花子工業株式会社', 1, CURRENT_TIMESTAMP - INTERVAL '340 days');

-- 人データ（社員・担当者）
INSERT INTO PERSON (Name, Email, CreatedAt) VALUES
('山田太郎', 'yamada@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('鈴木花子', 'suzuki@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('佐藤次郎', 'sato@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('田中美咲', 'tanaka@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('高橋健一', 'takahashi@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days'),
('伊藤真理', 'ito@example.com', CURRENT_TIMESTAMP - INTERVAL '360 days');

-- 組織データ（階層構造）
INSERT INTO ORGANIZATION (OrganizationName, OrganizationType, ParentOrganizationID, CreatedAt) VALUES
('開発本部', '本部', NULL, CURRENT_TIMESTAMP - INTERVAL '365 days'),
('第一開発部', '部', 1, CURRENT_TIMESTAMP - INTERVAL '365 days'),
('第二開発部', '部', 1, CURRENT_TIMESTAMP - INTERVAL '365 days'),
('品質保証部', '部', 1, CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 役割データ
INSERT INTO ROLE (RoleName, CreatedAt) VALUES
('プロジェクトマネージャー', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('リードエンジニア', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('エンジニア', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('QAエンジニア', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 開発種別データ（タグ）
INSERT INTO DEVELOPMENT_TYPE (DevelopmentTypeName, Description, CreatedAt) VALUES
('新規開発', '新しいシステムをゼロから開発', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('保守開発', '既存システムの改修・保守', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('機能追加', '既存システムへの機能追加', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 開発方式データ（タグ）
INSERT INTO DEVELOPMENT_METHOD (DevelopmentMethodName, Description, CreatedAt) VALUES
('アジャイル', 'スプリント方式での反復開発', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('ウォーターフォール', '段階的な計画駆動開発', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('ハイブリッド', 'アジャイルとウォーターフォールの組み合わせ', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 対象工程データ（タグ）
INSERT INTO TARGET_PHASE (TargetPhaseName, Description, CreatedAt) VALUES
('要件定義', 'システム要件の定義', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('基本設計', 'システムの基本設計', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('詳細設計', '詳細な実装設計', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('実装', 'コーディング', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('テスト', 'システムテスト', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- 支援タイプデータ
INSERT INTO SUPPORT_TYPE (SupportTypeName, Description, CreatedAt) VALUES
('技術支援', '技術的な問題解決をサポート', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('プロセス改善', 'プロジェクト運営プロセスの改善提案', CURRENT_TIMESTAMP - INTERVAL '365 days'),
('リスク対策', 'リスクの予防と対策', CURRENT_TIMESTAMP - INTERVAL '365 days');

-- ユーザーアカウントデータ
INSERT INTO USER_ACCOUNT (PersonID, Username, CreatedAt) VALUES
(1, 'yamada_t', CURRENT_TIMESTAMP - INTERVAL '355 days'),
(2, 'suzuki_h', CURRENT_TIMESTAMP - INTERVAL '355 days'),
(3, 'sato_j', CURRENT_TIMESTAMP - INTERVAL '355 days');

-- プロジェクトデータ
INSERT INTO PROJECT (ProjectName, CustomerID, EstimatedEffort, PlannedStartDate, PlannedEndDate, CreatedAt) VALUES
-- プロジェクト1: 6ヶ月前開始予定、すでに完了
('次世代ECサイト構築', 1, 500.00, CURRENT_DATE - INTERVAL '180 days', CURRENT_DATE - INTERVAL '30 days', CURRENT_TIMESTAMP - INTERVAL '210 days'),
-- プロジェクト2: 5ヶ月前開始予定、長期プロジェクト（進行中）
('勘定系システムリプレース', 2, 1200.00, CURRENT_DATE - INTERVAL '150 days', CURRENT_DATE + INTERVAL '180 days', CURRENT_TIMESTAMP - INTERVAL '180 days'),
-- プロジェクト3: 1ヶ月前開始予定、短期プロジェクト（開始直後）
('生産管理システム改修', 3, 300.00, CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '150 days', CURRENT_TIMESTAMP - INTERVAL '60 days');

-- プロジェクトと開発種別の紐付け（タグ方式）
INSERT INTO PROJECT_DEVELOPMENT_TYPE (ProjectID, DevelopmentTypeID) VALUES
(1, 1), -- 次世代ECサイト: 新規開発
(2, 1), -- 勘定系リプレース: 新規開発
(3, 2), -- 生産管理: 保守開発
(3, 3); -- 生産管理: 機能追加

-- プロジェクトと開発方式の紐付け（タグ方式）
INSERT INTO PROJECT_DEVELOPMENT_METHOD (ProjectID, DevelopmentMethodID) VALUES
(1, 1), -- 次世代ECサイト: アジャイル
(2, 3), -- 勘定系リプレース: ハイブリッド
(3, 2); -- 生産管理: ウォーターフォール

-- プロジェクトと対象工程の紐付け（タグ方式）
INSERT INTO PROJECT_TARGET_PHASE (ProjectID, TargetPhaseID) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), -- 次世代ECサイト: 全工程
(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), -- 勘定系リプレース: 全工程
(3, 3), (3, 4), (3, 5); -- 生産管理: 詳細設計〜テスト

-- ================================================
-- イベントデータ投入（時系列で発生したイベント）
-- ================================================

-- ========================================
-- シナリオ1: プロジェクト1（次世代ECサイト）
-- 順調に進行し、完了したプロジェクト
-- 6ヶ月前開始 → 1ヶ月前完了
-- ========================================

-- プロジェクト開始（180日前）
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(1, CURRENT_TIMESTAMP - INTERVAL '180 days', 1);

-- 組織参画（180日前）
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(1, 2, CURRENT_TIMESTAMP - INTERVAL '180 days', 1); -- 第一開発部

-- 担当者アサイン（180日前）
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(1, 1, 1, CURRENT_TIMESTAMP - INTERVAL '180 days' + INTERVAL '1 hour', 1), -- 山田太郎: PM
(1, 2, 2, CURRENT_TIMESTAMP - INTERVAL '180 days' + INTERVAL '1 hour', 1), -- 鈴木花子: リードエンジニア
(1, 3, 3, CURRENT_TIMESTAMP - INTERVAL '180 days' + INTERVAL '1 hour', 1); -- 佐藤次郎: エンジニア

-- リスク評価（低リスク、150日前）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(1, '低', CURRENT_TIMESTAMP - INTERVAL '150 days', 1, TRUE, FALSE);

-- 支援実施（技術支援、120日前）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(1, 1, 6, CURRENT_TIMESTAMP - INTERVAL '120 days', 'React最新バージョン移行サポート', 'React 18へのスムーズな移行完了', 'パフォーマンス改善を確認');

-- プロジェクト完了（35日前）
INSERT INTO PROJECT_COMPLETE (ProjectID, CompleteDateTime, ActualEffort, RegisteredBy) VALUES
(1, CURRENT_TIMESTAMP - INTERVAL '35 days', 480.00, 1);

-- ========================================
-- シナリオ2: プロジェクト2（勘定系リプレース）
-- 途中で担当者交代・リスク上昇があるプロジェクト
-- 5ヶ月前開始 → 現在進行中
-- ========================================

-- プロジェクト開始（150日前）
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(2, CURRENT_TIMESTAMP - INTERVAL '150 days', 2);

-- 組織参画（150日前）
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(2, 2, CURRENT_TIMESTAMP - INTERVAL '150 days', 2), -- 第一開発部
(2, 4, CURRENT_TIMESTAMP - INTERVAL '150 days', 2); -- 品質保証部

-- 担当者アサイン（150日前）
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(2, 2, 1, CURRENT_TIMESTAMP - INTERVAL '150 days' + INTERVAL '1 hour', 2), -- 鈴木花子: PM
(2, 4, 2, CURRENT_TIMESTAMP - INTERVAL '150 days' + INTERVAL '1 hour', 2), -- 田中美咲: リードエンジニア
(2, 5, 3, CURRENT_TIMESTAMP - INTERVAL '150 days' + INTERVAL '1 hour', 2); -- 高橋健一: エンジニア

-- リスク評価（初回：中リスク、120日前）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '中', CURRENT_TIMESTAMP - INTERVAL '120 days', 2, TRUE, FALSE);

-- 担当者交代（高橋 → 佐藤、80日前）
INSERT INTO PERSON_REPLACE (ProjectID, OldPersonID, NewPersonID, RoleID, ReplaceDateTime, RegisteredBy) VALUES
(2, 5, 3, 3, CURRENT_TIMESTAMP - INTERVAL '80 days', 2);

-- リスク評価（交代後：高リスク、60日前）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '高', CURRENT_TIMESTAMP - INTERVAL '60 days', 2, TRUE, FALSE);

-- 支援実施（リスク対策、45日前）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(2, 3, 6, CURRENT_TIMESTAMP - INTERVAL '45 days', '進捗遅延の原因分析と対策提案', 'リソース追加と作業分担見直し実施', 'プロジェクト計画を再調整');

-- リスク評価（対策後：中リスク、30日前）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '中', CURRENT_TIMESTAMP - INTERVAL '30 days', 2, FALSE, TRUE);

-- 支援実施（プロセス改善、15日前）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(2, 2, 6, CURRENT_TIMESTAMP - INTERVAL '15 days', 'コミュニケーション改善とレビュー強化', 'チーム連携が改善し品質向上', '定例ミーティング頻度を増加');

-- ========================================
-- シナリオ3: プロジェクト3（生産管理システム改修）
-- 開始直後でこれから進行するプロジェクト
-- 1ヶ月前開始 → 現在開始直後
-- ========================================

-- プロジェクト開始（30日前）
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(3, CURRENT_TIMESTAMP - INTERVAL '30 days', 3);

-- 組織参画（30日前）
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(3, 3, CURRENT_TIMESTAMP - INTERVAL '30 days', 3); -- 第二開発部

-- 担当者アサイン（30日前）
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(3, 3, 1, CURRENT_TIMESTAMP - INTERVAL '30 days' + INTERVAL '1 hour', 3), -- 佐藤次郎: PM
(3, 4, 3, CURRENT_TIMESTAMP - INTERVAL '30 days' + INTERVAL '1 hour', 3), -- 田中美咲: エンジニア
(3, 5, 4, CURRENT_TIMESTAMP - INTERVAL '30 days' + INTERVAL '1 hour', 3); -- 高橋健一: QAエンジニア

-- リスク評価（初回：低リスク、10日前）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(3, '低', CURRENT_TIMESTAMP - INTERVAL '10 days', 3, TRUE, FALSE);

-- ================================================
-- データサマリー
-- ================================================
-- リソース:
--   業界: 3件
--   顧客: 3社
--   人: 6人
--   組織: 4組織（階層構造）
--   役割: 4種類
--   開発種別: 3種類
--   開発方式: 3種類
--   対象工程: 5種類
--   支援タイプ: 3種類
--   プロジェクト: 3件
--
-- イベント:
--   プロジェクト開始: 3件
--   組織参画: 4件
--   担当者アサイン: 8件
--   担当者交代: 1件
--   リスク評価: 5件
--   支援実施: 4件
--   プロジェクト完了: 1件
--
-- 状態パターン:
--   ✅ 完了プロジェクト: プロジェクト1（6ヶ月前開始、1ヶ月前完了）
--   ⚠️ 進行中（課題あり）: プロジェクト2（5ヶ月前開始、現在進行中、リスク変動あり）
--   🆕 開始直後: プロジェクト3（1ヶ月前開始、低リスクで順調）
-- ================================================
