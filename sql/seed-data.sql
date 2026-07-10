-- ============================================
--  实习通 · 种子数据（含偏好标签表 + 演示数据）
--  在 schema-mysql.sql 建表后执行此文件
-- ============================================

USE internship_platform;

-- ============================================
-- 8. 用户偏好标签表（Pixiv风格喜好tag）
-- ============================================
CREATE TABLE IF NOT EXISTS user_tag_preferences (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    tag_name    VARCHAR(50) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_tag (user_id, tag_name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================
-- 更新测试用户密码为真实 bcrypt hash
-- 密码统一为: 123456
-- ============================================
UPDATE users SET password_hash = '$2a$10$1G8jN5rru/6SuaBYODRJNO0Wt2Ha9JRN3dBl9NQvSlkiLo1tapWy.';

-- 张三设为会员（已绑定邮箱，可直接发布/收藏/评论）
UPDATE users SET is_member = 1, email_verified = 1 WHERE username = '张三';

-- ============================================
-- 插入/更新管理员账号（内部使用）
-- 账号: admin  密码: admin123  |  管理员权限最大，无需绑定邮箱
-- ============================================
INSERT IGNORE INTO users (username, password_hash, email, school, role, bio, is_member, email_verified) VALUES
('admin', '$2a$10$6ddM66YHzbSPtFHW1tzHNu8Gz.shUHOFL5G9yHuAdBt1AqJWCgOyC', 'admin@shixitong.cn', '实习通官方', 'admin', '🛡️ 平台管理员（内部账号）', 1, 1);
-- 确保管理员密码和会员状态正确
UPDATE users SET password_hash = '$2a$10$6ddM66YHzbSPtFHW1tzHNu8Gz.shUHOFL5G9yHuAdBt1AqJWCgOyC', is_member = 1, email_verified = 1 WHERE username = 'admin';

-- ============================================
-- 补充实习-标签关联（4条已有实习）
-- ============================================
-- #1 前端开发实习生-字节跳动 → React, TypeScript, Node.js, 可转正
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(1, 1), (1, 3), (1, 5), (1, 16);
-- #2 产品经理-阿里巴巴 → 数据分析
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(2, 10);
-- #3 Golang后端-腾讯 → Go, 微服务, 导师带教
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(3, 8), (3, 18);
-- #4 数据分析-美团 → SQL, Python, 可转正
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(4, 10), (4, 6), (4, 16);

-- ============================================
-- 新增3条实习数据
-- ============================================
INSERT INTO internships (poster_id, title, company, city, district, job_type, salary_min, salary_max, education, days_per_week, duration_months, deadline, target_grade, target_major, headcount, description, requirements, can_refer, status) VALUES

(3, 'Java后端实习生',  '华为',   '深圳', '坂田', '技术开发', 400, 500, '硕士及以上', 5, 6, '2026-07-25',
 '2027届、2028届', '计算机/软件、电子信息/通信', 5,
 '参与华为云核心后端服务开发，负责高并发分布式系统的设计与实现。\n\n工作内容：\n• 参与微服务架构设计与开发\n• 负责API网关和中间件优化\n• 参与技术方案评审与Code Review\n• 撰写技术文档与最佳实践',
 '• 硕士及以上学历，计算机相关专业\n• 精通Java，熟悉Spring Boot/Spring Cloud\n• 了解Docker和Kubernetes\n• 有分布式系统项目经验优先\n• 每周出勤5天，实习期6个月以上',
 0, 'active'),

(2, '内容运营实习生',  '小红书', '上海', '黄浦', '运营',    200, 300, '本科及以上', 4, 3, '2026-08-10',
 '2026届、2027届', '市场营销/广告、设计/传媒', 3,
 '参与小红书社区内容运营，策划热门话题与活动。\n\n工作内容：\n• 策划社区话题与活动方案\n• 分析用户内容消费数据\n• 与达人创作者对接合作\n• 输出运营报告与优化建议',
 '• 本科及以上学历，传媒/营销相关专业优先\n• 小红书重度用户，了解社区文化\n• 有基础数据分析能力\n• 文案功底好，有创意\n• 每周出勤4天，实习期3个月以上',
 0, 'active'),

(1, '算法实习生（NLP方向）', '微软亚洲研究院', '北京', '海淀', '技术开发', 500, 600, '硕士及以上', 5, 6, '2026-08-15',
 '2027届、2028届', '人工智能/大数据、计算机/软件、数学/统计', 3,
 '加入微软亚洲研究院NLP组，参与前沿自然语言处理研究。\n\n工作内容：\n• 参与大语言模型相关研究\n• 阅读前沿论文并复现实验\n• 撰写学术论文（目标顶会）\n• 与研究员协作推进项目',
 '• 硕士及以上学历，AI/CS/数学相关专业\n• 熟练使用PyTorch/TensorFlow\n• 有NLP相关项目或论文经验\n• 数学基础扎实，编码能力强\n• 每周出勤5天，实习期6个月以上',
 1, 'active');

-- ============================================
-- 新实习的标签关联
-- ============================================
-- #5 Java后端-华为 → Java, Spring, K8s, Docker
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(5, 7), (5, 11), (5, 14), (5, 15);
-- #6 内容运营-小红书 → 可转正, 免费三餐
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(6, 16), (6, 19);
-- #7 算法-NLP → PyTorch, Python, 大厂
INSERT IGNORE INTO internship_tags (internship_id, tag_id) VALUES
(7, 13), (7, 6), (7, 20);

-- ============================================
-- 收藏数据（让演示时收藏页不空）
-- ============================================
INSERT IGNORE INTO favorites (user_id, internship_id) VALUES
(2, 1), (2, 6),
(3, 1), (3, 3), (3, 5),
(4, 2), (4, 4), (4, 7);

-- 更新收藏计数
UPDATE internships SET favorite_count = (SELECT COUNT(*) FROM favorites WHERE internship_id = internships.id);

-- ============================================
-- 用户偏好标签（Pixiv风格喜好tag）
-- ============================================
INSERT IGNORE INTO user_tag_preferences (user_id, tag_name) VALUES
(1, 'React'), (1, 'TypeScript'), (1, '大厂'), (1, '可转正'), (1, 'Node.js'),
(2, '产品经理'), (2, '数据分析'), (2, '可转正'), (2, '运营'),
(3, 'Go'), (3, '微服务'), (3, '大厂'), (3, 'Java'),
(4, 'Python'), (4, 'SQL'), (4, '数据分析'), (4, '可转正');

-- ============================================
-- 感谢数据
-- ============================================
INSERT IGNORE INTO thanks (from_user_id, to_user_id, internship_id, message) VALUES
(2, 1, 1, '感谢分享，已经拿到offer了！'),
(3, 1, 7, '谢谢学长的信息，面试中'),
(4, 2, 2, '好人一生平安'),
(2, 3, 5, '感谢！');

-- ============================================
-- 验证数据
-- ============================================
SELECT '=== 数据统计 ===' AS '';
SELECT 'users' AS tbl, COUNT(*) AS cnt FROM users
UNION ALL SELECT 'internships', COUNT(*) FROM internships
UNION ALL SELECT 'tags', COUNT(*) FROM tags
UNION ALL SELECT 'internship_tags', COUNT(*) FROM internship_tags
UNION ALL SELECT 'favorites', COUNT(*) FROM favorites
UNION ALL SELECT 'user_tag_preferences', COUNT(*) FROM user_tag_preferences
UNION ALL SELECT 'thanks', COUNT(*) FROM thanks;
