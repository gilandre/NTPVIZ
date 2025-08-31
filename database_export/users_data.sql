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
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `login_count` int DEFAULT NULL,
  `preferences` json DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_username` (`username`),
  KEY `fk_users_deleted_by` (`deleted_by`),
  KEY `idx_users_deleted_at` (`deleted_at`),
  CONSTRAINT `fk_users_deleted_by` FOREIGN KEY (`deleted_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `first_name`, `last_name`, `role`, `is_active`, `created_at`, `last_login`, `login_count`, `preferences`, `deleted_at`, `deleted_by`) VALUES (2,'operator','operator@ntp-monitor.local','pbkdf2:sha256:600000$tkHB3lgAWAU73W5f$30ee73bb7abf5c71c93778278c33ca25de83f5b7517c73801e9258f7f4726615','Opérateur','Système','operator',1,'2025-07-06 13:31:38','2025-07-22 10:14:47',1,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}',NULL,NULL),(14,'viewer','viewer@ntp-monitor.local','pbkdf2:sha256:600000$J77HpMUQb0RUE2hS$08f9f7f0d3c856796c1bfc995ff625888e15634cb9fb877de6914a3ced3083e2','Visualiseur','Système','viewer',1,'2025-07-15 19:09:08','2025-07-22 10:20:14',1,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}',NULL,NULL),(15,'admin','admin@ntp-monitor.local','pbkdf2:sha256:600000$WTh5KTS7wgr4jiOd$7f2ab19badecab6783f854d3c906ffdc579d971a931622c5d09198b3bb20a0f5','Administrateur','Système','admin',1,'2025-07-19 10:41:56','2025-08-06 20:52:51',223,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}',NULL,NULL),(18,'investech-op','investeches-op@investech.com','pbkdf2:sha256:600000$XgJPM19U6cS1DAb7$79d553ba26b3561c02e3329d1f5ed6927ed4d13831b6088cac17ba4d9440f686','Investech','Operatores','viewer',0,'2025-07-19 10:44:37','2025-07-19 10:45:27',1,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}','2025-07-25 21:46:55',15),(19,'iser.resr','iser.resr@invesviz.com','pbkdf2:sha256:600000$wrzab86HuRZlCdTj$93655900e27e98c866beabff16bfa1baaab6a8a776d4c20adac980f681818a91','user','test','operator',0,'2025-07-22 07:06:38',NULL,0,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}','2025-07-22 10:17:51',15),(20,'test_user_1753169502','test_user_1753169502@test.com','pbkdf2:sha256:600000$RR6BGVweDig7k5FN$bf62da9018e13073d30da69ab9db26009e1d0945f7c5c619c943653c3b4ed3ff',NULL,NULL,'viewer',0,'2025-07-22 07:31:43',NULL,0,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}','2025-07-22 07:31:43',15),(21,'new.viewer','new.viewer@test.com','pbkdf2:sha256:600000$8mvPiu9n0GEATSJQ$202cfd2bd7b50761c16d61bde9665bba47c7098d37ffd5869e107cef334d40e6','New','Viewer','viewer',0,'2025-07-24 14:57:22','2025-07-24 15:04:00',1,'{\"theme\": \"light\", \"language\": \"fr\", \"auto_refresh\": true, \"notifications\": true, \"refresh_interval\": 30}','2025-07-24 15:05:54',15);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
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
