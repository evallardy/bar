-- MySQL dump 10.13  Distrib 8.4.8, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: bar_db
-- ------------------------------------------------------
-- Server version	8.4.8

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
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'administrador'),(2,'empleados');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add product',9,'add_product'),(26,'Can change product',9,'change_product'),(27,'Can delete product',9,'delete_product'),(28,'Can view product',9,'view_product'),(29,'Can add supply',10,'add_supply'),(30,'Can change supply',10,'change_supply'),(31,'Can delete supply',10,'delete_supply'),(32,'Can view supply',10,'view_supply'),(33,'Can add order',7,'add_order'),(34,'Can change order',7,'change_order'),(35,'Can delete order',7,'delete_order'),(36,'Can view order',7,'view_order'),(37,'Can add order item',8,'add_orderitem'),(38,'Can change order item',8,'change_orderitem'),(39,'Can delete order item',8,'delete_orderitem'),(40,'Can view order item',8,'view_orderitem'),(41,'Can add product supply',11,'add_productsupply'),(42,'Can change product supply',11,'change_productsupply'),(43,'Can delete product supply',11,'delete_productsupply'),(44,'Can view product supply',11,'view_productsupply'),(45,'Can add product variant',12,'add_productvariant'),(46,'Can change product variant',12,'change_productvariant'),(47,'Can delete product variant',12,'delete_productvariant'),(48,'Can view product variant',12,'view_productvariant'),(49,'Can add Acceso de usuario',13,'add_useraccess'),(50,'Can change Acceso de usuario',13,'change_useraccess'),(51,'Can delete Acceso de usuario',13,'delete_useraccess'),(52,'Can view Acceso de usuario',13,'view_useraccess'),(53,'Can add work day',14,'add_workday'),(54,'Can change work day',14,'change_workday'),(55,'Can delete work day',14,'delete_workday'),(56,'Can view work day',14,'view_workday'),(57,'Can add order payment',16,'add_orderpayment'),(58,'Can change order payment',16,'change_orderpayment'),(59,'Can delete order payment',16,'delete_orderpayment'),(60,'Can view order payment',16,'view_orderpayment'),(61,'Can add order item payment',15,'add_orderitempayment'),(62,'Can change order item payment',15,'change_orderitempayment'),(63,'Can delete order item payment',15,'delete_orderitempayment'),(64,'Can view order item payment',15,'view_orderitempayment');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$1200000$bYH10t9Bvdr4oKFwJKN0WA$Z/qkNlkbtYjatvfqp+slgaskKYZqwJYbikCgvFQ4DhQ=','2026-05-02 01:15:40.482304',1,'admin','','','admin@bar.local',1,1,'2026-04-30 00:20:52.457270'),(2,'pbkdf2_sha256$1200000$gQ54GEzIhyW0x5MXc6ZQCU$7igoH857FvINcoLNTxwxUTCcVIGyYcb4712S9s/w72Q=','2026-05-01 06:08:08.566280',0,'victor','Victor','','',0,1,'2026-04-30 03:33:09.980585'),(3,'pbkdf2_sha256$1200000$2shEZV8TBw92pJc27p8LAU$yAVz7/5uhMha3yCo/5y71clx4/6AjWFMBaa1cPh+r7U=',NULL,0,'manu','Manuel','','',0,1,'2026-05-02 02:19:47.126089'),(5,'pbkdf2_sha256$1200000$fTI03FBdXnmbTtrxdEkxgt$2pXeK4muBixYnIcb7UXQh+5bFHENn9xeskv0G0GW6Hg=',NULL,0,'erika','Erika','','',0,1,'2026-05-02 02:21:07.554677'),(6,'pbkdf2_sha256$1200000$MAz0uotKUb00wC5M320plK$waZMV+UMjBzYeDFOz/IM0wS3K3Hxcj1FZEhMLNnkv8A=',NULL,0,'marco','Marco','','',0,1,'2026-05-02 02:21:47.252244'),(7,'pbkdf2_sha256$1200000$0c672lxV3t3dMmtc0RAlt3$GG5NL4R2+tyVMejDqpvwNgEbH/fo1rPm91oZUdN/37I=',NULL,0,'cesar','Cesar','','',0,1,'2026-05-02 02:23:23.367789');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
INSERT INTO `auth_user_groups` VALUES (1,1,1);
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_order`
--

DROP TABLE IF EXISTS `core_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_order` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `table_number` int unsigned NOT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `closed_at` datetime(6) DEFAULT NULL,
  `created_by_id` int DEFAULT NULL,
  `workday_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `core_order_created_by_id_1264a02d_fk_auth_user_id` (`created_by_id`),
  KEY `core_order_workday_id_e9570d7b_fk_core_workday_id` (`workday_id`),
  CONSTRAINT `core_order_created_by_id_1264a02d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_order_workday_id_e9570d7b_fk_core_workday_id` FOREIGN KEY (`workday_id`) REFERENCES `core_workday` (`id`),
  CONSTRAINT `core_order_chk_1` CHECK ((`table_number` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_order`
--

LOCK TABLES `core_order` WRITE;
/*!40000 ALTER TABLE `core_order` DISABLE KEYS */;
INSERT INTO `core_order` VALUES (3,1,'ABIERTA','','2026-04-30 05:40:07.812478',NULL,1,1),(4,2,'ABIERTA','','2026-04-30 06:03:45.496058',NULL,1,1),(5,99,'ABIERTA','','2026-05-01 07:03:56.221534',NULL,1,1),(6,777,'ABIERTA','','2026-05-01 07:50:44.917466',NULL,1,1);
/*!40000 ALTER TABLE `core_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_orderitem`
--

DROP TABLE IF EXISTS `core_orderitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_orderitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `diner_name` varchar(120) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `notes` varchar(255) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `order_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  `variant_id` bigint DEFAULT NULL,
  `waiter_name` varchar(120) NOT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  `paid_status` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_orderitem_order_id_30929c10_fk_core_order_id` (`order_id`),
  KEY `core_orderitem_product_id_0c2047cd_fk_core_product_id` (`product_id`),
  KEY `core_orderitem_variant_id_fc31f244_fk_core_productvariant_id` (`variant_id`),
  CONSTRAINT `core_orderitem_order_id_30929c10_fk_core_order_id` FOREIGN KEY (`order_id`) REFERENCES `core_order` (`id`),
  CONSTRAINT `core_orderitem_product_id_0c2047cd_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_orderitem_variant_id_fc31f244_fk_core_productvariant_id` FOREIGN KEY (`variant_id`) REFERENCES `core_productvariant` (`id`),
  CONSTRAINT `core_orderitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_orderitem`
--

LOCK TABLES `core_orderitem` WRITE;
/*!40000 ALTER TABLE `core_orderitem` DISABLE KEYS */;
INSERT INTO `core_orderitem` VALUES (8,'Adrian',2,80.00,'Victoria | Escarcha Miguelito, Escarcha tamarindo','ENTREGADO','2026-04-30 05:40:07.829950',3,3,2,'',NULL,'PAGADO'),(9,'Roberto',1,120.00,'Hawiana','ENTREGADO','2026-04-30 05:40:07.843688',3,5,5,'',NULL,'PAGADO'),(10,'Ricardo',1,85.00,'Cebolla, Queso amarillo','ENTREGADO','2026-04-30 06:03:45.505112',4,6,NULL,'',NULL,'PAGADO'),(11,'Roberto',1,120.00,'Hawiana','ENTREGADO','2026-04-30 06:03:45.521107',4,5,5,'',NULL,'PAGADO'),(12,'Roberto',1,80.00,'Victoria','ENTREGADO','2026-04-30 06:16:28.619397',4,3,2,'',NULL,'PAGADO'),(13,'Roberto',1,80.00,'Victoria | Escarcha tamarindo','ENTREGADO','2026-04-30 06:22:19.481077',3,3,2,'',NULL,'PAGADO'),(14,'Prueba',1,80.00,'','ENTREGADO','2026-05-01 07:03:56.225618',5,3,NULL,'',NULL,'PAGADO'),(15,'',1,10.00,'','EN_PREPARACION','2026-05-01 07:50:44.921942',6,6,NULL,'','2026-05-01 07:50:44.926570','PAGADO'),(16,'Roberto',1,80.00,'Corona','COMANDADO','2026-05-01 07:53:16.067731',3,3,3,'',NULL,'NO_PAGADO');
/*!40000 ALTER TABLE `core_orderitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_orderitempayment`
--

DROP TABLE IF EXISTS `core_orderitempayment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_orderitempayment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(10,2) NOT NULL,
  `order_item_id` bigint NOT NULL,
  `payment_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_payment_order_item` (`payment_id`,`order_item_id`),
  UNIQUE KEY `unique_paid_order_item` (`order_item_id`),
  CONSTRAINT `core_orderitempaymen_order_item_id_375951fd_fk_core_orde` FOREIGN KEY (`order_item_id`) REFERENCES `core_orderitem` (`id`),
  CONSTRAINT `core_orderitempaymen_payment_id_ef2a8d05_fk_core_orde` FOREIGN KEY (`payment_id`) REFERENCES `core_orderpayment` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_orderitempayment`
--

LOCK TABLES `core_orderitempayment` WRITE;
/*!40000 ALTER TABLE `core_orderitempayment` DISABLE KEYS */;
INSERT INTO `core_orderitempayment` VALUES (1,85.00,10,1),(2,120.00,11,1),(3,80.00,12,2),(4,160.00,8,3),(5,80.00,13,4),(6,120.00,9,5),(7,80.00,14,6),(8,10.00,15,7);
/*!40000 ALTER TABLE `core_orderitempayment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_orderpayment`
--

DROP TABLE IF EXISTS `core_orderpayment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_orderpayment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `cash_amount` decimal(10,2) NOT NULL,
  `card_amount` decimal(10,2) NOT NULL,
  `transfer_amount` decimal(10,2) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `order_id` bigint NOT NULL,
  `workday_id` bigint DEFAULT NULL,
  `card_evidence` varchar(100) NOT NULL,
  `transfer_evidence` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_orderpayment_created_by_id_d837f992_fk_auth_user_id` (`created_by_id`),
  KEY `core_orderpayment_order_id_312ea6c0_fk_core_order_id` (`order_id`),
  KEY `core_orderpayment_workday_id_e52ae3de_fk_core_workday_id` (`workday_id`),
  CONSTRAINT `core_orderpayment_created_by_id_d837f992_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_orderpayment_order_id_312ea6c0_fk_core_order_id` FOREIGN KEY (`order_id`) REFERENCES `core_order` (`id`),
  CONSTRAINT `core_orderpayment_workday_id_e52ae3de_fk_core_workday_id` FOREIGN KEY (`workday_id`) REFERENCES `core_workday` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_orderpayment`
--

LOCK TABLES `core_orderpayment` WRITE;
/*!40000 ALTER TABLE `core_orderpayment` DISABLE KEYS */;
INSERT INTO `core_orderpayment` VALUES (1,'2026-05-01 04:06:34.760263',5.00,0.00,200.00,205.00,1,4,1,'','pago-tranferencia/payment_1_transfer.svg'),(2,'2026-05-01 04:25:38.284325',0.00,80.00,0.00,80.00,1,4,1,'pago-tarjeta/payment_2_card.svg',''),(3,'2026-05-01 06:16:20.429452',160.00,0.00,0.00,160.00,1,3,1,'',''),(4,'2026-05-01 07:01:26.457141',0.00,80.00,0.00,80.00,1,3,1,'pago-tarjeta/payment_4_card.svg',''),(5,'2026-05-01 07:02:18.663503',0.00,0.00,120.00,120.00,1,3,1,'','pago-tranferencia/17776775877618989636566545673904.jpg'),(6,'2026-05-01 07:04:10.973527',0.00,80.00,0.00,80.00,1,5,1,'pago-tarjeta/payment_6_card.svg',''),(7,'2026-05-01 07:50:44.926570',10.00,0.00,0.00,10.00,1,6,1,'','');
/*!40000 ALTER TABLE `core_orderpayment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_product`
--

DROP TABLE IF EXISTS `core_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `category` varchar(20) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `description` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `stock` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  CONSTRAINT `core_product_chk_1` CHECK ((`stock` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_product`
--

LOCK TABLES `core_product` WRITE;
/*!40000 ALTER TABLE `core_product` DISABLE KEYS */;
INSERT INTO `core_product` VALUES (3,'Cerveza','BEBIDA',100.00,'',1,34),(4,'Drink','BEBIDA',85.00,'',1,220),(5,'Pizza','COMIDA',120.00,'',1,15),(6,'Hambuerguesa','COMIDA',85.00,'',1,20),(7,'Alas','COMIDA',120.00,'',1,10),(8,'Bonless','COMIDA',120.00,'',1,3),(9,'Cerveza Barril','BEBIDA',85.00,'',1,20),(10,'Jochos','COMIDA',80.00,'',1,10),(11,'Especial','BEBIDA',90.00,'',1,60),(12,'Tacos','COMIDA',120.00,'',1,10),(13,'Papas a la frencesa','COMIDA',80.00,'',1,15);
/*!40000 ALTER TABLE `core_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_productsupply`
--

DROP TABLE IF EXISTS `core_productsupply`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_productsupply` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity_required` decimal(10,2) NOT NULL,
  `product_id` bigint NOT NULL,
  `supply_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product_supply` (`product_id`,`supply_id`),
  KEY `core_productsupply_supply_id_98b613ca_fk_core_supply_id` (`supply_id`),
  CONSTRAINT `core_productsupply_product_id_66c2a7d6_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_productsupply_supply_id_98b613ca_fk_core_supply_id` FOREIGN KEY (`supply_id`) REFERENCES `core_supply` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_productsupply`
--

LOCK TABLES `core_productsupply` WRITE;
/*!40000 ALTER TABLE `core_productsupply` DISABLE KEYS */;
INSERT INTO `core_productsupply` VALUES (2,1.00,3,4),(4,1.00,3,3),(5,1.00,6,2),(6,1.00,6,1),(7,1.00,6,5),(8,1.00,6,8),(9,1.00,7,7),(10,1.00,7,6),(11,1.00,8,7),(12,1.00,8,9),(13,1.00,8,5),(14,1.00,3,11),(15,1.00,3,12),(16,1.00,9,4),(17,1.00,9,3),(18,1.00,9,11),(19,1.00,9,12),(20,1.00,4,4),(21,1.00,4,3),(22,1.00,4,11),(23,1.00,6,9),(24,1.00,6,10),(25,1.00,10,9),(26,1.00,10,2),(27,1.00,10,1),(28,1.00,10,10),(29,1.00,10,8),(30,1.00,13,9),(31,1.00,13,12),(32,1.00,5,7),(33,1.00,5,9),(34,1.00,3,13);
/*!40000 ALTER TABLE `core_productsupply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_productvariant`
--

DROP TABLE IF EXISTS `core_productvariant`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_productvariant` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `stock` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `product_id` bigint NOT NULL,
  `price_delta` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_product_variant` (`product_id`,`name`),
  CONSTRAINT `core_productvariant_product_id_79c7de1b_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_productvariant_chk_1` CHECK ((`stock` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_productvariant`
--

LOCK TABLES `core_productvariant` WRITE;
/*!40000 ALTER TABLE `core_productvariant` DISABLE KEYS */;
INSERT INTO `core_productvariant` VALUES (2,'Victoria',6,1,3,0.00),(3,'Corona',4,1,3,0.00),(4,'Peperonni',3,1,5,0.00),(5,'Hawiana',12,1,5,0.00),(6,'XX',5,1,3,0.00),(7,'Modelo Especial',2,1,3,15.00),(8,'Negra Modelo',3,1,3,15.00),(9,'Pacífico',2,1,3,0.00),(10,'Leon',3,1,3,0.00),(11,'Indio',3,1,3,0.00),(12,'Miller',4,1,3,0.00),(13,'Heneken',2,1,3,0.00),(14,'Ron',100,1,4,0.00),(15,'Brandy',10,1,4,0.00),(16,'Tequila',100,1,4,0.00),(17,'Bodka',10,1,4,0.00),(18,'Frutos Rojos',40,1,11,0.00),(19,'Azulito',20,1,11,0.00);
/*!40000 ALTER TABLE `core_productvariant` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_supply`
--

DROP TABLE IF EXISTS `core_supply`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_supply` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `is_available` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_supply`
--

LOCK TABLES `core_supply` WRITE;
/*!40000 ALTER TABLE `core_supply` DISABLE KEYS */;
INSERT INTO `core_supply` VALUES (1,'Jitomate',1),(2,'Cebolla',1),(3,'Escarcha tamarindo',1),(4,'Escarcha Miguelito',1),(5,'Queso amarillo',1),(6,'Salsa Mango',1),(7,'Salsa BBQ',1),(8,'Picante',1),(9,'Catsup',1),(10,'Mostaza',1),(11,'Limón',1),(12,'Sal',1),(13,'Tajin',1);
/*!40000 ALTER TABLE `core_supply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_useraccess`
--

DROP TABLE IF EXISTS `core_useraccess`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_useraccess` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `can_menu` tinyint(1) NOT NULL,
  `can_administrador` tinyint(1) NOT NULL,
  `can_comanda` tinyint(1) NOT NULL,
  `can_cocina` tinyint(1) NOT NULL,
  `can_bar` tinyint(1) NOT NULL,
  `can_entregas` tinyint(1) NOT NULL,
  `can_caja` tinyint(1) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `core_useraccess_user_id_87592e74_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_useraccess`
--

LOCK TABLES `core_useraccess` WRITE;
/*!40000 ALTER TABLE `core_useraccess` DISABLE KEYS */;
INSERT INTO `core_useraccess` VALUES (1,'ADMINISTRADOR',1,1,1,1,1,1,1,1),(2,'EMPLEADO',1,0,1,1,1,1,1,2),(3,'EMPLEADO',1,0,0,0,1,0,0,3),(4,'ADMINISTRADOR',1,1,1,1,1,1,1,5),(5,'EMPLEADO',1,0,1,1,1,1,1,6),(6,'ADMINISTRADOR',1,1,1,1,1,1,1,7);
/*!40000 ALTER TABLE `core_useraccess` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_workday`
--

DROP TABLE IF EXISTS `core_workday`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_workday` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `opened_at` datetime(6) NOT NULL,
  `closed_at` datetime(6) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `pending_orders_on_close` int unsigned NOT NULL,
  `closed_by_id` int DEFAULT NULL,
  `opened_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_workday_closed_by_id_f446df3f_fk_auth_user_id` (`closed_by_id`),
  KEY `core_workday_opened_by_id_c9c68326_fk_auth_user_id` (`opened_by_id`),
  CONSTRAINT `core_workday_closed_by_id_f446df3f_fk_auth_user_id` FOREIGN KEY (`closed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_workday_opened_by_id_c9c68326_fk_auth_user_id` FOREIGN KEY (`opened_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_workday_chk_1` CHECK ((`pending_orders_on_close` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_workday`
--

LOCK TABLES `core_workday` WRITE;
/*!40000 ALTER TABLE `core_workday` DISABLE KEYS */;
INSERT INTO `core_workday` VALUES (1,'2026-04-30 04:04:01.360167','2026-05-02 02:00:35.368830','CERRADO',4,1,1),(2,'2026-05-02 02:00:44.882352',NULL,'ABIERTO',0,NULL,1);
/*!40000 ALTER TABLE `core_workday` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(2,'auth','group'),(3,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(7,'core','order'),(8,'core','orderitem'),(15,'core','orderitempayment'),(16,'core','orderpayment'),(9,'core','product'),(11,'core','productsupply'),(12,'core','productvariant'),(10,'core','supply'),(13,'core','useraccess'),(14,'core','workday'),(6,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-04-30 00:20:42.084813'),(2,'auth','0001_initial','2026-04-30 00:20:42.550184'),(3,'admin','0001_initial','2026-04-30 00:20:42.650261'),(4,'admin','0002_logentry_remove_auto_add','2026-04-30 00:20:42.654257'),(5,'admin','0003_logentry_add_action_flag_choices','2026-04-30 00:20:42.660311'),(6,'contenttypes','0002_remove_content_type_name','2026-04-30 00:20:42.739895'),(7,'auth','0002_alter_permission_name_max_length','2026-04-30 00:20:42.787947'),(8,'auth','0003_alter_user_email_max_length','2026-04-30 00:20:42.804964'),(9,'auth','0004_alter_user_username_opts','2026-04-30 00:20:42.810353'),(10,'auth','0005_alter_user_last_login_null','2026-04-30 00:20:42.851777'),(11,'auth','0006_require_contenttypes_0002','2026-04-30 00:20:42.853607'),(12,'auth','0007_alter_validators_add_error_messages','2026-04-30 00:20:42.858966'),(13,'auth','0008_alter_user_username_max_length','2026-04-30 00:20:42.904500'),(14,'auth','0009_alter_user_last_name_max_length','2026-04-30 00:20:42.947158'),(15,'auth','0010_alter_group_name_max_length','2026-04-30 00:20:42.960358'),(16,'auth','0011_update_proxy_permissions','2026-04-30 00:20:42.967004'),(17,'auth','0012_alter_user_first_name_max_length','2026-04-30 00:20:43.019336'),(18,'core','0001_initial','2026-04-30 00:20:43.198054'),(19,'sessions','0001_initial','2026-04-30 00:20:43.219289'),(20,'core','0002_remove_product_preparation_area','2026-04-30 00:25:13.418962'),(21,'core','0003_alter_orderitem_status_productsupply_and_more','2026-04-30 00:32:31.481035'),(22,'core','0004_existencia_producto_insumo_disponible','2026-04-30 00:36:58.946622'),(23,'core','0005_variante_producto_supply_simplificado','2026-04-30 00:46:21.651128'),(24,'core','0006_quitar_unit_supply','2026-04-30 01:08:45.658417'),(25,'core','0007_productvariant_price_delta','2026-04-30 01:57:06.950166'),(26,'core','0008_useraccess','2026-04-30 03:15:11.446167'),(27,'core','0009_workday_order_workday','2026-04-30 03:28:09.896916'),(28,'core','0010_orderitem_variant','2026-04-30 03:57:52.678567'),(29,'core','0011_remove_order_guest_reference','2026-04-30 04:40:10.107749'),(30,'core','0012_orderitem_waiter_name','2026-04-30 04:45:33.044589'),(31,'core','0013_remove_order_waiter_request_scope','2026-04-30 05:32:38.162419'),(32,'core','0014_orderpayment_orderitempayment_and_item_paid_status','2026-05-01 04:06:10.069591'),(33,'core','0015_orderpayment_evidence_fields','2026-05-01 06:59:49.770452'),(34,'core','0016_orderitem_paid_status_split','2026-05-01 07:50:05.172262');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('4hpzlicq31874nuafyii3nla7bma7cgi','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIyxI:jv711GHoVhTYN-o0iMK0eCfzYVMENFMGLM14yzIiguQ','2026-05-16 01:15:40.486399'),('6fvoyk1fs245vj5g5gslztlaar65jbua','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIi8o:N3CICxucx5Bmwt9BzU6j-E_PlF_Enj6K0fzGQ_zzVRw','2026-05-15 07:18:26.633349'),('b427vdfys01pmuxbwk9xkixe5xrxxygr','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIi6l:vRh2QcL2WaXU27rNgzx8J4kE4ejfZ0WqzJJ_tZWkFmk','2026-05-15 07:16:19.343677'),('dltyhwfja0dk2r6dhxm7jmcqi1j40gkb','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIgpm:4_ENv2GYHZuqBX0fmbpXj6tsZHVUCJczqKIWauMNZE0','2026-05-15 05:54:42.120853'),('ip7ivzf5qssxivjp09loawu6xg4oc80j','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIx7m:lg_SBOtncwiKuPDt6FGSXlftHG0xsCRoHTh8Pxh2wlI','2026-05-15 23:18:22.868285'),('tc99h9zyrqqczf4p3suigjs2wxz999dj','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIx7X:N9__s-0ecEfG0vpVqTmRZR_1xCVIXvBB5hLsoJ5GDhc','2026-05-15 23:18:07.653201'),('wye3mh60yert5iqf0d5vamjwldd1ql3t','.eJxVjMsOwiAQRf-FtSE8pBSX7vsNZJhhpGogKe3K-O_apAvd3nPOfYkI21ri1vMSZxIXocXpd0uAj1x3QHeotyax1XWZk9wVedAup0b5eT3cv4MCvXxrdsk7AoUYrDZGKWSdrAqWAhKx14wDBj-ExGxA03kEUsYkYscQRi3eH_ucOLk:1wIi6G:_Qn-4tJFLFTrmYbkcM6_jePdG0J4_NRAYMdL62FLgx4','2026-05-15 07:15:48.696048');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'bar_db'
--

--
-- Dumping routines for database 'bar_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-05  0:43:01
