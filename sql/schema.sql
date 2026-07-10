-- ============================================
--  实习通 · 数据库结构设计
--  兼容 PostgreSQL / MySQL 8.0+
-- ============================================

-- 1. 用户表
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(30)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(100),
    school          VARCHAR(100),           -- 学校
    major           VARCHAR(100),           -- 专业
    grade           VARCHAR(20),            -- 年级，如 2026届
    bio             VARCHAR(500),           -- 个人简介
    avatar_url      VARCHAR(500),           -- 头像URL
    role            VARCHAR(20)  DEFAULT 'student',  -- student / admin
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 2. 实习信息表
CREATE TABLE internships (
    id              BIGSERIAL PRIMARY KEY,
    poster_id       BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,           -- 岗位名
    company         VARCHAR(200) NOT NULL,           -- 公司名
    city            VARCHAR(50)  NOT NULL,           -- 城市
    district        VARCHAR(100),                    -- 区/详细地址
    job_type        VARCHAR(50)  NOT NULL,           -- 岗位类型: 技术/产品/设计/...
    salary_min      INTEGER,                        -- 最低日薪
    salary_max      INTEGER,                        -- 最高日薪
    education       VARCHAR(30)  DEFAULT '本科及以上', -- 学历要求
    days_per_week   INTEGER      DEFAULT 4,          -- 每周天数
    duration_months INTEGER      DEFAULT 3,          -- 实习月数
    target_grade    VARCHAR(50),                     -- 面向年级
    target_major    VARCHAR(500),                    -- 面向专业（逗号分隔）
    headcount       INTEGER      DEFAULT 1,          -- 招聘人数
    deadline        DATE,                            -- 截止日期
    description     TEXT,                            -- 职位描述
    requirements    TEXT,                            -- 任职要求
    apply_url       VARCHAR(500),                    -- 投递链接
    apply_email     VARCHAR(100),                    -- 投递邮箱
    can_refer       BOOLEAN      DEFAULT FALSE,      -- 是否可内推
    view_count      INTEGER      DEFAULT 0,          -- 浏览次数
    favorite_count  INTEGER      DEFAULT 0,          -- 收藏次数
    status          VARCHAR(20)  DEFAULT 'active',   -- active / closed / draft
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    -- 索引：按城市+岗位类型查询是最频繁的
    INDEX idx_city_job (city, job_type),
    INDEX idx_poster (poster_id),
    INDEX idx_status_deadline (status, deadline),
    INDEX idx_created (created_at DESC)
);

-- 3. 标签表
CREATE TABLE tags (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(30) NOT NULL UNIQUE
);

-- 4. 实习-标签关联表
CREATE TABLE internship_tags (
    internship_id BIGINT NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    tag_id        INT    NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (internship_id, tag_id)
);

-- 预置标签
INSERT INTO tags (name) VALUES
('React'),('Vue'),('TypeScript'),('JavaScript'),('Node.js'),
('Python'),('Java'),('Go'),('C/C++'),('SQL'),
('Spring'),('Django'),('PyTorch'),('K8s'),('Docker'),
('可转正'),('远程办公'),('导师带教'),('免费三餐'),('大厂');

-- 5. 收藏表
CREATE TABLE favorites (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    internship_id   BIGINT NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, internship_id)
);

-- 6. 订阅表
CREATE TABLE subscriptions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword     VARCHAR(200),           -- 订阅关键词
    city        VARCHAR(50),            -- 订阅城市
    job_type    VARCHAR(50),            -- 订阅岗位类型
    major       VARCHAR(100),           -- 订阅专业
    is_active   BOOLEAN     DEFAULT TRUE,
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- 7. 反馈/感谢表（用户间互动）
CREATE TABLE thanks (
    id              BIGSERIAL PRIMARY KEY,
    from_user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    internship_id   BIGINT REFERENCES internships(id) ON DELETE SET NULL,
    message         VARCHAR(200),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
--  常用查询示例
-- ============================================

-- 首页列表：按时间倒序
-- SELECT i.*, u.username, u.school, u.avatar_url AS poster_avatar
-- FROM internships i
-- JOIN users u ON i.poster_id = u.id
-- WHERE i.status = 'active'
-- ORDER BY i.created_at DESC
-- LIMIT 20 OFFSET 0;

-- 按城市+岗位类型筛选
-- SELECT ... FROM internships
-- WHERE status = 'active'
--   AND city = '北京'
--   AND job_type = '技术开发'
-- ORDER BY created_at DESC;

-- 关键词搜索
-- SELECT ... FROM internships
-- WHERE status = 'active'
--   AND (title ILIKE '%前端%' OR company ILIKE '%字节%' OR description ILIKE '%React%');

-- 热门排行（按收藏数）
-- SELECT ... FROM internships
-- WHERE status = 'active'
--   AND created_at > NOW() - INTERVAL '7 days'
-- ORDER BY favorite_count DESC LIMIT 10;

-- 用户分享列表
-- SELECT ... FROM internships WHERE poster_id = ? ORDER BY created_at DESC;

-- 用户收藏列表
-- SELECT i.* FROM internships i
-- JOIN favorites f ON i.id = f.internship_id
-- WHERE f.user_id = ? ORDER BY f.created_at DESC;
