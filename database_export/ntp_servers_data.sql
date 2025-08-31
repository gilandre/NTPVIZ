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
-- Table structure for table `ntp_servers`
--

DROP TABLE IF EXISTS `ntp_servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ntp_servers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `port` int DEFAULT NULL,
  `server_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `timeout` float DEFAULT NULL,
  `max_offset` float DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_sync` datetime DEFAULT NULL,
  `last_offset` float DEFAULT NULL,
  `last_latency` float DEFAULT NULL,
  `last_stratum` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `critical_offset` float DEFAULT '5',
  `last_delay` float DEFAULT NULL,
  `last_internet_status` tinyint(1) DEFAULT NULL,
  `last_error` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `error_count` int DEFAULT '0',
  `consecutive_errors` int DEFAULT '0',
  `created_by` int DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ntp_servers_address_type_deleted` (`address`,`server_type`,`deleted_at`),
  KEY `fk_ntp_servers_deleted_by` (`deleted_by`),
  KEY `idx_ntp_servers_deleted_at` (`deleted_at`),
  KEY `idx_ntp_servers_active` (`is_active`,`deleted_at`),
  KEY `idx_ntp_servers_address_deleted` (`address`,`deleted_at`),
  CONSTRAINT `fk_ntp_servers_deleted_by` FOREIGN KEY (`deleted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ntp_servers`
--

LOCK TABLES `ntp_servers` WRITE;
/*!40000 ALTER TABLE `ntp_servers` DISABLE KEYS */;
INSERT INTO `ntp_servers` (`id`, `name`, `address`, `port`, `server_type`, `priority`, `is_active`, `timeout`, `max_offset`, `description`, `status`, `last_sync`, `last_offset`, `last_latency`, `last_stratum`, `created_at`, `updated_at`, `critical_offset`, `last_delay`, `last_internet_status`, `last_error`, `error_count`, `consecutive_errors`, `created_by`, `deleted_at`, `deleted_by`) VALUES (24,'Pool NTP 0','0.pool.ntp.org',123,'global',6,1,15,500,'','ok','2025-08-07 13:31:19',0.460306,0.219562,2,'2025-07-18 19:13:47','2025-08-07 13:31:19',1000,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(25,'Pool NTP 1','1.pool.ntp.org',123,'global',3,1,15,500,'','ok','2025-08-07 13:31:19',0.469511,0.265216,2,'2025-07-18 19:13:47','2025-08-07 13:31:20',1000,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(26,'Pool NTP 2','2.pool.ntp.org',123,'global',4,1,15,500,'','ok','2025-08-07 13:31:20',0.468644,0.223094,2,'2025-07-18 19:13:47','2025-08-07 13:31:20',1000,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(27,'Pool NTP 3','3.pool.ntp.org',123,'global',5,1,20,1000,'','ok','2025-08-07 13:31:20',0.447035,0.314689,2,'2025-07-18 19:13:47','2025-08-07 13:31:20',2000,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(67,'Serveur principal','70.137.36.66',123,'local',1,1,20,1000,'Serveur de distribution d\'heure NTP aux autres NVR sur le reseau.','offline','2025-08-07 13:31:08',NULL,NULL,NULL,'2025-07-19 10:05:31','2025-08-07 13:31:28',2000,NULL,NULL,NULL,0,0,1,NULL,NULL),(71,'serveur NTP 2','192.168.7.28',123,'local',2,1,20,1000,'','offline','2025-08-07 13:30:52',NULL,NULL,NULL,'2025-07-19 10:33:01','2025-08-07 13:31:12',2000,NULL,NULL,NULL,0,0,1,NULL,NULL),(72,'Serveur Temps France','ntp.pool.ntp.org',123,'global',5,1,10,NULL,NULL,'offline','2025-08-07 13:31:12',NULL,NULL,NULL,'2025-08-07 13:19:02','2025-08-07 13:31:12',5,NULL,NULL,NULL,0,0,NULL,NULL,NULL),(73,'Serveur de secours','time.cloudflare.com',123,'global',6,1,10,NULL,NULL,'ok','2025-08-07 13:31:12',0.682761,0.424351,3,'2025-08-07 13:19:02','2025-08-07 13:31:13',5,NULL,NULL,NULL,0,0,NULL,NULL,NULL);
/*!40000 ALTER TABLE `ntp_servers` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-07 14:09:01
