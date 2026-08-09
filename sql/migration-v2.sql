-- ============================================
--  迁移: 去掉会员系统 + 增加密码修改限制
--  执行前请备份数据库
-- ============================================

USE internship_platform;

-- 1. 去掉会员字段
ALTER TABLE users DROP COLUMN IF EXISTS is_member;
ALTER TABLE users DROP COLUMN IF EXISTS email_verified;

-- 2. 增加密码修改时间（用于7天限制）
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP NULL AFTER password_hash;

-- 3. 清理不再需要的表（如果存在）
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS user_tag_preferences;

-- 4. 清理不再需要的路由对应的表
-- reports 表保留（举报功能）
