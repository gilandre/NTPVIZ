-- Table d'audit pour persister les logs
CREATE TABLE IF NOT EXISTS audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  user_id INT NULL,
  username VARCHAR(150) NULL,
  role VARCHAR(50) NULL,
  action VARCHAR(100) NOT NULL,
  resource VARCHAR(100) NULL,
  resource_id VARCHAR(100) NULL,
  details TEXT NULL,
  ip_address VARCHAR(64) NULL,
  user_agent TEXT NULL,
  method VARCHAR(10) NULL,
  endpoint VARCHAR(200) NULL,
  url TEXT NULL,
  INDEX idx_timestamp (timestamp),
  INDEX idx_user_id (user_id),
  INDEX idx_action (action),
  INDEX idx_resource (resource),
  INDEX idx_resource_id (resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


