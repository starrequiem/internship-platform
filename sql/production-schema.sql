-- 实习通生产环境基线结构。可重复执行，不包含本机业务数据。

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(30) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  password_changed_at TIMESTAMP NULL,
  email VARCHAR(100),
  school VARCHAR(100),
  major VARCHAR(100),
  grade VARCHAR(20),
  bio VARCHAR(500),
  avatar_url VARCHAR(500),
  role VARCHAR(20) DEFAULT 'student',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS internships (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  poster_id BIGINT NOT NULL,
  title VARCHAR(200) NOT NULL,
  company VARCHAR(200) NOT NULL,
  city VARCHAR(50) NOT NULL,
  district VARCHAR(100),
  job_type VARCHAR(50) NOT NULL,
  salary_min INT,
  salary_max INT,
  education VARCHAR(30) DEFAULT '本科及以上',
  days_per_week INT DEFAULT 4,
  duration_months INT DEFAULT 3,
  target_grade VARCHAR(50),
  target_major VARCHAR(500),
  headcount INT DEFAULT 1,
  deadline DATE,
  apply_time VARCHAR(100),
  description TEXT,
  requirements TEXT,
  contact_info TEXT,
  apply_url VARCHAR(500),
  apply_email VARCHAR(100),
  can_refer TINYINT(1) DEFAULT 0,
  view_count INT DEFAULT 0,
  favorite_count INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  review_status ENUM('pending','approved','rejected') DEFAULT 'approved',
  reviewed_at TIMESTAMP NULL,
  reviewed_by BIGINT,
  KEY idx_city_job (city, job_type),
  KEY idx_poster (poster_id),
  KEY idx_status (status, deadline),
  KEY idx_created (created_at),
  KEY idx_review (review_status, created_at),
  CONSTRAINT fk_internships_poster FOREIGN KEY (poster_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tags (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS internship_tags (
  internship_id BIGINT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (internship_id, tag_id),
  CONSTRAINT fk_internship_tags_internship FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,
  CONSTRAINT fk_internship_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS favorites (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  internship_id BIGINT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_favorites_user_internship (user_id, internship_id),
  CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_favorites_internship FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS thanks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  from_user_id BIGINT NOT NULL,
  to_user_id BIGINT NOT NULL,
  internship_id BIGINT,
  message VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_thanks_from_user FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_thanks_to_user FOREIGN KEY (to_user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_thanks_internship FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  internship_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  type ENUM('duplicate','error','outdated','other') DEFAULT 'other',
  message TEXT,
  status ENUM('pending','reviewed','resolved') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_reports_internship (internship_id),
  KEY idx_reports_status (status),
  KEY idx_reports_user (user_id),
  CONSTRAINT fk_reports_internship FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE,
  CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS applications (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  internship_id BIGINT NOT NULL,
  status ENUM('clicked','submitted','interview','offer','rejected') DEFAULT 'clicked',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_applications_user_internship (user_id, internship_id),
  CONSTRAINT fk_applications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_applications_internship FOREIGN KEY (internship_id) REFERENCES internships(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO tags (name) VALUES
  ('React'), ('Vue'), ('TypeScript'), ('JavaScript'), ('Node.js'),
  ('Python'), ('Java'), ('Go'), ('SQL'), ('机器学习'), ('数据分析'),
  ('产品设计'), ('UI设计'), ('可转正'), ('导师带教'), ('免费三餐'),
  ('远程面试'), ('大厂');
