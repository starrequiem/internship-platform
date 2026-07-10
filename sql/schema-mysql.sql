-- ============================================
--  实习通 · MySQL 数据库
-- ============================================

CREATE DATABASE IF NOT EXISTS internship_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE internship_platform;

-- 1. 用户表
CREATE TABLE users (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(30)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(100),
    school          VARCHAR(100),
    major           VARCHAR(100),
    grade           VARCHAR(20),
    bio             VARCHAR(500),
    avatar_url      VARCHAR(500),
    role            VARCHAR(20)  DEFAULT 'student',
    is_member       TINYINT(1)   DEFAULT 0 COMMENT '是否会员',
    email_verified  TINYINT(1)   DEFAULT 0 COMMENT '邮箱是否已验证',
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. 实习信息表
CREATE TABLE internships (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    poster_id       BIGINT       NOT NULL,
    title           VARCHAR(200) NOT NULL,
    company         VARCHAR(200) NOT NULL,
    city            VARCHAR(50)  NOT NULL,
    district        VARCHAR(100),
    job_type        VARCHAR(50)  NOT NULL,
    salary_min      INT,
    salary_max      INT,
    education       VARCHAR(30)  DEFAULT '本科及以上',
    days_per_week   INT          DEFAULT 4,
    duration_months INT          DEFAULT 3,
    target_grade    VARCHAR(50),
    target_major    VARCHAR(500),
    headcount       INT          DEFAULT 1,
    deadline        DATE,
    description     TEXT,
    requirements    TEXT,
    apply_url       VARCHAR(500),
    apply_email     VARCHAR(100),
    can_refer       TINYINT(1)   DEFAULT 0,
    view_count      INT          DEFAULT 0,
    favorite_count  INT          DEFAULT 0,
    status          VARCHAR(20)  DEFAULT 'active',
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (poster_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_city_job (city, job_type),
    INDEX idx_poster (poster_id),
    INDEX idx_status (status, deadline),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- 3. 标签表
CREATE TABLE tags (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- 4. 实习-标签关联
CREATE TABLE internship_tags (
    internship_id BIGINT NOT NULL,
    tag_id        INT    NOT NULL,
    PRIMARY KEY (internship_id, tag_id),
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)        REFERENCES tags(id)        ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. 收藏表
CREATE TABLE favorites (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    internship_id BIGINT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_intern (user_id, internship_id),
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. 订阅表
CREATE TABLE subscriptions (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT      NOT NULL,
    keyword     VARCHAR(200),
    city        VARCHAR(50),
    job_type    VARCHAR(50),
    major       VARCHAR(100),
    is_active   TINYINT(1)  DEFAULT 1,
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. 用户偏好标签表
CREATE TABLE user_tag_preferences (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    tag_name    VARCHAR(50) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_tag (user_id, tag_name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. 感谢表
CREATE TABLE thanks (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    from_user_id    BIGINT NOT NULL,
    to_user_id      BIGINT NOT NULL,
    internship_id   BIGINT,
    message         VARCHAR(200),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id)  REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (to_user_id)    REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ========== 预置标签 ==========
INSERT INTO tags (name) VALUES
('React'),('Vue'),('TypeScript'),('JavaScript'),('Node.js'),
('Python'),('Java'),('Go'),('C/C++'),('SQL'),
('Spring'),('Django'),('PyTorch'),('K8s'),('Docker'),
('可转正'),('远程办公'),('导师带教'),('免费三餐'),('大厂');

-- ========== 测试用户 ==========
-- 注意：普通用户即使填了邮箱，也需要验证后才能升级会员
-- 管理员直接拥有全部权限
INSERT INTO users (username, password_hash, email, school, major, grade, bio, role, is_member, email_verified) VALUES
('admin',  '$2a$10$YvOlacI1Z9m8sIO6lfYT9ugkEJnvG1877U.BrY2JRIfLusxjzeZia', 'admin@shixitong.cn', '实习通官方', '--', '--', '🛡️ 平台管理员（内部账号）', 'admin', 1, 1),
('张三',   'test_hash', 'zhangsan@tsinghua.edu.cn',  '清华大学', '计算机科学与技术', '2026届', '希望能帮学弟学妹少走弯路', 'student', 1, 1),
('王同学', 'test_hash', 'wang@zju.edu.cn',            '浙江大学', '产品设计',         '2026届', '', 'student', 0, 0),
('陈学长', 'test_hash', 'chen@hust.edu.cn',           '华中科技大学', '计算机科学',   '2026届', '', 'student', 0, 0),
('刘学姐', 'test_hash', NULL,                         '上海交通大学', '数据科学',     '2026届', '', 'student', 0, 0);

-- ========== 测试数据 ==========
INSERT INTO internships (poster_id, title, company, city, district, job_type, salary_min, salary_max, education, days_per_week, duration_months, deadline, description, requirements, can_refer, status) VALUES
(1, '前端开发实习生',    '字节跳动', '北京', '海淀', '技术开发', 400, 500, '本科及以上', 4, 3, '2026-07-20', '参与抖音电商核心业务前端开发，使用 React + TypeScript 技术栈。导师一对一带教。', '熟悉 HTML/CSS/JS，了解 React 或 Vue，有 TypeScript 经验优先', 0, 'active'),
(2, '产品经理实习生',    '阿里巴巴', '杭州', '余杭', '产品经理', 350, 450, '硕士优先',   5, 6, '2026-08-15', '参与B端产品设计与迭代，与业务团队紧密协作。', '逻辑清晰，有数据分析基础，了解产品设计流程', 0, 'active'),
(1, 'Golang后端实习生',  '腾讯',     '深圳', '南山', '技术开发', 450, 550, '本科及以上', 4, 3, '2026-07-30', '负责腾讯核心服务后端开发，涉及高并发分布式系统。', '熟悉 Go 或 Java，了解微服务架构，有项目经验优先', 0, 'active'),
(4, '数据分析实习生',    '美团',     '上海', '杨浦', '数据分析', 300, 400, '本科及以上', 4, 4, '2026-08-01', '参与业务数据分析，输出数据报告驱动决策。', '熟练 SQL 和 Python，有 Tableau 经验优先', 0, 'active');
