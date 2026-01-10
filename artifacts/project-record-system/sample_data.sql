-- ================================================
-- サンプルデータINSERT
-- プロジェクト記録システムのデモ用データ
-- ================================================

-- ================================================
-- リソースデータ投入
-- ================================================

-- 業界データ
INSERT INTO INDUSTRY (IndustryName, CreatedAt) VALUES
('製造業', '2024-01-01 09:00:00+09'),
('金融業', '2024-01-01 09:00:00+09'),
('情報通信業', '2024-01-01 09:00:00+09');

-- 顧客データ
INSERT INTO CUSTOMER (CustomerName, IndustryID, CreatedAt) VALUES
('株式会社テックソリューション', 3, '2024-01-10 10:00:00+09'),
('金融太郎銀行', 2, '2024-01-15 11:00:00+09'),
('製造花子工業株式会社', 1, '2024-01-20 14:00:00+09');

-- 人データ（社員・担当者）
INSERT INTO PERSON (Name, Email, CreatedAt) VALUES
('山田太郎', 'yamada@example.com', '2024-01-05 09:00:00+09'),
('鈴木花子', 'suzuki@example.com', '2024-01-05 09:00:00+09'),
('佐藤次郎', 'sato@example.com', '2024-01-05 09:00:00+09'),
('田中美咲', 'tanaka@example.com', '2024-01-05 09:00:00+09'),
('高橋健一', 'takahashi@example.com', '2024-01-05 09:00:00+09'),
('伊藤真理', 'ito@example.com', '2024-01-05 09:00:00+09');

-- 組織データ（階層構造）
INSERT INTO ORGANIZATION (OrganizationName, OrganizationType, ParentOrganizationID, CreatedAt) VALUES
('開発本部', '本部', NULL, '2024-01-01 09:00:00+09'),
('第一開発部', '部', 1, '2024-01-01 09:00:00+09'),
('第二開発部', '部', 1, '2024-01-01 09:00:00+09'),
('品質保証部', '部', 1, '2024-01-01 09:00:00+09');

-- 役割データ
INSERT INTO ROLE (RoleName, CreatedAt) VALUES
('プロジェクトマネージャー', '2024-01-01 09:00:00+09'),
('リードエンジニア', '2024-01-01 09:00:00+09'),
('エンジニア', '2024-01-01 09:00:00+09'),
('QAエンジニア', '2024-01-01 09:00:00+09');

-- 開発種別データ（タグ）
INSERT INTO DEVELOPMENT_TYPE (DevelopmentTypeName, Description, CreatedAt) VALUES
('新規開発', '新しいシステムをゼロから開発', '2024-01-01 09:00:00+09'),
('保守開発', '既存システムの改修・保守', '2024-01-01 09:00:00+09'),
('機能追加', '既存システムへの機能追加', '2024-01-01 09:00:00+09');

-- 開発方式データ（タグ）
INSERT INTO DEVELOPMENT_METHOD (DevelopmentMethodName, Description, CreatedAt) VALUES
('アジャイル', 'スプリント方式での反復開発', '2024-01-01 09:00:00+09'),
('ウォーターフォール', '段階的な計画駆動開発', '2024-01-01 09:00:00+09'),
('ハイブリッド', 'アジャイルとウォーターフォールの組み合わせ', '2024-01-01 09:00:00+09');

-- 対象工程データ（タグ）
INSERT INTO TARGET_PHASE (TargetPhaseName, Description, CreatedAt) VALUES
('要件定義', 'システム要件の定義', '2024-01-01 09:00:00+09'),
('基本設計', 'システムの基本設計', '2024-01-01 09:00:00+09'),
('詳細設計', '詳細な実装設計', '2024-01-01 09:00:00+09'),
('実装', 'コーディング', '2024-01-01 09:00:00+09'),
('テスト', 'システムテスト', '2024-01-01 09:00:00+09');

-- 支援タイプデータ
INSERT INTO SUPPORT_TYPE (SupportTypeName, Description, CreatedAt) VALUES
('技術支援', '技術的な問題解決をサポート', '2024-01-01 09:00:00+09'),
('プロセス改善', 'プロジェクト運営プロセスの改善提案', '2024-01-01 09:00:00+09'),
('リスク対策', 'リスクの予防と対策', '2024-01-01 09:00:00+09');

-- ユーザーアカウントデータ
INSERT INTO USER_ACCOUNT (PersonID, Username, CreatedAt) VALUES
(1, 'yamada_t', '2024-01-05 10:00:00+09'),
(2, 'suzuki_h', '2024-01-05 10:00:00+09'),
(3, 'sato_j', '2024-01-05 10:00:00+09');

-- プロジェクトデータ
INSERT INTO PROJECT (ProjectName, CustomerID, EstimatedEffort, PlannedStartDate, PlannedEndDate, CreatedAt) VALUES
('次世代ECサイト構築', 1, 500.00, '2024-04-01', '2024-09-30', '2024-03-01 10:00:00+09'),
('勘定系システムリプレース', 2, 1200.00, '2024-05-01', '2025-03-31', '2024-04-01 09:00:00+09'),
('生産管理システム改修', 3, 300.00, '2024-06-01', '2024-11-30', '2024-05-10 14:00:00+09');

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
-- ========================================

-- プロジェクト開始
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(1, '2024-04-01 10:00:00+09', 1);

-- 組織参画
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(1, 2, '2024-04-01 10:00:00+09', 1); -- 第一開発部

-- 担当者アサイン
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(1, 1, 1, '2024-04-01 11:00:00+09', 1), -- 山田太郎: PM
(1, 2, 2, '2024-04-01 11:00:00+09', 1), -- 鈴木花子: リードエンジニア
(1, 3, 3, '2024-04-01 11:00:00+09', 1); -- 佐藤次郎: エンジニア

-- リスク評価（低リスク）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(1, '低', '2024-05-01 15:00:00+09', 1, TRUE, FALSE);

-- 支援実施（技術支援）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(1, 1, 6, '2024-06-15 14:00:00+09', 'React最新バージョン移行サポート', 'React 18へのスムーズな移行完了', 'パフォーマンス改善を確認');

-- プロジェクト完了
INSERT INTO PROJECT_COMPLETE (ProjectID, CompleteDateTime, ActualEffort, RegisteredBy) VALUES
(1, '2024-09-25 17:00:00+09', 480.00, 1);

-- ========================================
-- シナリオ2: プロジェクト2（勘定系リプレース）
-- 途中で担当者交代・リスク上昇があるプロジェクト
-- ========================================

-- プロジェクト開始
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(2, '2024-05-01 09:00:00+09', 2);

-- 組織参画
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(2, 2, '2024-05-01 09:00:00+09', 2), -- 第一開発部
(2, 4, '2024-05-01 09:00:00+09', 2); -- 品質保証部

-- 担当者アサイン
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(2, 2, 1, '2024-05-01 10:00:00+09', 2), -- 鈴木花子: PM
(2, 4, 2, '2024-05-01 10:00:00+09', 2), -- 田中美咲: リードエンジニア
(2, 5, 3, '2024-05-01 10:00:00+09', 2); -- 高橋健一: エンジニア

-- リスク評価（初回：中リスク）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '中', '2024-06-01 16:00:00+09', 2, TRUE, FALSE);

-- 担当者交代（高橋 → 佐藤）
INSERT INTO PERSON_REPLACE (ProjectID, OldPersonID, NewPersonID, RoleID, ReplaceDateTime, RegisteredBy) VALUES
(2, 5, 3, 3, '2024-07-10 14:00:00+09', 2);

-- リスク評価（交代後：高リスク）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '高', '2024-08-01 11:00:00+09', 2, TRUE, FALSE);

-- 支援実施（リスク対策）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(2, 3, 6, '2024-08-15 10:00:00+09', '進捗遅延の原因分析と対策提案', 'リソース追加と作業分担見直し実施', 'プロジェクト計画を再調整');

-- リスク評価（対策後：中リスク）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(2, '中', '2024-09-01 15:00:00+09', 2, FALSE, TRUE);

-- 支援実施（プロセス改善）
INSERT INTO SUPPORT_EXECUTE (ProjectID, SupportTypeID, SupportPersonID, ExecuteDateTime, SupportContent, Outcome, Memo) VALUES
(2, 2, 6, '2024-10-01 14:00:00+09', 'コミュニケーション改善とレビュー強化', 'チーム連携が改善し品質向上', '定例ミーティング頻度を増加');

-- ========================================
-- シナリオ3: プロジェクト3（生産管理システム改修）
-- 開始直後でこれから進行するプロジェクト
-- ========================================

-- プロジェクト開始
INSERT INTO PROJECT_START (ProjectID, StartDateTime, RegisteredBy) VALUES
(3, '2024-06-01 09:00:00+09', 3);

-- 組織参画
INSERT INTO ORGANIZATION_JOIN (ProjectID, OrganizationID, JoinDateTime, RegisteredBy) VALUES
(3, 3, '2024-06-01 09:00:00+09', 3); -- 第二開発部

-- 担当者アサイン
INSERT INTO PERSON_ASSIGN (ProjectID, PersonID, RoleID, AssignDateTime, RegisteredBy) VALUES
(3, 3, 1, '2024-06-01 10:00:00+09', 3), -- 佐藤次郎: PM
(3, 4, 3, '2024-06-01 10:00:00+09', 3), -- 田中美咲: エンジニア
(3, 5, 4, '2024-06-01 10:00:00+09', 3); -- 高橋健一: QAエンジニア

-- リスク評価（初回：低リスク）
INSERT INTO RISK_EVALUATE (ProjectID, RiskRank, EvaluateDateTime, EvaluatedBy, IsSystemProposed, IsManualAdjusted) VALUES
(3, '低', '2024-07-01 14:00:00+09', 3, TRUE, FALSE);

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
--   ✅ 完了プロジェクト: プロジェクト1（順調に完了）
--   ⚠️ 進行中（課題あり）: プロジェクト2（担当者交代、リスク変動あり）
--   🆕 開始直後: プロジェクト3（順調にスタート）
-- ================================================
