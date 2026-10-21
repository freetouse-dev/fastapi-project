-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: project_management
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.20.04.1

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
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('f69a3b2c4e5d');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `actor_id` int DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `resource_id` varchar(100) NOT NULL,
  `details` text,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_id` (`id`),
  KEY `ix_audit_logs_actor_id` (`actor_id`),
  KEY `ix_audit_logs_action` (`action`),
  KEY `ix_audit_logs_resource_type` (`resource_type`),
  KEY `ix_audit_logs_resource_id` (`resource_id`),
  KEY `ix_audit_logs_created_at` (`created_at`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,1,'COMMENT_CREATED','COMMENT','3','{\"task_id\": 5, \"content_length\": 116}',NULL,'2026-10-20 13:22:59'),(2,1,'COMMENT_DELETED','COMMENT','3','{\"task_id\": 5}',NULL,'2026-10-20 13:23:23'),(3,1,'COMMENT_CREATED','COMMENT','4','{\"task_id\": 5, \"content_length\": 116}',NULL,'2026-10-20 13:24:25'),(4,1,'WORKSPACE_MEMBER_ADDED','MEMBERSHIP','1:12','{\"workspace_id\": 1, \"user_id\": 12, \"role\": \"ADMIN\"}',NULL,'2026-10-20 13:31:43'),(5,1,'PROJECT_MEMBER_ADDED','MEMBERSHIP','proj_1:12','{\"project_id\": 1, \"user_id\": 12, \"role\": \"CONTRIBUTOR\"}',NULL,'2026-10-20 13:32:15'),(6,12,'TASK_UPDATED','TASK','5','{\"ticket_key\": \"MOB-4\", \"changes\": {\"status\": \"TaskStatus.IN_REVIEW\"}}',NULL,'2026-10-20 13:32:33'),(7,12,'TASK_UPDATED','TASK','3','{\"ticket_key\": \"MOB-3\", \"changes\": {\"status\": \"TaskStatus.IN_PROGRESS\"}}',NULL,'2026-10-20 13:34:20'),(8,12,'TASK_UPDATED','TASK','3','{\"ticket_key\": \"MOB-3\", \"changes\": {\"status\": \"TaskStatus.IN_REVIEW\"}}',NULL,'2026-10-20 13:48:03'),(9,12,'COMMENT_CREATED','COMMENT','5','{\"task_id\": 1, \"content_length\": 43}',NULL,'2026-10-20 13:48:44'),(10,13,'SUPERUSER_CREATED_CLI','USER','13','{\"email\": \"clisuper@example.com\", \"method\": \"CLI\"}',NULL,'2026-10-20 16:17:55'),(11,1,'USER_AVATAR_UPDATED','USER','1','{\"file_size\": 246209, \"mime_type\": \"image/jpeg\"}',NULL,'2026-10-20 17:28:48'),(12,1,'USER_AVATAR_REMOVED','USER','1','{}',NULL,'2026-10-20 17:29:24'),(13,1,'USER_AVATAR_UPDATED','USER','1','{\"file_size\": 246209, \"mime_type\": \"image/jpeg\"}',NULL,'2026-10-20 17:29:31'),(14,14,'SUPERUSER_PROMOTED_CLI','USER','14','{\"email\": \"kevins@10timer.com\", \"method\": \"CLI\"}',NULL,'2026-10-20 19:26:36'),(15,15,'COMPANY_CREATION_REQUESTED','COMPANY_REQUEST','0','{\"company_name\": \"Health Care Academy\", \"company_slug\": \"health-care-academy\"}',NULL,'2026-10-20 19:45:31'),(16,14,'COMPANY_REQUEST_APPROVED','COMPANY_REQUEST','1','{\"company_id\": 7, \"approved_user_id\": 15}',NULL,'2026-10-20 19:46:19'),(17,14,'COMPANY_CREATED','COMPANY','7','{\"name\": \"Health Care Academy\", \"slug\": \"health-care-academy\", \"owner_id\": 15}',NULL,'2026-10-20 19:46:19'),(18,15,'COMPANY_INVITATION_CREATED','COMPANY_INVITATION','0','{\"company_id\": 7, \"email\": \"john@gmail.com\", \"role\": \"MEMBER\"}',NULL,'2026-10-20 19:47:15'),(19,7,'COMPANY_CREATION_REQUESTED','COMPANY_REQUEST','0','{\"company_name\": \"New Org\", \"company_slug\": \"new-org\"}',NULL,'2026-10-20 20:06:57'),(20,14,'COMPANY_REQUEST_APPROVED','COMPANY_REQUEST','2','{\"company_id\": 8, \"approved_user_id\": 7}',NULL,'2026-10-20 20:07:39'),(21,14,'COMPANY_CREATED','COMPANY','8','{\"name\": \"New Org\", \"slug\": \"new-org\", \"owner_id\": 7}',NULL,'2026-10-20 20:07:39');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comment_attachments`
--

DROP TABLE IF EXISTS `comment_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comment_attachments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `comment_id` int NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `storage_key` varchar(255) NOT NULL,
  `mime_type` varchar(100) NOT NULL,
  `file_size` int NOT NULL,
  `uploaded_by_id` int NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_comment_attachments_storage_key` (`storage_key`),
  KEY `deleted_by_id` (`deleted_by_id`),
  KEY `ix_comment_attachments_id` (`id`),
  KEY `ix_comment_attachments_comment_id` (`comment_id`),
  KEY `ix_comment_attachments_uploaded_by_id` (`uploaded_by_id`),
  KEY `ix_comment_attachments_deleted_at` (`deleted_at`),
  CONSTRAINT `comment_attachments_ibfk_1` FOREIGN KEY (`comment_id`) REFERENCES `task_comments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comment_attachments_ibfk_2` FOREIGN KEY (`uploaded_by_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `comment_attachments_ibfk_3` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment_attachments`
--

LOCK TABLES `comment_attachments` WRITE;
/*!40000 ALTER TABLE `comment_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `comment_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `companies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `status` enum('ACTIVE','SUSPENDED','PENDING_APPROVAL') NOT NULL DEFAULT 'ACTIVE',
  `owner_id` int NOT NULL,
  `created_by_id` int NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_companies_slug` (`slug`),
  KEY `owner_id` (`owner_id`),
  KEY `created_by_id` (`created_by_id`),
  KEY `deleted_by_id` (`deleted_by_id`),
  KEY `ix_companies_id` (`id`),
  KEY `ix_companies_deleted_at` (`deleted_at`),
  CONSTRAINT `companies_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `companies_ibfk_2` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `companies_ibfk_3` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `companies`
--

LOCK TABLES `companies` WRITE;
/*!40000 ALTER TABLE `companies` DISABLE KEYS */;
INSERT INTO `companies` VALUES (1,'Alice engineering Corp','alice-engineering-corp','Company organization for Alice engineering','ACTIVE',1,1,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(2,'Bob Engineering Corp','bob-engineering-corp','Company organization for Bob Engineering','ACTIVE',2,2,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(3,'Acme Engineering Corp','acme-engineering-corp','Company organization for Acme Engineering','ACTIVE',4,4,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(4,'Studio green Corp','studio-green-corp','Company organization for Studio green','ACTIVE',3,3,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(5,'Skullcade marks Corp','skullcade-marks-corp','Company organization for Skullcade marks','ACTIVE',5,5,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(6,'GrowthLab Marketing Corp','growthLab-marketing-corp','Company organization for GrowthLab Marketing','ACTIVE',6,6,NULL,NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11'),(7,'Health Care Academy','health-care-academy',NULL,'ACTIVE',15,14,NULL,NULL,'2026-10-20 19:46:19','2026-10-20 19:46:19'),(8,'New Org','new-org',NULL,'ACTIVE',7,14,NULL,NULL,'2026-10-20 20:07:39','2026-10-20 20:07:39');
/*!40000 ALTER TABLE `companies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `company_creation_requests`
--

DROP TABLE IF EXISTS `company_creation_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company_creation_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `company_name` varchar(100) NOT NULL,
  `company_slug` varchar(100) NOT NULL,
  `business_description` varchar(500) DEFAULT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'PENDING',
  `reviewed_by_id` int DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `rejection_reason` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `reviewed_by_id` (`reviewed_by_id`),
  KEY `ix_company_creation_requests_id` (`id`),
  KEY `ix_company_creation_requests_user_id` (`user_id`),
  KEY `ix_company_creation_requests_company_slug` (`company_slug`),
  KEY `ix_company_creation_requests_status` (`status`),
  CONSTRAINT `company_creation_requests_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `company_creation_requests_ibfk_2` FOREIGN KEY (`reviewed_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `company_creation_requests`
--

LOCK TABLES `company_creation_requests` WRITE;
/*!40000 ALTER TABLE `company_creation_requests` DISABLE KEYS */;
INSERT INTO `company_creation_requests` VALUES (1,15,'Health Care Academy','health-care-academy',NULL,'APPROVED',14,'2026-10-20 14:16:20',NULL,'2026-10-20 19:45:31'),(2,7,'New Org','new-org',NULL,'APPROVED',14,'2026-10-20 14:37:39',NULL,'2026-10-20 20:06:57');
/*!40000 ALTER TABLE `company_creation_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `company_invitations`
--

DROP TABLE IF EXISTS `company_invitations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company_invitations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `role` enum('COMPANY_OWNER','COMPANY_ADMIN','MEMBER','VIEWER') NOT NULL DEFAULT 'MEMBER',
  `token_hash` varchar(255) NOT NULL,
  `invited_by_id` int NOT NULL,
  `status` varchar(50) NOT NULL DEFAULT 'PENDING',
  `expires_at` datetime NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_company_invitations_token_hash` (`token_hash`),
  KEY `invited_by_id` (`invited_by_id`),
  KEY `ix_company_invitations_id` (`id`),
  KEY `ix_company_invitations_company_id` (`company_id`),
  KEY `ix_company_invitations_email` (`email`),
  KEY `ix_company_invitations_status` (`status`),
  CONSTRAINT `company_invitations_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `company_invitations_ibfk_2` FOREIGN KEY (`invited_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `company_invitations`
--

LOCK TABLES `company_invitations` WRITE;
/*!40000 ALTER TABLE `company_invitations` DISABLE KEYS */;
INSERT INTO `company_invitations` VALUES (1,7,'john@gmail.com','MEMBER','43810d4c486212f35ae5e36ac08aa6d515d26d3727cc698d020e63ad4e1697eb',15,'PENDING','2026-10-27 14:17:15','2026-10-20 19:47:15');
/*!40000 ALTER TABLE `company_invitations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `company_members`
--

DROP TABLE IF EXISTS `company_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `company_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` enum('COMPANY_OWNER','COMPANY_ADMIN','MEMBER','VIEWER') NOT NULL DEFAULT 'MEMBER',
  `status` varchar(50) NOT NULL DEFAULT 'ACTIVE',
  `invited_by_id` int DEFAULT NULL,
  `joined_at` datetime NOT NULL DEFAULT (now()),
  `created_at` datetime NOT NULL DEFAULT (now()),
  `can_create_workspace` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_company_user` (`company_id`,`user_id`),
  KEY `invited_by_id` (`invited_by_id`),
  KEY `ix_company_members_id` (`id`),
  KEY `ix_company_members_company_id` (`company_id`),
  KEY `ix_company_members_user_id` (`user_id`),
  CONSTRAINT `company_members_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `company_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `company_members_ibfk_3` FOREIGN KEY (`invited_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `company_members`
--

LOCK TABLES `company_members` WRITE;
/*!40000 ALTER TABLE `company_members` DISABLE KEYS */;
INSERT INTO `company_members` VALUES (1,1,1,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(2,1,4,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(3,1,5,'MEMBER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',0),(4,1,6,'MEMBER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',0),(5,1,12,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(6,2,2,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(7,3,4,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(8,4,3,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(9,4,2,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(10,2,3,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(11,5,5,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(12,5,4,'MEMBER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',0),(13,6,6,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(14,6,2,'MEMBER','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',0),(15,6,5,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(16,1,2,'COMPANY_ADMIN','ACTIVE',NULL,'2026-10-20 17:35:11','2026-10-20 17:35:11',1),(17,7,15,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 19:46:19','2026-10-20 19:46:19',1),(18,8,7,'COMPANY_OWNER','ACTIVE',NULL,'2026-10-20 20:07:39','2026-10-20 20:07:39',1);
/*!40000 ALTER TABLE `company_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_members`
--

DROP TABLE IF EXISTS `project_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` enum('PROJECT_LEAD','CONTRIBUTOR','VIEWER') NOT NULL,
  `joined_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_project_user` (`project_id`,`user_id`),
  KEY `user_id` (`user_id`),
  KEY `ix_project_members_id` (`id`),
  CONSTRAINT `project_members_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `project_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_members`
--

LOCK TABLES `project_members` WRITE;
/*!40000 ALTER TABLE `project_members` DISABLE KEYS */;
INSERT INTO `project_members` VALUES (1,1,4,'PROJECT_LEAD','2026-10-15 17:50:30'),(2,2,5,'PROJECT_LEAD','2026-10-15 18:04:02'),(3,1,6,'CONTRIBUTOR','2026-10-15 18:54:00'),(4,3,3,'PROJECT_LEAD','2026-10-16 15:44:20'),(5,3,2,'VIEWER','2026-10-16 15:44:53'),(6,4,3,'PROJECT_LEAD','2026-10-16 15:52:42'),(7,1,12,'CONTRIBUTOR','2026-10-20 13:32:15');
/*!40000 ALTER TABLE `project_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `workspace_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `key` varchar(10) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `status` enum('ACTIVE','ARCHIVED','COMPLETED') NOT NULL,
  `created_by_id` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_workspace_project_key` (`workspace_id`,`key`),
  KEY `created_by_id` (`created_by_id`),
  KEY `ix_projects_id` (`id`),
  KEY `ix_projects_key` (`key`),
  KEY `ix_projects_workspace_id` (`workspace_id`),
  KEY `ix_projects_deleted_at` (`deleted_at`),
  KEY `fk_projects_deleted_by` (`deleted_by_id`),
  CONSTRAINT `fk_projects_deleted_by` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `projects_ibfk_1` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `projects_ibfk_2` FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projects`
--

LOCK TABLES `projects` WRITE;
/*!40000 ALTER TABLE `projects` DISABLE KEYS */;
INSERT INTO `projects` VALUES (1,1,'Dashboard Redesign','MOB','Redesign the application dashboard to improve usability, simplify navigation, display relevant metrics, and provide a consistent responsive experience.','ACTIVE',4,'2026-10-15 17:50:30','2026-10-15 17:50:30',NULL,NULL),(2,9,'Mobile Application','MOB','iOS and Android client development','ACTIVE',5,'2026-10-15 18:04:02','2026-10-15 18:04:02',NULL,NULL),(3,4,'Lavanya','LAVA',NULL,'ACTIVE',3,'2026-10-16 15:44:20','2026-10-16 15:44:20',NULL,NULL),(4,6,'ThrieveCart','THRIVECART',NULL,'ACTIVE',3,'2026-10-16 15:52:42','2026-10-16 15:52:42',NULL,NULL);
/*!40000 ALTER TABLE `projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task_activities`
--

DROP TABLE IF EXISTS `task_activities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_activities` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` int NOT NULL,
  `actor_id` int NOT NULL,
  `action` enum('TASK_CREATED','STATUS_CHANGED','PRIORITY_CHANGED','ASSIGNEE_CHANGED','TITLE_CHANGED','DESCRIPTION_CHANGED','DUE_DATE_CHANGED') NOT NULL,
  `field_name` varchar(50) DEFAULT NULL,
  `old_value` text,
  `new_value` text,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_task_activities_actor_id` (`actor_id`),
  KEY `ix_task_activities_id` (`id`),
  KEY `ix_task_activities_task_id` (`task_id`),
  CONSTRAINT `task_activities_ibfk_1` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `task_activities_ibfk_2` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_activities`
--

LOCK TABLES `task_activities` WRITE;
/*!40000 ALTER TABLE `task_activities` DISABLE KEYS */;
INSERT INTO `task_activities` VALUES (1,5,1,'TASK_CREATED',NULL,NULL,'Audit Trail Feature Test','2026-10-16 16:13:29'),(2,5,1,'STATUS_CHANGED','status','TODO','IN_PROGRESS','2026-10-16 16:13:38'),(3,5,1,'PRIORITY_CHANGED','priority','MEDIUM','URGENT','2026-10-16 16:13:38'),(4,1,1,'STATUS_CHANGED','status','IN_PROGRESS','DONE','2026-10-16 16:29:13'),(5,5,12,'STATUS_CHANGED','status','IN_PROGRESS','IN_REVIEW','2026-10-20 13:32:33'),(6,3,12,'STATUS_CHANGED','status','TODO','IN_PROGRESS','2026-10-20 13:34:20'),(7,3,12,'STATUS_CHANGED','status','IN_PROGRESS','IN_REVIEW','2026-10-20 13:48:03');
/*!40000 ALTER TABLE `task_activities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task_comments`
--

DROP TABLE IF EXISTS `task_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `task_id` int NOT NULL,
  `author_id` int NOT NULL,
  `content` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_task_comments_author_id` (`author_id`),
  KEY `ix_task_comments_id` (`id`),
  KEY `ix_task_comments_task_id` (`task_id`),
  KEY `ix_task_comments_deleted_at` (`deleted_at`),
  KEY `fk_task_comments_deleted_by` (`deleted_by_id`),
  CONSTRAINT `fk_task_comments_deleted_by` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `task_comments_ibfk_1` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `task_comments_ibfk_2` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task_comments`
--

LOCK TABLES `task_comments` WRITE;
/*!40000 ALTER TABLE `task_comments` DISABLE KEYS */;
INSERT INTO `task_comments` VALUES (2,1,1,'I have created the Google Developer Console project and credentials. Working on the iOS callback.','2026-10-16 16:02:41','2026-10-16 16:02:41',NULL,NULL),(3,5,1,'I have complete the audit trail test with workspace and task functionalities. Need to move on task based audit test.','2026-10-20 13:22:59','2026-10-20 13:23:23','2026-10-20 07:53:24',1),(4,5,1,'I have complete the audit trail test with workspace and task functionalities. Need to move on task based audit test.','2026-10-20 13:24:25','2026-10-20 13:24:25',NULL,NULL),(5,1,12,'I was testing the whole application wokflow','2026-10-20 13:48:44','2026-10-20 13:48:44',NULL,NULL);
/*!40000 ALTER TABLE `task_comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `task_number` int NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text,
  `status` enum('BACKLOG','TODO','IN_PROGRESS','IN_REVIEW','DONE','CANCELLED') NOT NULL,
  `priority` enum('LOW','MEDIUM','HIGH','URGENT') NOT NULL,
  `creator_id` int NOT NULL,
  `assignee_id` int DEFAULT NULL,
  `due_date` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_project_task_number` (`project_id`,`task_number`),
  KEY `creator_id` (`creator_id`),
  KEY `ix_tasks_assignee_id` (`assignee_id`),
  KEY `ix_tasks_id` (`id`),
  KEY `ix_tasks_priority` (`priority`),
  KEY `ix_tasks_project_id` (`project_id`),
  KEY `ix_tasks_status` (`status`),
  KEY `ix_tasks_deleted_at` (`deleted_at`),
  KEY `fk_tasks_deleted_by` (`deleted_by_id`),
  CONSTRAINT `fk_tasks_deleted_by` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`assignee_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `tasks_ibfk_2` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `tasks_ibfk_3` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
INSERT INTO `tasks` VALUES (1,1,1,'Setup OAuth2 Login with Google','Implement social login on iOS and Android','DONE','HIGH',1,NULL,NULL,'2026-10-16 13:25:37','2026-10-16 16:29:13',NULL,NULL),(2,1,2,'Design Profile Settings UI',NULL,'TODO','MEDIUM',1,NULL,NULL,'2026-10-16 13:26:54','2026-10-16 13:26:54',NULL,NULL),(3,1,3,'Implement Email service','Need to implement an email service when the user register in our application','IN_REVIEW','LOW',1,6,'2026-10-24 00:00:00','2026-10-16 15:41:10','2026-10-20 13:48:03',NULL,NULL),(4,3,1,'Urgent Task','Issue in production','IN_PROGRESS','URGENT',3,2,'2026-10-17 00:00:00','2026-10-16 15:45:44','2026-10-16 15:46:49',NULL,NULL),(5,1,4,'Audit Trail Feature Test',NULL,'IN_REVIEW','URGENT',1,NULL,NULL,'2026-10-16 16:13:29','2026-10-20 13:32:33',NULL,NULL);
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_otps`
--

DROP TABLE IF EXISTS `user_otps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_otps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `hashed_otp` varchar(255) NOT NULL,
  `purpose` enum('EMAIL_VERIFICATION','PASSWORD_RESET') NOT NULL,
  `expires_at` datetime NOT NULL,
  `attempts` int NOT NULL,
  `is_used` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_user_otps_id` (`id`),
  KEY `ix_user_otps_purpose` (`purpose`),
  KEY `ix_user_otps_user_id` (`user_id`),
  CONSTRAINT `user_otps_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_otps`
--

LOCK TABLES `user_otps` WRITE;
/*!40000 ALTER TABLE `user_otps` DISABLE KEYS */;
INSERT INTO `user_otps` VALUES (1,7,'6b3c5572c5ddf29d4649562975f322e8a499c90a5d86f5bab771aa6d25515a78','EMAIL_VERIFICATION','2026-10-16 13:28:26',0,0,'2026-10-16 18:48:26'),(3,9,'4a115abc38531fecaa5f11f1c306ae5770f2811064af3cb1712724ff873a46b3','EMAIL_VERIFICATION','2026-10-16 13:41:25',1,1,'2026-10-16 19:01:24'),(4,9,'70cf3011421c17690c332cae80976137de8f0027eed5404ecc9c5afe6684e2ea','PASSWORD_RESET','2026-10-16 13:42:35',0,0,'2026-10-16 19:02:35'),(5,10,'e5054c274cc23d0213e885cafa901e129068d4bb6fc62c805c752fb592161a50','EMAIL_VERIFICATION','2026-10-16 13:45:36',1,1,'2026-10-16 19:05:36'),(6,10,'134f763bc0072de1075b9fd9e9355014325a6b9736c2e9afcefffc03300418fd','PASSWORD_RESET','2026-10-16 13:46:16',1,1,'2026-10-16 19:06:16'),(7,1,'e96fd467d64090c65ff9033fb8db92b859a5706190d46bd456d288ba1cb89e0a','EMAIL_VERIFICATION','2026-10-16 13:50:34',0,1,'2026-10-16 19:10:34'),(8,1,'f8dabb53bb0acdbb930b2a6b965ea4063a409acea33a8268a6358d1c11e4899d','EMAIL_VERIFICATION','2026-10-16 13:51:54',1,1,'2026-10-16 19:11:53'),(9,1,'1c40f76dde8ad77fa88197dc32cea47e000b52de689a8768442e9a340ac74640','PASSWORD_RESET','2026-10-20 06:49:30',1,1,'2026-10-20 12:09:29'),(10,11,'d7bd89d9047c16797ac1886737a180a794dcbb8c0556614df40fc73c9a3f2056','EMAIL_VERIFICATION','2026-10-20 07:07:40',0,0,'2026-10-20 12:27:39'),(11,12,'8be6793f568de1ef874f2ac596d695240c6098498cef2adf35878f77d01c8bd1','EMAIL_VERIFICATION','2026-10-20 08:09:56',1,1,'2026-10-20 13:29:56'),(12,14,'baff0e89b43f3158cfafbf42a39575deb4b78f2b113b959527472f28c5248166','EMAIL_VERIFICATION','2026-10-20 13:59:13',1,1,'2026-10-20 19:19:12'),(13,15,'fb4ab79e07dc2b761c22b89b23f326e3c4703dc33a9d3782d609493da9eaf585','EMAIL_VERIFICATION','2026-10-20 14:24:03',0,0,'2026-10-20 19:44:03'),(15,7,'66e94c861effda765332dc561623b17454e49110e26ab12ad2bda94b108ffbc7','PASSWORD_RESET','2026-10-20 14:41:51',1,1,'2026-10-20 20:01:51'),(16,16,'5584f4e7d7cfae75290db867cd1f13e0b2ed39cd83b848ac746cc63542db1152','EMAIL_VERIFICATION','2026-10-20 15:31:37',1,1,'2026-10-20 20:51:36');
/*!40000 ALTER TABLE `user_otps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `is_verified` tinyint(1) NOT NULL,
  `avatar_storage_key` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admins@10timer.com','Admin','$2b$12$CAXP4ceEWs/Urmr1V9/mZ.McU4xdffz4j6unTJjkdQLezfo5vooSa',1,0,'2026-10-14 12:26:13','2026-10-20 17:29:31',1,'avatars/112f88f0a8c8496fb29e9ff2028b038e.jpg'),(2,'ajay@gmail.com','Ajay','$2b$12$1Rhvuzg2rmPr/FYdWuWzGuWhCQu8gpXHJe0b5Tjrgqk8.ybV8bvSi',1,0,'2026-10-14 12:26:29','2026-10-14 12:26:29',0,NULL),(3,'lavanya@example.com','Lavanya','$2b$12$3FQiBuSXQ1z0rEhP90rwluUksK7oot5C4y5P0YrKs5HYzhoOkyFSK',1,0,'2026-10-14 19:56:09','2026-10-14 19:56:09',0,NULL),(4,'sam@gmail.com','Sam','$2b$12$HAApsK2xjvUS4zMagGEDvOak7Hx37V1mh/6cuTn8k70xGtxIG5bZu',1,0,'2026-10-14 19:56:39','2026-10-14 19:56:39',0,NULL),(5,'mary@gmail.com','Mary','$2b$12$6PgViRrrDySWmK4.BrnPl.jGwDu.ganLMUNDP9gpfWneRSCdW9xw2',1,0,'2026-10-15 16:17:02','2026-10-15 16:17:02',0,NULL),(6,'john@gmail.com','john','$2b$12$wP6nSqvwMpoWb0AtTHUj.OKdQhC.AyB6ReYxAh8OELJo2SgK6apOO',1,0,'2026-10-15 18:01:01','2026-10-15 18:01:01',0,NULL),(7,'davids@10timer.com','David','$2b$12$5hzTM9ngFi.10ylhXvB3e.1pY.U9TOLacuXeCI7Kckbxq0JdaIAFu',1,0,'2026-10-16 18:48:25','2026-10-20 20:03:17',1,NULL),(9,'babema7208@iconcubic.com','Babema','$2b$12$yp1eNx.cW6DAAA6TTb0ENe127pVtnNuFpXJFR74HPBRioJO.ZqiKC',1,0,'2026-10-16 19:01:24','2026-10-16 19:01:52',1,NULL),(10,'gnmqwl04225@smaau.com','Karan','$2b$12$aDSZPyRjUWNk3Mk7ag5ufeQQIR7smzH46IyeYSDV4vXSLPmSbNlc2',1,0,'2026-10-16 19:05:36','2026-10-16 19:06:35',1,NULL),(11,'ajayraj.b@mitrahsoft.in','Ajayraj','$2b$12$R/PtjbicdIABOuBvcFCcr.0TGvVV.liWCiHWJO8U/rZOkjHISIxfq',1,0,'2026-10-20 12:27:39','2026-10-20 12:27:39',0,NULL),(12,'lavanyacrush@litedl.com','Lavanya sri','$2b$12$tRQXfUGVezw1bUiM3skrHOVjHLmhVU.Zzb9IixPrgNMX66/U6npOK',1,0,'2026-10-20 13:29:56','2026-10-20 13:30:13',1,NULL),(13,'clisuper@example.com','CLI Administrator','$2b$12$b3ya9K82GEeL.9NQ4L.Js.cBKZzN4IAOrdDfuGcdk07NH0B.BuxqW',1,1,'2026-10-20 16:17:55','2026-10-20 16:17:55',1,NULL),(14,'kevins@10timer.com','Kevin','$2b$12$fndXfxZd649abT9.G1fP2O0w7KEScTG1miBbBn//MTJTxfp1vx80S',1,1,'2026-10-20 19:19:12','2026-10-20 19:26:36',1,NULL),(15,'jegan@gmail.com','Jegan','$2b$12$Uo01bE1dkyJwH0KGMxOB7eP1CkhwdDQtflJl28nNVDXTz/NdqnjBC',1,0,'2026-10-20 19:44:03','2026-10-20 19:44:03',1,NULL),(16,'srikrishna@10timer.com','srikrishna','$2b$12$0tsST.N1o5RyDU.LXtWxDO3gMO7PvDdyLS33Jw5w01Qnq0LF1h8ua',1,0,'2026-10-20 20:51:36','2026-10-20 20:51:47',1,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workspace_access_requests`
--

DROP TABLE IF EXISTS `workspace_access_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workspace_access_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `user_id` int NOT NULL,
  `request_type` enum('CREATE_WORKSPACE','JOIN_WORKSPACE') NOT NULL DEFAULT 'CREATE_WORKSPACE',
  `workspace_id` int DEFAULT NULL,
  `requested_role` varchar(50) DEFAULT NULL,
  `reason` varchar(500) DEFAULT NULL,
  `status` enum('PENDING','APPROVED','REJECTED','CANCELLED') NOT NULL DEFAULT 'PENDING',
  `reviewer_id` int DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `decision_reason` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `reviewer_id` (`reviewer_id`),
  KEY `ix_workspace_access_requests_id` (`id`),
  KEY `ix_workspace_access_requests_company_id` (`company_id`),
  KEY `ix_workspace_access_requests_user_id` (`user_id`),
  KEY `ix_workspace_access_requests_workspace_id` (`workspace_id`),
  KEY `ix_workspace_access_requests_status` (`status`),
  CONSTRAINT `workspace_access_requests_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workspace_access_requests_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workspace_access_requests_ibfk_3` FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workspace_access_requests_ibfk_4` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workspace_access_requests`
--

LOCK TABLES `workspace_access_requests` WRITE;
/*!40000 ALTER TABLE `workspace_access_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `workspace_access_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workspace_members`
--

DROP TABLE IF EXISTS `workspace_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workspace_members` (
  `id` int NOT NULL AUTO_INCREMENT,
  `workspace_id` int NOT NULL,
  `user_id` int NOT NULL,
  `role` enum('OWNER','ADMIN','MEMBER') NOT NULL,
  `joined_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_workspace_user` (`workspace_id`,`user_id`),
  KEY `user_id` (`user_id`),
  KEY `ix_workspace_members_id` (`id`),
  CONSTRAINT `workspace_members_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workspace_members_ibfk_2` FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workspace_members`
--

LOCK TABLES `workspace_members` WRITE;
/*!40000 ALTER TABLE `workspace_members` DISABLE KEYS */;
INSERT INTO `workspace_members` VALUES (1,1,1,'OWNER','2026-10-14 17:54:44'),(2,2,2,'OWNER','2026-10-14 18:00:19'),(3,3,4,'OWNER','2026-10-14 20:10:58'),(4,4,3,'OWNER','2026-10-14 20:13:54'),(5,5,3,'OWNER','2026-10-14 20:16:38'),(6,5,2,'MEMBER','2026-10-15 12:50:05'),(7,4,2,'ADMIN','2026-10-15 13:15:23'),(8,6,2,'OWNER','2026-10-15 13:55:41'),(9,6,3,'ADMIN','2026-10-15 13:55:58'),(10,7,5,'OWNER','2026-10-15 16:19:36'),(11,8,5,'OWNER','2026-10-15 16:33:58'),(12,8,4,'MEMBER','2026-10-15 16:34:31'),(13,1,4,'ADMIN','2026-10-15 17:50:25'),(14,1,5,'MEMBER','2026-10-15 17:57:23'),(15,9,6,'OWNER','2026-10-15 18:02:09'),(16,9,5,'ADMIN','2026-10-15 18:02:39'),(17,9,2,'MEMBER','2026-10-15 18:08:01'),(18,1,6,'MEMBER','2026-10-15 18:53:48'),(19,10,1,'OWNER','2026-10-15 18:55:38'),(20,10,2,'ADMIN','2026-10-15 18:55:50'),(21,1,12,'ADMIN','2026-10-20 13:31:43');
/*!40000 ALTER TABLE `workspace_members` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workspaces`
--

DROP TABLE IF EXISTS `workspaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workspaces` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  `description` varchar(500) DEFAULT NULL,
  `owner_id` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `deleted_by_id` int DEFAULT NULL,
  `company_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_workspaces_slug` (`slug`),
  KEY `owner_id` (`owner_id`),
  KEY `ix_workspaces_id` (`id`),
  KEY `ix_workspaces_deleted_at` (`deleted_at`),
  KEY `fk_workspaces_deleted_by` (`deleted_by_id`),
  KEY `ix_workspaces_company_id` (`company_id`),
  CONSTRAINT `fk_workspaces_company_id` FOREIGN KEY (`company_id`) REFERENCES `companies` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workspaces_deleted_by` FOREIGN KEY (`deleted_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `workspaces_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workspaces`
--

LOCK TABLES `workspaces` WRITE;
/*!40000 ALTER TABLE `workspaces` DISABLE KEYS */;
INSERT INTO `workspaces` VALUES (1,'Alice engineering','alice-engineering','Core engineering workspace',1,'2026-10-14 17:54:44','2026-10-14 17:54:44',NULL,NULL,1),(2,'Bob Engineering','bob-engineering','Modern core engineering workspace',2,'2026-10-14 18:00:19','2026-10-14 18:00:19',NULL,NULL,2),(3,'Acme Engineering','acme-engineering','Core engineering workspace',4,'2026-10-14 20:10:58','2026-10-14 20:10:58',NULL,NULL,3),(4,'Studio green','studio-green','Majorly worked on cinema field',3,'2026-10-14 20:13:54','2026-10-14 20:13:54',NULL,NULL,4),(5,'Polo grade','polo-grade','Senior citizen membership for sports',3,'2026-10-14 20:16:38','2026-10-14 20:16:38',NULL,NULL,4),(6,'Panther Academy','panther-academy','It was sport based academy for under 17-19 players.',2,'2026-10-15 13:55:41','2026-10-15 13:55:41',NULL,NULL,2),(7,'Skullcade marks','skullcade-marks','This is testing company that performs manual and automation testing.',5,'2026-10-15 16:19:36','2026-10-15 16:19:36',NULL,NULL,5),(8,'TechNova Solutions','technova-solutions','A workspace for managing software development projects, API integrations, bug fixes, and cloud infrastructure improvements for a growing technology company.',5,'2026-10-15 16:33:58','2026-10-15 16:33:58',NULL,NULL,5),(9,'GrowthLab Marketing','growthLab-marketing','A collaborative workspace for planning marketing campaigns, improving brand awareness, managing content, and tracking digital marketing performance.',6,'2026-10-15 18:02:09','2026-10-15 18:02:09',NULL,NULL,6),(10,'Operations Hub','operations-hub','A workspace for managing internal business operations, employee processes, IT support requests, documentation, and workflow automation.',1,'2026-10-15 18:55:38','2026-10-15 18:55:38',NULL,NULL,1);
/*!40000 ALTER TABLE `workspaces` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-21 11:59:32
