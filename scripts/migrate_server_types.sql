-- Idempotent migration for server_types and server_type_id columns

-- 1) Create reference table if not exists
CREATE TABLE IF NOT EXISTS server_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(32) NOT NULL UNIQUE,
  label VARCHAR(64) NOT NULL,
  description VARCHAR(255) NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Seed base types if missing
INSERT IGNORE INTO server_types (code, label) VALUES
('local','Local'),
('internet','Internet'),
('pool','Pool public'),
('all','Tous');

-- 3) Add columns if not exists
-- Add ntp_servers.server_type_id if missing
SET @exists_col := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ntp_servers' AND COLUMN_NAME = 'server_type_id');
SET @sql := IF(@exists_col = 0, 'ALTER TABLE ntp_servers ADD COLUMN server_type_id INT NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add alert_thresholds.server_type_id if missing
SET @exists_col := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'alert_thresholds' AND COLUMN_NAME = 'server_type_id');
SET @sql := IF(@exists_col = 0, 'ALTER TABLE alert_thresholds ADD COLUMN server_type_id INT NULL', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4) Populate server_type_id from legacy values
UPDATE ntp_servers s
JOIN server_types t ON t.code = (
  CASE
    WHEN LOWER(TRIM(COALESCE(s.server_type, ''))) IN ('local','1','internal') THEN 'local'
    WHEN LOWER(TRIM(COALESCE(s.server_type, ''))) IN ('pool','2','public') THEN 'pool'
    WHEN LOWER(TRIM(COALESCE(s.server_type, ''))) IN ('global','internet') THEN 'internet'
    WHEN LOWER(TRIM(COALESCE(s.server_type, ''))) IN ('all','0','') THEN 'all'
    ELSE 'all'
  END
)
SET s.server_type_id = COALESCE(s.server_type_id, t.id);

UPDATE alert_thresholds a
JOIN server_types t ON t.code = (
  CASE
    WHEN LOWER(TRIM(COALESCE(a.server_type, ''))) IN ('local','1','internal') THEN 'local'
    WHEN LOWER(TRIM(COALESCE(a.server_type, ''))) IN ('pool','2','public') THEN 'pool'
    WHEN LOWER(TRIM(COALESCE(a.server_type, ''))) IN ('global','internet') THEN 'internet'
    WHEN LOWER(TRIM(COALESCE(a.server_type, ''))) IN ('all','0','') THEN 'all'
    ELSE 'all'
  END
)
SET a.server_type_id = COALESCE(a.server_type_id, t.id);

-- 5) Add FKs (guard against duplicates via names)
-- Add FK ntp_servers -> server_types if missing
SET @fk_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ntp_servers' AND CONSTRAINT_TYPE = 'FOREIGN KEY' AND CONSTRAINT_NAME = 'fk_ntp_servers_server_type');
SET @sql := IF(@fk_exists = 0, 'ALTER TABLE ntp_servers ADD CONSTRAINT fk_ntp_servers_server_type FOREIGN KEY (server_type_id) REFERENCES server_types(id)', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add FK alert_thresholds -> server_types if missing
SET @fk_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'alert_thresholds' AND CONSTRAINT_TYPE = 'FOREIGN KEY' AND CONSTRAINT_NAME = 'fk_alert_thresholds_server_type');
SET @sql := IF(@fk_exists = 0, 'ALTER TABLE alert_thresholds ADD CONSTRAINT fk_alert_thresholds_server_type FOREIGN KEY (server_type_id) REFERENCES server_types(id)', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 6) Add indexes
-- Create indexes if missing
SET @idx_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ntp_servers' AND INDEX_NAME = 'idx_ntp_servers_server_type_id');
SET @sql := IF(@idx_exists = 0, 'CREATE INDEX idx_ntp_servers_server_type_id ON ntp_servers(server_type_id)', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_exists := (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'alert_thresholds' AND INDEX_NAME = 'idx_alert_thresholds_server_type_id');
SET @sql := IF(@idx_exists = 0, 'CREATE INDEX idx_alert_thresholds_server_type_id ON alert_thresholds(server_type_id)', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 7) Make NOT NULL once populated (commented for safety - enable after validation)
-- ALTER TABLE ntp_servers MODIFY server_type_id INT NOT NULL;
-- ALTER TABLE alert_thresholds MODIFY server_type_id INT NOT NULL;

-- 8) Optional unique business rule on thresholds
-- CREATE UNIQUE INDEX ux_alert_thresholds_metric_type ON alert_thresholds(metric_name, server_type_id);

-- 9) Drop legacy columns after full rollout (commented for staged rollout)
-- ALTER TABLE ntp_servers DROP COLUMN server_type;
-- ALTER TABLE alert_thresholds DROP COLUMN server_type;


