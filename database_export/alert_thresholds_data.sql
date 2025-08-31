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
-- Table structure for table `alert_thresholds`
--

DROP TABLE IF EXISTS `alert_thresholds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alert_thresholds` (
  `id` int NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `server_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `warning_threshold` float NOT NULL,
  `critical_threshold` float NOT NULL,
  `unit` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `enabled` tinyint(1) DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `alert_thresholds_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alert_thresholds`
--

LOCK TABLES `alert_thresholds` WRITE;
/*!40000 ALTER TABLE `alert_thresholds` DISABLE KEYS */;
INSERT INTO `alert_thresholds` (`id`, `metric_name`, `server_type`, `warning_threshold`, `critical_threshold`, `unit`, `enabled`, `description`, `created_at`, `updated_at`, `created_by`) VALUES (19,'offset','all',200,350,'ms',1,'Seuil optimisé offset production','2025-07-07 22:31:18','2025-08-03 07:57:48',NULL),(20,'latency','all',50,500,'ms',1,'Seuil optimisé latency production','2025-07-07 22:31:18','2025-08-03 07:57:48',NULL),(21,'stratum','all',1,3,'level',1,'Seuil optimisé stratum production','2025-07-07 22:31:18','2025-08-03 07:57:48',NULL),(22,'test_metric','all',100,500,'ms',1,'Seuil de test','2025-07-14 16:23:04','2025-07-14 16:30:13',NULL),(23,'offset','local',300,500,'ms',1,'Écart de synchronisation en millisecondes','2025-08-02 18:18:46','2025-08-03 16:49:18',NULL),(24,'offset','pool',250,500,'ms',1,'Écart de synchronisation en millisecondes','2025-08-02 18:18:46','2025-08-03 16:52:07',NULL),(25,'offset','internet',250,400,'ms',1,'Écart de synchronisation en millisecondes','2025-08-02 18:18:46','2025-08-03 16:53:19',NULL),(26,'latency','local',50,300,'ms',1,'Délai de réponse en millisecondes','2025-08-02 18:18:46','2025-08-03 16:49:18',NULL),(27,'latency','pool',100,500,'ms',1,'Délai de réponse en millisecondes','2025-08-02 18:18:46','2025-08-03 16:52:07',NULL),(28,'latency','internet',150,300,'ms',1,'Délai de réponse en millisecondes','2025-08-02 18:18:46','2025-08-03 16:53:19',NULL),(29,'stratum','local',0,3,'level',1,'Niveau de précision du serveur','2025-08-02 18:18:46','2025-08-03 16:49:18',NULL),(30,'stratum','pool',0,3,'level',1,'Niveau de précision du serveur','2025-08-02 18:18:46','2025-08-03 16:52:07',NULL),(31,'stratum','internet',0,3,'level',1,'Niveau de précision du serveur','2025-08-02 18:18:46','2025-08-03 16:53:19',NULL),(32,'availability','local',98,95,'%',1,'Pourcentage de disponibilité','2025-08-02 18:18:46','2025-08-03 16:49:18',NULL),(33,'availability','pool',98,95,'%',1,'Pourcentage de disponibilité','2025-08-02 18:18:46','2025-08-03 16:52:07',NULL),(34,'availability','internet',98,95,'%',1,'Pourcentage de disponibilité','2025-08-02 18:18:46','2025-08-03 16:53:19',NULL),(35,'availability','all',98,90,'%',1,'Pourcentage de disponibilité','2025-08-02 18:18:46','2025-08-03 09:10:37',NULL),(36,'internet','local',0,0,'bool',1,'État de la connexion internet','2025-08-02 18:18:46','2025-08-02 18:18:46',NULL),(37,'internet','pool',0,0,'bool',1,'État de la connexion internet','2025-08-02 18:18:46','2025-08-02 18:18:46',NULL),(38,'internet','internet',0,0,'bool',1,'État de la connexion internet','2025-08-02 18:18:46','2025-08-03 10:01:49',NULL),(39,'internet','all',0,0,'bool',1,'État de la connexion internet','2025-08-02 18:18:46','2025-08-02 18:18:46',NULL),(40,'test_metric','local',100,500,'ms',1,'Seuil de test','2025-08-02 18:40:30','2025-08-03 09:10:37',NULL),(41,'test_metric_api','local',150,600,'ms',1,'Seuil de test API','2025-08-02 19:25:07','2025-08-02 19:25:07',NULL);
/*!40000 ALTER TABLE `alert_thresholds` ENABLE KEYS */;
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
