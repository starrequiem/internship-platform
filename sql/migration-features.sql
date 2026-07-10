-- ============================================
--  实习通 · 新功能迁移（通知 + 投递）
--  执行方式：mysql -u root -p200619 internship_platform < migration-features.sql
-- ============================================

USE internship_platform;

-- 1. 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    type            VARCHAR(30) NOT NULL DEFAULT 'subscription',
    title           VARCHAR(200) NOT NULL,
    content         TEXT,
    internship_id   BIGINT,
    is_read         TINYINT(1) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE SET NULL,
    INDEX idx_user_read (user_id, is_read, created_at)
) ENGINE=InnoDB;

-- 2. 投递记录表
CREATE TABLE IF NOT EXISTS applications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    internship_id   BIGINT NOT NULL,
    status          ENUM('clicked','submitted','interview','offer','rejected') DEFAULT 'clicked' COMMENT '投递状态',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_internship (user_id, internship_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE
) ENGINE=InnoDB;
