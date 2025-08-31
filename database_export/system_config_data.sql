-- MySQL dump 10.13  Distrib 9.2.0, for macos14.7 (x86_64)
--
-- Host: localhost    Database: ntp_monitor
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `system_config`
--

DROP TABLE IF EXISTS `system_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `value_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `category` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_public` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `updated_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_config_key_name` (`key_name`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_config`
--

LOCK TABLES `system_config` WRITE;
/*!40000 ALTER TABLE `system_config` DISABLE KEYS */;
INSERT INTO `system_config` (`id`, `key_name`, `value`, `value_type`, `category`, `description`, `is_public`, `created_at`, `updated_at`, `updated_by`) VALUES (1,'ntp_sync_interval','45','string','general','Intervalle de synchronisation NTP (secondes)',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(2,'alert_threshold_offset','250','string','general','Seuil d\'alerte pour le décalage temporel (ms)',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(3,'dashboard_refresh_rate','30','string','general','Taux de rafraichissement du dashboard (secondes)',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(4,'log_retention_days','30','string','general','Durée de rétention des logs (jours)',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(5,'email_notifications','false','string','general','Notifications par email activées',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(6,'monitoring_enabled','true','string','general','Monitoring automatique activé',1,'2025-07-06 13:31:55','2025-08-02 19:02:54',15),(14,'alerts.offset_warning_threshold','250.0','int','alerts','Configuration des alertes: offset_warning_threshold',0,'2025-07-07 06:55:13','2025-08-03 16:53:19',15),(15,'alerts.offset_critical_threshold','400.0','int','alerts','Configuration des alertes: offset_critical_threshold',0,'2025-07-07 06:55:13','2025-08-03 16:53:19',15),(16,'alerts.latency_warning_threshold','150.0','int','alerts','Configuration des alertes: latency_warning_threshold',0,'2025-07-07 06:55:13','2025-08-03 16:53:19',15),(17,'alerts.latency_critical_threshold','300.0','int','alerts','Configuration des alertes: latency_critical_threshold',0,'2025-07-07 06:55:13','2025-08-03 16:53:19',15),(18,'alerts.stratum_max_threshold','0.0','int','alerts','Configuration des alertes: stratum_max_threshold',0,'2025-07-07 06:55:13','2025-08-03 16:53:19',15),(19,'alerts.connection_timeout','30','int','alerts','Configuration des alertes: connection_timeout',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(20,'alerts.max_consecutive_failures','3','int','alerts','Configuration des alertes: max_consecutive_failures',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(21,'alerts.email_notifications','False','bool','alerts','Configuration des alertes: email_notifications',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(22,'alerts.email_addresses','','string','alerts','Configuration des alertes: email_addresses',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(23,'alerts.webhook_notifications','False','bool','alerts','Configuration des alertes: webhook_notifications',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(24,'alerts.webhook_url','','string','alerts','Configuration des alertes: webhook_url',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(25,'alerts.min_alert_interval','15','int','alerts','Configuration des alertes: min_alert_interval',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(26,'alerts.escalation_enabled','False','bool','alerts','Configuration des alertes: escalation_enabled',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(27,'alerts.escalation_delay','2','int','alerts','Configuration des alertes: escalation_delay',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(28,'alerts.resolved_alerts_retention','30','int','alerts','Configuration des alertes: resolved_alerts_retention',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(29,'alerts.acknowledged_alerts_retention','7','int','alerts','Configuration des alertes: acknowledged_alerts_retention',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(30,'alerts.detailed_logs_retention','7','int','alerts','Configuration des alertes: detailed_logs_retention',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(31,'alerts.aggregated_logs_retention','90','int','alerts','Configuration des alertes: aggregated_logs_retention',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(32,'alerts.check_interval','60','int','alerts','Configuration des alertes: check_interval',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(33,'alerts.ntp_timeout','10','int','alerts','Configuration des alertes: ntp_timeout',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(34,'alerts.debug_mode','False','bool','alerts','Configuration des alertes: debug_mode',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(35,'alerts.require_auth_alerts','True','bool','alerts','Configuration des alertes: require_auth_alerts',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(36,'alerts.audit_log','True','bool','alerts','Configuration des alertes: audit_log',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(37,'alerts.log_level','INFO','string','alerts','Configuration des alertes: log_level',0,'2025-07-07 06:55:13','2025-08-02 19:02:04',15),(39,'alerts.stratum_critical_threshold','3.0','int','alerts','Seuil critique pour stratum',0,'2025-07-12 10:51:14','2025-08-03 16:53:19',NULL),(40,'system_name','NTPVIZ Test','string','general','Nom du système',0,'2025-07-14 19:31:20','2025-08-02 19:02:54',15),(41,'alert_email','test@example.com','string','alerts','Email pour les alertes',0,'2025-07-14 19:31:20','2025-07-14 20:26:43',1),(42,'retention_days','30','int','system','Jours de rétention des logs',0,'2025-07-14 19:31:20','2025-07-14 20:26:43',1),(43,'ntp.query_interval','25','int','ntp','Intervalle de requte',0,'2025-07-14 20:50:04','2025-08-02 19:03:11',15),(44,'ntp.default_timeout','5','int','ntp','Timeout par dfaut',0,'2025-07-14 20:50:04','2025-08-02 19:03:11',15),(45,'ntp.timeout','10','int','ntp','Timeout des requêtes NTP (secondes)',0,'2025-07-19 16:26:53','2025-08-02 19:03:11',15),(46,'ntp.retries','2','int','ntp','Nombre de tentatives NTP',0,'2025-07-19 16:26:53','2025-08-02 19:03:11',15),(47,'alerts.use_threshold_conditions','True','bool','alerts','Configuration alerte: alerts.use_threshold_conditions',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(48,'alerts.use_latency_conditions','True','bool','alerts','Configuration alerte: alerts.use_latency_conditions',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(49,'alerts.use_availability_conditions','True','bool','alerts','Configuration alerte: alerts.use_availability_conditions',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(50,'alerts.use_stratum_conditions','True','bool','alerts','Configuration alerte: alerts.use_stratum_conditions',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(51,'alerts.threshold_warning','0','float','alerts','Configuration alerte: alerts.threshold_warning',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(52,'alerts.threshold_critical','0','float','alerts','Configuration alerte: alerts.threshold_critical',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(53,'alerts.latency_warning','150','float','alerts','Configuration alerte: alerts.latency_warning',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(54,'alerts.latency_critical','300','float','alerts','Configuration alerte: alerts.latency_critical',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(55,'alerts.availability_warning','98','float','alerts','Configuration alerte: alerts.availability_warning',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(56,'alerts.availability_critical','95','float','alerts','Configuration alerte: alerts.availability_critical',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL),(57,'alerts.stratum_max','3','int','alerts','Configuration alerte: alerts.stratum_max',0,'2025-08-02 19:22:18','2025-08-03 16:53:19',NULL);
/*!40000 ALTER TABLE `system_config` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-07 14:09:02
