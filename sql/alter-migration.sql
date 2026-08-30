-- ============================================
--  实习通 · 会员系统迁移脚本
--  执行方式：mysql -u root -p internship_platform < alter-migration.sql
-- ============================================

USE internship_platform;

-- 添加会员相关字段
ALTER TABLE users
  ADD COLUMN is_member TINYINT(1) DEFAULT 0 COMMENT '是否会员（绑定邮箱后自动升级）',
  ADD COLUMN email_verified TINYINT(1) DEFAULT 0 COMMENT '邮箱是否已验证';

-- 管理员权限最大，直接标记为会员（无需绑定邮箱）
UPDATE users SET is_member = 1, email_verified = 1 WHERE role = 'admin';

-- 张三：演示用会员账号（已绑定邮箱）
UPDATE users SET is_member = 1, email_verified = 1 WHERE username = '张三';

-- 注意：其余普通用户即使注册时填了邮箱，也需要通过验证码验证后才能升级会员
