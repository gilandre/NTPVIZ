-- Ajouter contrainte d'unicité (metric_name, server_type_id) si absente
SET @idx_exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'alert_thresholds' AND INDEX_NAME = 'ux_alert_thresholds_metric_type'
);
SET @sql := IF(@idx_exists = 0,
  'CREATE UNIQUE INDEX ux_alert_thresholds_metric_type ON alert_thresholds(metric_name, server_type_id)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Étape ultérieure (après bascule complète UI/API/Services) : suppression du champ legacy
-- ALTER TABLE alert_thresholds DROP COLUMN server_type;

