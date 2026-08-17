-- ============================================
--  实习通 · 新增「投递时间」字段迁移
--  执行方式：mysql -u root -p200619 internship_platform < migration-apply-time.sql
-- ============================================

USE internship_platform;

-- 投递时间区间原文（如「2026年3月23日-2026年8月31日」），与 deadline(截止日期) 并存
ALTER TABLE internships ADD COLUMN apply_time VARCHAR(100) NULL COMMENT '投递时间区间原文' AFTER deadline;
