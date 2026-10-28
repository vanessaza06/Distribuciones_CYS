-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: distribuidora_cys
-- ------------------------------------------------------
-- Server version	8.0.43

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
-- Table structure for table `agenda_inventario`
--

DROP TABLE IF EXISTS `agenda_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agenda_inventario` (
  `codigo_agenda` int NOT NULL AUTO_INCREMENT,
  `titulo` varchar(200) NOT NULL,
  `descripcion` longtext,
  `fecha` datetime(6) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `completado_por` varchar(50) DEFAULT NULL,
  `documento_usuario_agenda` varchar(50) DEFAULT NULL,
  `responsable_agenda` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`codigo_agenda`),
  KEY `agenda_inventario_completado_por_8e772769_fk_usuario_documento` (`completado_por`),
  KEY `agenda_inventario_documento_usuario_ag_52168aec_fk_usuario_d` (`documento_usuario_agenda`),
  KEY `agenda_inventario_responsable_agenda_e9433822_fk_usuario_d` (`responsable_agenda`),
  CONSTRAINT `agenda_inventario_completado_por_8e772769_fk_usuario_documento` FOREIGN KEY (`completado_por`) REFERENCES `usuario` (`documento`),
  CONSTRAINT `agenda_inventario_documento_usuario_ag_52168aec_fk_usuario_d` FOREIGN KEY (`documento_usuario_agenda`) REFERENCES `usuario` (`documento`),
  CONSTRAINT `agenda_inventario_responsable_agenda_e9433822_fk_usuario_d` FOREIGN KEY (`responsable_agenda`) REFERENCES `usuario` (`documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agenda_inventario`
--

LOCK TABLES `agenda_inventario` WRITE;
/*!40000 ALTER TABLE `agenda_inventario` DISABLE KEYS */;
/*!40000 ALTER TABLE `agenda_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `apertura_caja`
--

DROP TABLE IF EXISTS `apertura_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apertura_caja` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `monto_base` decimal(12,2) NOT NULL,
  `observacion` longtext NOT NULL,
  `denominaciones` json NOT NULL,
  `creado_en` datetime(6) NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `fecha` (`fecha`),
  KEY `apertura_caja_usuario_id_e3b64d8c_fk_usuarios_usuario_id` (`usuario_id`),
  CONSTRAINT `apertura_caja_usuario_id_e3b64d8c_fk_usuarios_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `apertura_caja`
--

LOCK TABLES `apertura_caja` WRITE;
/*!40000 ALTER TABLE `apertura_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `apertura_caja` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=133 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add Usuario',7,'add_usuario'),(22,'Can change Usuario',7,'change_usuario'),(23,'Can delete Usuario',7,'delete_usuario'),(24,'Can view Usuario',7,'view_usuario'),(25,'Can add Registro de actividad',6,'add_registroactividad'),(26,'Can change Registro de actividad',6,'change_registroactividad'),(27,'Can delete Registro de actividad',6,'delete_registroactividad'),(28,'Can view Registro de actividad',6,'view_registroactividad'),(29,'Can add usuario',25,'add_usuario'),(30,'Can change usuario',25,'change_usuario'),(31,'Can delete usuario',25,'delete_usuario'),(32,'Can view usuario',25,'view_usuario'),(33,'Can add bodega',8,'add_bodega'),(34,'Can change bodega',8,'change_bodega'),(35,'Can delete bodega',8,'delete_bodega'),(36,'Can view bodega',8,'view_bodega'),(37,'Can add detalle venta',15,'add_detalleventa'),(38,'Can change detalle venta',15,'change_detalleventa'),(39,'Can delete detalle venta',15,'delete_detalleventa'),(40,'Can view detalle venta',15,'view_detalleventa'),(41,'Can add Marca',19,'add_marca'),(42,'Can change Marca',19,'change_marca'),(43,'Can delete Marca',19,'delete_marca'),(44,'Can view Marca',19,'view_marca'),(45,'Can add Proveedor',24,'add_proveedor'),(46,'Can change Proveedor',24,'change_proveedor'),(47,'Can delete Proveedor',24,'delete_proveedor'),(48,'Can view Proveedor',24,'view_proveedor'),(49,'Can add caja',9,'add_caja'),(50,'Can change caja',9,'change_caja'),(51,'Can delete caja',9,'delete_caja'),(52,'Can view caja',9,'view_caja'),(53,'Can add Categoría',10,'add_categoria'),(54,'Can change Categoría',10,'change_categoria'),(55,'Can delete Categoría',10,'delete_categoria'),(56,'Can view Categoría',10,'view_categoria'),(57,'Can add Compra',11,'add_compra'),(58,'Can change Compra',11,'change_compra'),(59,'Can delete Compra',11,'delete_compra'),(60,'Can view Compra',11,'view_compra'),(61,'Can add Detalle de Compra',12,'add_detallecompra'),(62,'Can change Detalle de Compra',12,'change_detallecompra'),(63,'Can delete Detalle de Compra',12,'delete_detallecompra'),(64,'Can view Detalle de Compra',12,'view_detallecompra'),(65,'Can add devolucion',16,'add_devolucion'),(66,'Can change devolucion',16,'change_devolucion'),(67,'Can delete devolucion',16,'delete_devolucion'),(68,'Can view devolucion',16,'view_devolucion'),(69,'Can add metodo pago',20,'add_metodopago'),(70,'Can change metodo pago',20,'change_metodopago'),(71,'Can delete metodo pago',20,'delete_metodopago'),(72,'Can view metodo pago',20,'view_metodopago'),(73,'Can add producto',23,'add_producto'),(74,'Can change producto',23,'change_producto'),(75,'Can delete producto',23,'delete_producto'),(76,'Can view producto',23,'view_producto'),(77,'Can add presentacion producto',22,'add_presentacionproducto'),(78,'Can change presentacion producto',22,'change_presentacionproducto'),(79,'Can delete presentacion producto',22,'delete_presentacionproducto'),(80,'Can view presentacion producto',22,'view_presentacionproducto'),(81,'Can add lote',18,'add_lote'),(82,'Can change lote',18,'change_lote'),(83,'Can delete lote',18,'delete_lote'),(84,'Can view lote',18,'view_lote'),(85,'Can add detalle producto',14,'add_detalleproducto'),(86,'Can change detalle producto',14,'change_detalleproducto'),(87,'Can delete detalle producto',14,'delete_detalleproducto'),(88,'Can view detalle producto',14,'view_detalleproducto'),(89,'Can add detalle devolucion',13,'add_detalledevolucion'),(90,'Can change detalle devolucion',13,'change_detalledevolucion'),(91,'Can delete detalle devolucion',13,'delete_detalledevolucion'),(92,'Can view detalle devolucion',13,'view_detalledevolucion'),(93,'Can add devolucion proveedores',17,'add_devolucionproveedores'),(94,'Can change devolucion proveedores',17,'change_devolucionproveedores'),(95,'Can delete devolucion proveedores',17,'delete_devolucionproveedores'),(96,'Can view devolucion proveedores',17,'view_devolucionproveedores'),(97,'Can add venta',26,'add_venta'),(98,'Can change venta',26,'change_venta'),(99,'Can delete venta',26,'delete_venta'),(100,'Can view venta',26,'view_venta'),(101,'Can add pago venta',21,'add_pagoventa'),(102,'Can change pago venta',21,'change_pagoventa'),(103,'Can delete pago venta',21,'delete_pagoventa'),(104,'Can view pago venta',21,'view_pagoventa'),(105,'Can add Agenda de Inventario',27,'add_agendainventario'),(106,'Can change Agenda de Inventario',27,'change_agendainventario'),(107,'Can delete Agenda de Inventario',27,'delete_agendainventario'),(108,'Can view Agenda de Inventario',27,'view_agendainventario'),(109,'Can add Hallazgo',28,'add_hallazgo'),(110,'Can change Hallazgo',28,'change_hallazgo'),(111,'Can delete Hallazgo',28,'delete_hallazgo'),(112,'Can view Hallazgo',28,'view_hallazgo'),(113,'Can add Cliente',31,'add_cliente'),(114,'Can change Cliente',31,'change_cliente'),(115,'Can delete Cliente',31,'delete_cliente'),(116,'Can view Cliente',31,'view_cliente'),(117,'Can add Apertura de Caja',29,'add_aperturacaja'),(118,'Can change Apertura de Caja',29,'change_aperturacaja'),(119,'Can delete Apertura de Caja',29,'delete_aperturacaja'),(120,'Can view Apertura de Caja',29,'view_aperturacaja'),(121,'Can add Cierre de Caja',30,'add_cierrecaja'),(122,'Can change Cierre de Caja',30,'change_cierrecaja'),(123,'Can delete Cierre de Caja',30,'delete_cierrecaja'),(124,'Can view Cierre de Caja',30,'view_cierrecaja'),(125,'Can add Respaldo',32,'add_backupregistro'),(126,'Can change Respaldo',32,'change_backupregistro'),(127,'Can delete Respaldo',32,'delete_backupregistro'),(128,'Can view Respaldo',32,'view_backupregistro'),(129,'Can add Configuracion de Empresa',33,'add_configuracionempresa'),(130,'Can change Configuracion de Empresa',33,'change_configuracionempresa'),(131,'Can delete Configuracion de Empresa',33,'delete_configuracionempresa'),(132,'Can view Configuracion de Empresa',33,'view_configuracionempresa');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `backup_registro`
--

DROP TABLE IF EXISTS `backup_registro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `backup_registro` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(200) NOT NULL,
  `ruta` varchar(500) NOT NULL,
  `fecha` datetime(6) NOT NULL,
  `tamaño_mb` double NOT NULL,
  `descripcion` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `backup_registro`
--

LOCK TABLES `backup_registro` WRITE;
/*!40000 ALTER TABLE `backup_registro` DISABLE KEYS */;
/*!40000 ALTER TABLE `backup_registro` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bodega`
--

DROP TABLE IF EXISTS `bodega`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bodega` (
  `codigo_bodega` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` longtext,
  `estado` varchar(20) NOT NULL,
  `capacidad` int DEFAULT NULL,
  PRIMARY KEY (`codigo_bodega`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bodega`
--

LOCK TABLES `bodega` WRITE;
/*!40000 ALTER TABLE `bodega` DISABLE KEYS */;
INSERT INTO `bodega` VALUES (1,'Bodega Principal',NULL,'',NULL);
/*!40000 ALTER TABLE `bodega` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `caja`
--

DROP TABLE IF EXISTS `caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `caja` (
  `codigo_caja` int NOT NULL AUTO_INCREMENT,
  `fecha_hora` datetime(6) NOT NULL,
  `denominaciones` json NOT NULL,
  `monto_base` decimal(12,2) NOT NULL,
  `total_efectivo` decimal(12,2) NOT NULL,
  `total_transferencias` decimal(12,2) NOT NULL,
  `total_retirado` decimal(12,2) NOT NULL,
  `observacion` longtext,
  `documento_usuario` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`codigo_caja`),
  KEY `caja_documento_usuario_e0d6d07a_fk_usuario_documento` (`documento_usuario`),
  CONSTRAINT `caja_documento_usuario_e0d6d07a_fk_usuario_documento` FOREIGN KEY (`documento_usuario`) REFERENCES `usuario` (`documento`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `caja`
--

LOCK TABLES `caja` WRITE;
/*!40000 ALTER TABLE `caja` DISABLE KEYS */;
INSERT INTO `caja` VALUES (1,'2026-10-16 15:04:25.414614','{}',460350.00,-200000.00,0.00,0.00,'[CERRADO]',NULL),(2,'2026-10-18 22:27:21.922149','{\"operador\": \"yuri@\"}',0.00,1000000.00,0.00,0.00,'Turno iniciado automáticamente al registrar venta',NULL);
/*!40000 ALTER TABLE `caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `codigo_categoria` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` longtext,
  `subcategoria_id` int DEFAULT NULL,
  `activo` tinyint(1) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  PRIMARY KEY (`codigo_categoria`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `categoria_subcategoria_id_941c9281` (`subcategoria_id`),
  CONSTRAINT `categoria_subcategoria_id_941c9281_fk_categoria_codigo_categoria` FOREIGN KEY (`subcategoria_id`) REFERENCES `categoria` (`codigo_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoria`
--

LOCK TABLES `categoria` WRITE;
/*!40000 ALTER TABLE `categoria` DISABLE KEYS */;
INSERT INTO `categoria` VALUES (49,'Cervezas',NULL,NULL,1,'CERV'),(50,'Aguardientes y rones',NULL,NULL,1,'AGRN'),(51,'Destilados importados',NULL,NULL,1,'DEST'),(52,'Licores dulces y vinos',NULL,NULL,1,'LIDV'),(53,'Bebidas sin alcohol',NULL,NULL,1,'SINA');
/*!40000 ALTER TABLE `categoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cierre_caja`
--

DROP TABLE IF EXISTS `cierre_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cierre_caja` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `total_contado` decimal(12,2) NOT NULL,
  `monto_base_siguiente` decimal(12,2) NOT NULL,
  `total_retirado` decimal(12,2) NOT NULL,
  `denominaciones` json NOT NULL,
  `creado_en` datetime(6) NOT NULL,
  `apertura_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `fecha` (`fecha`),
  UNIQUE KEY `apertura_id` (`apertura_id`),
  CONSTRAINT `cierre_caja_apertura_id_7d22e5c5_fk_apertura_caja_id` FOREIGN KEY (`apertura_id`) REFERENCES `apertura_caja` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cierre_caja`
--

LOCK TABLES `cierre_caja` WRITE;
/*!40000 ALTER TABLE `cierre_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `cierre_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compra`
--

DROP TABLE IF EXISTS `compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compra` (
  `codigo_compra` int NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `valor` decimal(12,2) NOT NULL,
  `saldo` decimal(12,2) NOT NULL,
  `documento_usuario` varchar(50) NOT NULL,
  `codigo_proveedor` varchar(50) NOT NULL,
  PRIMARY KEY (`codigo_compra`),
  KEY `compra_codigo_proveedor_976b6181_fk_proveedor_nit_proveedores` (`codigo_proveedor`),
  KEY `compra_documento_usuario_e08c977c_fk_usuario_documento` (`documento_usuario`),
  CONSTRAINT `compra_codigo_proveedor_976b6181_fk_proveedor_nit_proveedores` FOREIGN KEY (`codigo_proveedor`) REFERENCES `proveedor` (`nit_proveedores`),
  CONSTRAINT `compra_documento_usuario_e08c977c_fk_usuario_documento` FOREIGN KEY (`documento_usuario`) REFERENCES `usuario` (`documento`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compra`
--

LOCK TABLES `compra` WRITE;
/*!40000 ALTER TABLE `compra` DISABLE KEYS */;
INSERT INTO `compra` VALUES (1,'2026-09-22 12:36:42.945033','recibida',75000.00,35000.00,'12345678','10101010010'),(2,'2026-09-24 13:14:13.418947','recibida',25000.00,0.00,'1052382181','101010'),(3,'2026-09-24 13:34:02.984255','pendiente',150000.00,99999.99,'1052382181','10101010010'),(6,'2026-09-25 13:10:16.117980','recibida',210000.00,0.00,'1052382181','10101010010'),(29,'2026-10-08 13:09:50.029735','recibida',900000.00,0.00,'1052382181','10101010010'),(30,'2026-10-08 13:21:11.804255','recibida',225000.00,0.00,'1052382181','10101010010'),(31,'2026-10-09 20:20:36.830701','recibida',900.00,900.00,'1052382181','10101010010'),(32,'2026-10-09 20:30:34.934380','recibida',1.00,0.00,'1052382181','10101010010'),(33,'2026-10-09 20:33:24.829948','recibida',102.00,102.00,'1052382181','101010'),(34,'2026-10-15 13:14:07.385293','recibida',50000.00,0.00,'1052382181','101010'),(35,'2026-10-15 15:16:04.626455','confirmada',250000.00,0.00,'1052382181','101010');
/*!40000 ALTER TABLE `compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuracion_empresa`
--

DROP TABLE IF EXISTS `configuracion_empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion_empresa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre_empresa` varchar(200) NOT NULL,
  `nit` varchar(50) NOT NULL,
  `direccion` varchar(300) NOT NULL,
  `telefono` varchar(50) NOT NULL,
  `email` varchar(254) NOT NULL,
  `iva_porcentaje` decimal(5,2) NOT NULL,
  `moneda` varchar(10) NOT NULL,
  `unidades_medida` json NOT NULL,
  `tema_predeterminado` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion_empresa`
--

LOCK TABLES `configuracion_empresa` WRITE;
/*!40000 ALTER TABLE `configuracion_empresa` DISABLE KEYS */;
INSERT INTO `configuracion_empresa` VALUES (1,'CYS Ltda','','','','',19.00,'COP','[]','oscuro');
/*!40000 ALTER TABLE `configuracion_empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_compra`
--

DROP TABLE IF EXISTS `detalle_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_compra` (
  `numero_compra` int NOT NULL AUTO_INCREMENT,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `fecha_registro` datetime(6) NOT NULL,
  `subtotal_compra` decimal(12,2) NOT NULL,
  `codigo_compra` int NOT NULL,
  `codigo_lote` int DEFAULT NULL,
  `codigo_producto` int DEFAULT NULL,
  PRIMARY KEY (`numero_compra`),
  KEY `detalle_compra_codigo_compra_f15d5e35_fk_compra_codigo_compra` (`codigo_compra`),
  KEY `detalle_compra_codigo_lote_66a539e6_fk_lote_codigo_lote` (`codigo_lote`),
  KEY `detalle_compra_codigo_producto_4d61f167_fk_producto_` (`codigo_producto`),
  CONSTRAINT `detalle_compra_codigo_compra_f15d5e35_fk_compra_codigo_compra` FOREIGN KEY (`codigo_compra`) REFERENCES `compra` (`codigo_compra`),
  CONSTRAINT `detalle_compra_codigo_lote_66a539e6_fk_lote_codigo_lote` FOREIGN KEY (`codigo_lote`) REFERENCES `lote` (`codigo_lote`),
  CONSTRAINT `detalle_compra_codigo_producto_4d61f167_fk_producto_` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_compra`
--

LOCK TABLES `detalle_compra` WRITE;
/*!40000 ALTER TABLE `detalle_compra` DISABLE KEYS */;
INSERT INTO `detalle_compra` VALUES (1,5,15000.00,'2026-09-22 12:36:42.946111',75000.00,1,NULL,1),(2,1,25000.00,'2026-09-24 13:14:13.420230',25000.00,2,NULL,1),(3,1,150000.00,'2026-09-24 13:34:02.985624',150000.00,3,NULL,1),(6,1,210000.00,'2026-09-25 13:10:16.119425',210000.00,6,NULL,1),(29,60,15000.00,'2026-10-08 13:09:50.035795',900000.00,29,NULL,3646),(30,90,2500.00,'2026-10-08 13:21:11.805964',225000.00,30,NULL,3630),(31,90,10.00,'2026-10-09 20:20:36.832057',900.00,31,NULL,3643),(32,1,1.00,'2026-10-09 20:30:34.936240',1.00,32,NULL,3653),(33,102,1.00,'2026-10-09 20:33:24.831186',102.00,33,NULL,3630),(34,10,5000.00,'2026-10-15 13:14:07.386836',50000.00,34,NULL,4065),(35,10,25000.00,'2026-10-15 15:16:04.628524',250000.00,35,NULL,4066);
/*!40000 ALTER TABLE `detalle_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_devolucion`
--

DROP TABLE IF EXISTS `detalle_devolucion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_devolucion` (
  `numero_devolucion` int NOT NULL AUTO_INCREMENT,
  `cantidad` int unsigned NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `descripcion` longtext,
  `observacion` longtext,
  `codigo_devolucion` int NOT NULL,
  `codigo_producto` int DEFAULT NULL,
  `lote_id` int DEFAULT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `presentacion_id` int DEFAULT NULL,
  PRIMARY KEY (`numero_devolucion`),
  KEY `detalle_devolucion_codigo_devolucion_a6a5eabb_fk_devolucio` (`codigo_devolucion`),
  KEY `detalle_devolucion_lote_id_3e2c6061_fk_lote_codigo_lote` (`lote_id`),
  KEY `detalle_devolucion_presentacion_id_342f1565_fk_presentac` (`presentacion_id`),
  KEY `detalle_devolucion_codigo_producto_f2a5e156_fk_producto_` (`codigo_producto`),
  CONSTRAINT `detalle_devolucion_codigo_devolucion_a6a5eabb_fk_devolucio` FOREIGN KEY (`codigo_devolucion`) REFERENCES `devolucion` (`codigo_devolucion`),
  CONSTRAINT `detalle_devolucion_codigo_producto_f2a5e156_fk_producto_` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`),
  CONSTRAINT `detalle_devolucion_lote_id_3e2c6061_fk_lote_codigo_lote` FOREIGN KEY (`lote_id`) REFERENCES `lote` (`codigo_lote`),
  CONSTRAINT `detalle_devolucion_presentacion_id_342f1565_fk_presentac` FOREIGN KEY (`presentacion_id`) REFERENCES `presentacion_producto` (`codigo_presentacion`),
  CONSTRAINT `detalle_devolucion_cantidad_ac1a6474_check` CHECK ((`cantidad` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_devolucion`
--

LOCK TABLES `detalle_devolucion` WRITE;
/*!40000 ALTER TABLE `detalle_devolucion` DISABLE KEYS */;
INSERT INTO `detalle_devolucion` VALUES (3,1,'2026-10-16','Devolución de venta #1','defecto',3,4108,NULL,0.00,NULL),(4,1,'2026-10-18','Devolución de venta #2','defecto',4,4108,7,50000.00,4598);
/*!40000 ALTER TABLE `detalle_devolucion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_producto`
--

DROP TABLE IF EXISTS `detalle_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_producto` (
  `numero_producto` int NOT NULL AUTO_INCREMENT,
  `codigo_barras` varchar(100) NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `descripcion` longtext,
  `codigo_marca` int NOT NULL,
  `codigo_producto` int NOT NULL,
  PRIMARY KEY (`numero_producto`),
  UNIQUE KEY `detalle_producto_codigo_barras_fafc215f_uniq` (`codigo_barras`),
  KEY `detalle_producto_codigo_marca_7dd90974_fk_marca_codigo_marca` (`codigo_marca`),
  KEY `detalle_producto_codigo_producto_d3781e5e_fk_producto_` (`codigo_producto`),
  CONSTRAINT `detalle_producto_codigo_marca_7dd90974_fk_marca_codigo_marca` FOREIGN KEY (`codigo_marca`) REFERENCES `marca` (`codigo_marca`),
  CONSTRAINT `detalle_producto_codigo_producto_d3781e5e_fk_producto_` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_producto`
--

LOCK TABLES `detalle_producto` WRITE;
/*!40000 ALTER TABLE `detalle_producto` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_venta`
--

DROP TABLE IF EXISTS `detalle_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_venta` (
  `codigo_detalle_venta` int NOT NULL AUTO_INCREMENT,
  `cantidad` int unsigned NOT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `codigo_producto` int DEFAULT NULL,
  `codigo_venta` int NOT NULL,
  `lote_id` int DEFAULT NULL,
  `presentacion_id` int DEFAULT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  PRIMARY KEY (`codigo_detalle_venta`),
  KEY `detalle_venta_codigo_venta_4ef8519e_fk_venta_codigo_venta` (`codigo_venta`),
  KEY `detalle_venta_lote_id_3308e38d_fk_lote_codigo_lote` (`lote_id`),
  KEY `detalle_venta_presentacion_id_20ca4412_fk_presentac` (`presentacion_id`),
  KEY `detalle_venta_codigo_producto_93cc67a2_fk_producto_` (`codigo_producto`),
  CONSTRAINT `detalle_venta_codigo_producto_93cc67a2_fk_producto_` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`),
  CONSTRAINT `detalle_venta_codigo_venta_4ef8519e_fk_venta_codigo_venta` FOREIGN KEY (`codigo_venta`) REFERENCES `venta` (`codigo_venta`),
  CONSTRAINT `detalle_venta_lote_id_3308e38d_fk_lote_codigo_lote` FOREIGN KEY (`lote_id`) REFERENCES `lote` (`codigo_lote`),
  CONSTRAINT `detalle_venta_presentacion_id_20ca4412_fk_presentac` FOREIGN KEY (`presentacion_id`) REFERENCES `presentacion_producto` (`codigo_presentacion`),
  CONSTRAINT `detalle_venta_cantidad_150054a4_check` CHECK ((`cantidad` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_venta`
--

LOCK TABLES `detalle_venta` WRITE;
/*!40000 ALTER TABLE `detalle_venta` DISABLE KEYS */;
INSERT INTO `detalle_venta` VALUES (1,1,50000.00,4108,1,7,4598,50000.00,50000.00),(2,1,50000.00,4108,2,7,4598,50000.00,50000.00),(3,10,50000.00,4108,3,7,4598,500000.00,500000.00);
/*!40000 ALTER TABLE `detalle_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devolucion`
--

DROP TABLE IF EXISTS `devolucion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devolucion` (
  `codigo_devolucion` int NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `motivo` varchar(50) NOT NULL,
  `tipo_devolucion` varchar(50) NOT NULL,
  `observaciones` longtext,
  `total_devuelto` decimal(12,2) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `cantidad_cambio` int NOT NULL,
  `metodo_pago_devolucion` varchar(50) NOT NULL,
  `codigo_detalle_venta` int DEFAULT NULL,
  `documento_usuario` varchar(50) DEFAULT NULL,
  `codigo_venta` int NOT NULL,
  `restaurar_stock` tinyint(1) NOT NULL,
  `presenta_comprobante` tinyint(1) NOT NULL,
  PRIMARY KEY (`codigo_devolucion`),
  KEY `devolucion_codigo_detalle_venta_9ba57dc9_fk_detalle_v` (`codigo_detalle_venta`),
  KEY `devolucion_documento_usuario_936e0639_fk_usuario_documento` (`documento_usuario`),
  KEY `devolucion_codigo_venta_e7b87a98_fk_venta_codigo_venta` (`codigo_venta`),
  CONSTRAINT `devolucion_codigo_detalle_venta_9ba57dc9_fk_detalle_v` FOREIGN KEY (`codigo_detalle_venta`) REFERENCES `detalle_venta` (`codigo_detalle_venta`),
  CONSTRAINT `devolucion_codigo_venta_e7b87a98_fk_venta_codigo_venta` FOREIGN KEY (`codigo_venta`) REFERENCES `venta` (`codigo_venta`),
  CONSTRAINT `devolucion_documento_usuario_936e0639_fk_usuario_documento` FOREIGN KEY (`documento_usuario`) REFERENCES `usuario` (`documento`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devolucion`
--

LOCK TABLES `devolucion` WRITE;
/*!40000 ALTER TABLE `devolucion` DISABLE KEYS */;
INSERT INTO `devolucion` VALUES (3,'2026-10-16 15:11:26.993110','defecto','cambio','',50000.00,'completada',1,'efectivo',1,'1052382181',1,1,1),(4,'2026-10-18 22:29:05.257454','defecto','cambio','',50000.00,'completada',1,'efectivo',2,'1052382181',2,1,1);
/*!40000 ALTER TABLE `devolucion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devolucion_proveedores`
--

DROP TABLE IF EXISTS `devolucion_proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devolucion_proveedores` (
  `numero_proveedor` int NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `motivo` longtext NOT NULL,
  `estado` varchar(20) NOT NULL,
  `observaciones` longtext,
  `nit_proveedores` varchar(50) NOT NULL,
  PRIMARY KEY (`numero_proveedor`),
  KEY `devolucion_proveedor_nit_proveedores_b24c2411_fk_proveedor` (`nit_proveedores`),
  CONSTRAINT `devolucion_proveedor_nit_proveedores_b24c2411_fk_proveedor` FOREIGN KEY (`nit_proveedores`) REFERENCES `proveedor` (`nit_proveedores`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devolucion_proveedores`
--

LOCK TABLES `devolucion_proveedores` WRITE;
/*!40000 ALTER TABLE `devolucion_proveedores` DISABLE KEYS */;
INSERT INTO `devolucion_proveedores` VALUES (3,'2026-10-16 15:22:48.870133','otro','aplicada','{\"total\": 50000.0, \"cantidad\": 10, \"precio_unitario\": 5000.0, \"compra_id\": 34, \"detalle_compra_id\": 34, \"lote_id\": null, \"producto_id\": 4065, \"producto_nombre\": \"AGUA PET POOL 300\", \"tipo_resolucion\": \"reembolso\", \"obs\": \"\", \"unidades_descontadas\": 0, \"stock_descontado\": true}','101010');
/*!40000 ALTER TABLE `devolucion_proveedores` ENABLE KEYS */;
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
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_usuarios_usuario_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_usuarios_usuario_id` FOREIGN KEY (`user_id`) REFERENCES `usuarios_usuario` (`id`),
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
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(27,'app','agendainventario'),(29,'app','aperturacaja'),(32,'app','backupregistro'),(8,'app','bodega'),(9,'app','caja'),(10,'app','categoria'),(30,'app','cierrecaja'),(31,'app','cliente'),(11,'app','compra'),(33,'app','configuracionempresa'),(12,'app','detallecompra'),(13,'app','detalledevolucion'),(14,'app','detalleproducto'),(15,'app','detalleventa'),(16,'app','devolucion'),(17,'app','devolucionproveedores'),(28,'app','hallazgo'),(18,'app','lote'),(19,'app','marca'),(20,'app','metodopago'),(21,'app','pagoventa'),(22,'app','presentacionproducto'),(23,'app','producto'),(24,'app','proveedor'),(25,'app','usuario'),(26,'app','venta'),(2,'auth','group'),(3,'auth','permission'),(4,'contenttypes','contenttype'),(5,'sessions','session'),(6,'usuarios','registroactividad'),(7,'usuarios','usuario');
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
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-09-09 16:24:31.696583'),(2,'contenttypes','0002_remove_content_type_name','2026-09-09 16:24:31.824919'),(3,'auth','0001_initial','2026-09-09 16:24:32.193500'),(4,'auth','0002_alter_permission_name_max_length','2026-09-09 16:24:32.275944'),(5,'auth','0003_alter_user_email_max_length','2026-09-09 16:24:32.283459'),(6,'auth','0004_alter_user_username_opts','2026-09-09 16:24:32.290262'),(7,'auth','0005_alter_user_last_login_null','2026-09-09 16:24:32.297415'),(8,'auth','0006_require_contenttypes_0002','2026-09-09 16:24:32.303414'),(9,'auth','0007_alter_validators_add_error_messages','2026-09-09 16:24:32.312886'),(10,'auth','0008_alter_user_username_max_length','2026-09-09 16:24:32.322567'),(11,'auth','0009_alter_user_last_name_max_length','2026-09-09 16:24:32.332039'),(12,'auth','0010_alter_group_name_max_length','2026-09-09 16:24:32.359306'),(13,'auth','0011_update_proxy_permissions','2026-09-09 16:24:32.371654'),(14,'auth','0012_alter_user_first_name_max_length','2026-09-09 16:24:32.378551'),(15,'usuarios','0001_initial','2026-09-09 16:24:32.914520'),(16,'admin','0001_initial','2026-09-09 16:24:33.092126'),(17,'admin','0002_logentry_remove_auto_add','2026-09-09 16:24:33.102606'),(18,'admin','0003_logentry_add_action_flag_choices','2026-09-09 16:24:33.113970'),(19,'app','0001_initial','2026-09-09 16:24:35.488769'),(20,'app','0002_categoria_activo_producto_activo_and_more','2026-09-09 16:24:35.717127'),(21,'app','0003_lote_cantidad_inicial_lote_stock_actual_and_more','2026-09-09 16:24:36.011468'),(22,'app','0004_alter_categoria_options_categoria_codigo_and_more','2026-09-09 16:24:36.235573'),(23,'app','0005_alter_compra_options_alter_detallecompra_options_and_more','2026-09-09 16:24:36.571577'),(24,'app','0006_remove_categoria_padre_categoria_codigo_and_more','2026-09-09 16:24:36.920135'),(25,'app','0007_alter_marca_options_alter_caja_usuario_and_more','2026-09-09 16:24:37.801960'),(26,'sessions','0001_initial','2026-09-09 16:24:37.844037'),(27,'app','0008_alter_lote_options_lote_numero_lote_and_more','2026-09-10 11:51:40.111040'),(28,'app','0009_alter_detalleproducto_options_and_more','2026-09-10 13:25:24.401617'),(29,'app','0010_cliente_alter_detalledevolucion_options_and_more','2026-09-17 11:42:02.409724'),(30,'app','0011_backupregistro_configuracionempresa_and_more','2026-09-22 11:59:59.943713'),(31,'app','0012_remove_venta_cliente_lote_imagen_venta_cliente_email_and_more','2026-09-24 11:53:33.646646'),(32,'app','0013_remove_lote_imagen_alter_lote_bodega_and_more','2026-10-02 12:53:13.811458'),(33,'app','0014_marca_fecha_creacion','2026-10-15 12:18:16.010071'),(34,'app','0015_remove_marca_fecha_creacion_and_more','2026-10-19 11:33:55.264884'),(35,'app','0016_backupregistro_descripcion','2026-10-28 13:33:01.910026');
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
INSERT INTO `django_session` VALUES ('03z863q940iwl27vowegdij6jn88y8jl','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCf09:bpaXaG3gDkMRGn7AlImrzeHdTXPepEMCZlxMggyIOqA','2026-10-16 15:16:45.875067'),('1jiau0d0qqptbaebz0nvvncevavstkv3','.eJxVzEsOwiAUheG9MDYEuFweDp27BsLjIlVDk9KOjHvXJh3o-PvPebEQt7WFbdASpsLOTCrQaKxjp19KMT-o717usd9mnue-LlPie8IPHfw6F3pejvbvoMXRvutsCQiMs8WTQJEqCGsURBJFe0RvssGI5JWvKVdrkwMli1BVauMEIHt_AOb5OJY:1xHjbd:1g6859E5gElADgQtpXaEQavyWKVv6cni9QbYFj3eNvA','2026-10-30 15:12:25.288373'),('2fsl355r1b0u4v6926mv75xha7iszpg7','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xCezo:rijWlvUeX1M8RpF7NV2AMJ7HAkobLAF3teK5PM0RgBo','2026-10-16 15:16:24.804558'),('2ydjhtahou4ffyci3uj8oafm5iu1x2nk','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xM40i:Odem05W54U2zcCKaSvjYf21Z67j0OOXnuT8WXQNoYiQ','2026-11-11 13:48:12.358635'),('38he5shdljc2g7usi7clu7lcxfr34jta','.eJxVjzkOwyAURO9CHVkYzJYyfc6APvCJyQISmCrK3WNLLux23syT5kss9GW2vWG1KZArGRmfhFSaXI7IgX9h3nh4Qn6UwZe81OSGrTLstA33EvB927snwQxtXtdeIUcutQoGqaAucqok44A0TEYII70UINAwE52PSjnN2Rgoi-MkNeVilfbWoaZia3mvQgiflA_p-cPvD3vgRwc:1xHjbk:_mfdDVgR9C1CkJz8RElrJ3joDCzcBEoriupROp007fs','2026-10-30 15:12:32.024992'),('3jqd16lzfuys7rpxwx965f0jz5csae5g','.eJxVj02OwjAMhe_SNapIWhoyq9Hs5wyVkzi0UOIqaSohxN1x-RFFXvl7z_bztWghT12bE8a2d8VPIZpis4YG7AnDorgjhAOVlsIUe1MulvKlpvKfHA5_L-_Xgg5Sx9OqcsaoWluld0o3QiptQAhV-z1oqVB5i8220rUWkl076fdWYAXGVwDCS16aU4bY0yOnaD59oLOJyDdWnkgDAzyPA4KjlbBkYuWSY__LeIw0Izp6f79dirnDuZ0xTPDg8glGSMTN7Q6zkmXm:1xM3qt:3ebpk-9zhvEZF1yj-VHl0pRlSgbhWNXQ67ru3iVq3mw','2026-11-11 13:38:03.910965'),('4kl40p3gf48imxm2t0dsjjaau9al66or','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xEolk:WQ9x3BnTui09YhbbBXoRaJ-DlIig_H_f9LAJd-USWyU','2026-10-22 14:06:48.047732'),('5wk7viwt4fc0bk4v9swt59bys0jr5aj6','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCf6b:BoylLQYsgfcic4FYaZV6p8isiRmyJKjaDwKHkPmYiXc','2026-10-16 15:23:25.251794'),('6ixrb682uot2mymbfhvjmeck8p69ueev','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xEolb:_TS7wlh3Gjks9QQoWl6vQIERhIyjNbqxENYryi8q_U0','2026-10-22 14:06:39.284910'),('6vs5djc7lht57goufwllvej0ow7chfvm','e30:1x67Lh:uVrEfTnn9ufRB2yPK6vLCwaJsk9w_03u5Pj3N9KTUhY','2026-09-28 14:07:57.160862'),('87m8zkllruum10258b19vglh8qn6r1qw','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xEp0p:b7W49L3vf0QMcVW_rG7MNezfWOEJFT7tjGb-wSqV7tY','2026-10-22 14:22:23.871458'),('ao879jyrmy2pvxegnp0l9hsut2addjtc','.eJxVjs0OwiAQhN-FsyFLKX8evfsMzcJSqRowpfVifHdLUhPN3Ga-mcyLDbguaVhrnIeJ2JEJdvj1PIZbzC2gK-ZL4aHkZZ48bwjf08rPheL9tLN_Awlr2tpaK5KGrJVgegfGWSNBI5JQ1ljdKRCgHeAoQh-9D4RKig5hRCHJ-bCNPubyjJHK9yg0sfcHLVc-Gw:1xCfI2:IuskDEHilnEYdoMZTkY7O79C6veC2DjVIA0Jd2jIFL0','2026-10-16 15:35:14.156354'),('at1y1b6mt3vyhclao3kq6viea72udy2w','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xHkwy:MUyMmlNkO7GFE8_z_FiM4cVX2pQ-Bac1Huc4QTkm7Rc','2026-10-30 16:38:32.395829'),('auk60c7uwqovk603905te33vssq0295n','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjqW:dQbAgr9N1txpaI8RU4_O5Ek3XF7IT7Hod8yUK6cpcqk','2026-10-30 15:27:48.583690'),('bf1t54no72mj0rp7q1n1b7j8jvcw5ewv','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1x66ip:q6wnoJsQDwCdwXv-m4wMwn9ackEH2YSwMyf-7EX_DfY','2026-09-28 13:27:47.291795'),('bx6mmljukui2g08b8i97sqaf6eoo3bt8','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCf6V:ydaJnPV4fFydox_OCfMYFqMEGP88jxN_yUs4-vCjo0k','2026-10-16 15:23:19.071531'),('chdd9ooo901mxfmisaywaqndakcwjj24','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1xA5g8:Xs1I_Q6L_HQhy--0_oZk7aAPzpL8Sy9dhjj2Bneqhjs','2026-10-09 13:09:28.976885'),('dib074uwf2plhmc8b5k5fqx5gexj809o','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1x4ePk:atrPRKRhB0c1qwqeHyDMyEEeTCR61WkDD_hqdPpCUSg','2026-09-24 13:02:04.864827'),('dkodz8g96ofblv5ie2j4u739mqzpw0k5','.eJxVjs0OwiAQhN-FsyFLKX8evfsMzcJSqRowpfVifHdLUhPN3Ga-mcyLDbguaVhrnIeJ2JEJdvj1PIZbzC2gK-ZL4aHkZZ48bwjf08rPheL9tLN_Awlr2tpaK5KGrJVgegfGWSNBI5JQ1ljdKRCgHeAoQh-9D4RKig5hRCHJ-bCNPubyjJHK9yg0sfcHLVc-Gw:1xCf01:jLD-_5OLTxxaBbuYphN4vyI9OWLEz95N_SujyMBcbes','2026-10-16 15:16:37.719820'),('e4fhvtlu2qsl8kl0zyeqkxhcbfgn5j6l','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1x67KS:Os0lVxOXXrmEBGrAvbu3L7nVEojHPHNyPAQMnKaCGxQ','2026-09-28 14:06:40.836867'),('ecfp05z3uxf7nwvfbhe81y80ow4657x7','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCf0L:U1ks2E0-StS9auBsKtUpf6KlY7WJ4L3KpRhmYPxr9qM','2026-10-16 15:16:57.749084'),('et60p9e6hukc9cm91hdybnr94thx5n9w','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjfq:dIZId3Tx5X5C7wi1kg8sBUFhgBgWio9U9cBKT6N3szI','2026-10-30 15:16:46.453837'),('fklyjdzkhahmnjrxwdudxw1dzaz4gb7b','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHkwd:92tXgtwycGkfHUR7q42gLHMfVkiPjLqC9nTlK3VgoJU','2026-10-30 16:38:11.166616'),('gu8gpx0uzq1ig8uju3wxhbjpcye3c5hg','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjg4:scS1jYwHJJBibVs1Hww63H6-SAiZNFJQesVx51Z8U18','2026-10-30 15:17:00.173903'),('h8frghk6ljhhupp40c78ps47god91fb7','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xDlUR:Nm_KtCTam9w6mXrt-enZJdjF8fhshmeV2dDglLhFslY','2026-10-19 16:24:35.912042'),('hk9l8pwyt8iu6u4w9tcpdaznb4kxvd2z','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1xA5g9:rGXbUZWzHXxJv2eQV_HWlyl0brPcgEz8_46oDFEEvec','2026-10-09 13:09:29.932310'),('hminbpvvren2m5t2vgatpilltsonnjh8','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjjk:h7R3T9KzpjZptDZC9T0_vf3HqxzApd9310NR4y8bCn4','2026-10-30 15:20:48.175800'),('hwoxyzyl6i3knnq87peldhy8iq4wn2l6','e30:1x7EVQ:emK07ftsZ0Ka9NGaPtIdGCc_9c2wH5XLv7Z_Qq6jKcw','2026-10-01 15:58:36.395748'),('i1nlb3rddoh885gg72rycvdiv1q3uoyu','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHl9X:7lYglJBYKqY5GjB5iK3EKW1GDueaICvyQvKch66NQPM','2026-10-30 16:51:31.153778'),('id2cveunk6pt0piruu70ehkf1l39qnrw','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1x7EXh:N89_eJ55lGOg_1hxiNKOPfCdlnYgCNZceflztmIDuYU','2026-10-01 16:00:57.995037'),('ixaeov250bd80znww7zleyd64kj2fk79','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xCezj:K6ZQuiama4LyEOQc1-cey9GP2LbsZqYW1_G3a77IEp8','2026-10-16 15:16:19.529104'),('j23f3wyc5h3p8ze2lcldorq3bd3k9kqv','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjjt:81kmnusLqKnMkvgRld5og1bBb_msXE4JmG3856RnNiE','2026-10-30 15:20:57.763547'),('j70qrm5fzkzyz5pkkokz1pi53b0p4dak','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1x7EVH:S7gnaMvi2-MAVP-Aa17FgPwjzw__NOQaRHmr8culI9E','2026-10-01 15:58:27.931517'),('j7zjgj9rak8nsxxxmnwjb3cunt28u8se','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjjU:VmXjFJKTG0QmxTlQIrRn3DVJcsY4bidOpjQ-lReOkAA','2026-10-30 15:20:32.253670'),('k0hofom5wq04cn1nc6nz33aegq3ti2zx','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCfI9:3jZbsERV4c2P18CFjw2c1eceilk2LecfaryLfyBZXuc','2026-10-16 15:35:21.094412'),('kvkmfuig19kekz3tuzc1z6xwhhrhzqxo','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjjL:LNY0LyDOn1hm7ySPWv9V3HuMBD3_0qmE_sllwEBVXno','2026-10-30 15:20:23.729399'),('kytjcl5qalcpxh9r1mhmjhlg3akugcu8','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1xDkKn:L3EXCvfUW5L4s6hisZACEoQsXmVWYzY9ydBH6ZQLDvE','2026-10-19 15:10:33.708541'),('l5slcyugpd97xk0sqylzw1dsw2n687bt','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xHjms:P8Fhb5T0JM5bJSw9Og2_7qh1jde59O1xCc_9O5X3wtQ','2026-10-30 15:24:02.684174'),('m90jpjjrrkvz0s7jfuzc2sku7w51f3jx','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHkwT:lEc7IXL-NxV5TFH97KEwkUIu3nQ-oUqbSG3_M22-Qxg','2026-10-30 16:38:01.704467'),('mgl2qyt9y78kfsvb4nu9da3uvtuf2p23','e30:1x7EX2:buKXPLtomHU-TDHk1CA_RVUXfjif_vK8h57RGt_LiGc','2026-10-01 16:00:16.444984'),('muepqzavk7jmv9wgmzj65yciiyzgwr16','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjcD:PVaW3eg4Tm_hrwLGAc5V_7Q82H7KjvUvw9Tpq32ZLNc','2026-10-30 15:13:01.503120'),('mukq2cd4yr1krd6p0zmjf56k18mo8ssd','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjqJ:nH-NBmW2dEiXZc4gHF8S1135gf9nVOzG1v0y4P6A1LY','2026-10-30 15:27:35.665224'),('mzefx2fw7vjbeoymc5il5h13wzayuaap','.eJxVkE0OwiAQhe_C2jS0hUpduvcMZIDBVlto-HFjvLvU1Fgzq3nvmzeTeRIJOQ0yRwxyNOREakYOe1GBvqNbHXMDd_WV9i6FUVUrUm1urC7e4HTe2L-AAeJQpnlDobeMMoWm5h03iEoA17ZE2E6B0G0DQDsr9BEo71HQllmBfd-C1QJKaI4Zwug_d9bs1zs_q4Blx44JfioCmHl0O3U9qMh6gmxQJoxJpnkpwBL8A9H47xPoWuT1Bu6CYIA:1xA6VY:YjZwHRRMQgQGhR1HYQk_ubYx6nVWBT8UM0yjvaN8qNw','2026-10-09 14:02:36.867849'),('o1p8x65epvpyj1nqn2x8d8ewyn3rjb5w','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1xDkKo:BNCf01LEmKWZMHuqC-7TsCALPsQ6u1_lOlBGk7-kcl8','2026-10-19 15:10:34.664514'),('o6d2xd8lw0drje6efaj48xrxcyc9vozw','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xEolT:dQI2BuIxhgJSbicS0Mn5_tEP-2CNgdJelrWl_BVqCog','2026-10-22 14:06:31.460831'),('ouk2b78jbl6ca9jhlpw3eugakslnanes','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjcm:oZ2El3kIoUZmprKHuY4b5tQQ-WbX-siMAAKxpkAN91o','2026-10-30 15:13:36.869208'),('pu5af9p0mquoorx4csz8quail4u3wbjp','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1x67Nh:BbQvQ8MG2m-VxmBYzkJxM3g5Aqcjw79WaNp2tr_EQjY','2026-09-28 14:10:01.999076'),('q61uovahiq4kuvmq2jqfb7u76jkkursv','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xM3zI:pZ3w6cm8K8UtjFAQG4Pgrftt4YFrQdK8Ld5_WHOXvHs','2026-11-11 13:46:44.891736'),('qtxvab2mc32t7yz9qof8s5vrmi86b599','.eJxVzEsOwiAUheG9MDYEuFweDp27BsLjIlVDk9KOjHvXJh3o-PvPebEQt7WFbdASpsLOTCrQaKxjp19KMT-o717usd9mnue-LlPie8IPHfw6F3pejvbvoMXRvutsCQiMs8WTQJEqCGsURBJFe0RvssGI5JWvKVdrkwMli1BVauMEIHt_AOb5OJY:1xHjbr:AbYYJQmHi5HLStTyfn0PU4DrQDw0zZqfqbeiYtx9YAU','2026-10-30 15:12:39.361311'),('sc084582xppigjyoleolw3nspth95ips','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjkR:jK_ToxK3Q1TwlQ10YTYR03-MzClo_-Zw8VMMQii0dLc','2026-10-30 15:21:31.517869'),('t0cslx3t95n9b080nomoh8ebts4evn6w','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1x67Jr:8wWtY28KtkUIiLx29clzwlhcdHhque0neVV1P07gIW8','2026-09-28 14:06:03.234257'),('tgr8jfchculgd2x9r1m4a2jp7xu1l959','.eJxVkMFOwzAMhl8F5Yyqxm1Tj9t235Vr5SQOLXTxlKwcQLw76VaJIvtif79_W_5WAy23cVgyp2Hy6kWBet73LLkPjivw7xTfpHISb2my1SqpNpqrs3ieT5v2n8FIeSzTiNB2dRMwNNg6o1tN4Bg8egtQB-JgLJlDb7EzvfMdNRZ7Z8FC8GjgUEyXvFCa5H4m_JVRLjZxWfFKkXOmp-MX7dRJ5sL4cp2ZvOzAel0huu6gQdCoC7sm-WT2sv1C148oqX5-Ac3lYQM:1xA6Xi:ydDHBxrqp6VO3pFN1CUvn2HSzidTI69aA-80K_VDg4Q','2026-10-09 14:04:50.470654'),('ti9ezkk17jfp1jk46eiyo6mv9q9ntxz2','.eJxVjTkOwyAURO9CHVlgzJYyfc6APnwckwUkMGmi3D1YcuG0b2befIiFti621VBsRHImjJyOzIF_hLQFeId0y4PPaS3RDVtl2NM6XDOG52Xv_gkWqEtfSymQK9SaUzUZqoxWnEoAZEIrLUdBGZWGwsz8FJzzCIKzEegMjKNxvktbbVBitiU_uxDwFdOBbmcdvyGFWoF8f0iQR7g:1xHKOT:rtwaus9tEVnTlAKjsiIYj8ROmldvx4kfXbSkGc2wHW8','2026-10-29 12:17:09.340624'),('u9wskaj8bcfvv55hiwi4nrrj6jsc19wt','.eJxVjsFuwjAMhl8F5Yyqxm1TsxvcuXKt7MRZu5UEJfQC4t2XTkjrjvb3-ff_VAMt93FYsqRhcupDgdpvd0z2W8IK3BeFz1jZGO5p4mpVqjfN1Tk6mU9v91_ASHks14jQdnXj0TfYWqNbTWAFHDoGqD2JN0zm0DN2preuo4axtwwM3qGBQwld8kJpir814W8M8cpJyosLBcmZdscHbewU58LkepuFXNyAtV0huu6gQdCo1esHNBNY_g:1xA5gA:jNPFFYycRbfjK2yrbj0fOu66QdlHb72clvIAGxQ9p7s','2026-10-09 13:09:30.817595'),('vmb5i7t7pue368ne0bpn4mu6zrbvh3kh','.eJxVkMFOwzAMhl8F5Yyqxm1Tj9t235Vr5SQOLXTxlKwcQLw76VaJIvtif79_W_5WAy23cVgyp2Hy6kWBet73LLkPjivw7xTfpHISb2my1SqpNpqrs3ieT5v2n8FIeSzTiNB2dRMwNNg6o1tN4Bg8egtQB-JgLJlDb7EzvfMdNRZ7Z8FC8GjgUEyXvFCa5H4m_JVRLjZxWfFKkXOmp-MX7dRJ5sL4cp2ZvOzAel0huu6gQdCoC7sm-WT2sv1C148oqX5-Ac3lYQM:1x67WV:YiyI6rF_ZHBtdZZLTQYGkqaN-OlCCrCHwtY416RwdRk','2026-09-28 14:19:07.763343'),('vmj0nvzuzbq8l0q82ug4blk4ngk6qdab','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHjk2:wSvsWF63ThvXWZyjaJ0qGrbcveOHDnSb68n7DL2pjfY','2026-10-30 15:21:06.185562'),('wa3nqh3iazvk2hf7sgj0v9hh42e95ecw','.eJxVzDsOwjAQRdG9uEbW2JPxh5KeNVj-jEkAxVKcVIi9Q6QUUN_z3kuEuK1j2DovYSriLBSQRqeVU-L0G1PMD553Ue5xvjWZ27wuU5I7kUft8toKPy-H_TsYYx-_62wZGY2zxTMQpIpgjcbIUAZP5E02FIm99jXlam1yqFUBXdVgHCCJ9wctrDjx:1xCezv:CdbKjQ1Q4eTCJvEaD4OF4-VTAZ3qhLMtx1wL6O-2CVg','2026-10-16 15:16:31.453816'),('wijcfxj3cgaecbiqrmj5rexxc4zrcak5','.eJxVjs0OwiAQhN-FsyFLKX8evfsMzcJSqRowpfVifHdLUhPN3Ga-mcyLDbguaVhrnIeJ2JEJdvj1PIZbzC2gK-ZL4aHkZZ48bwjf08rPheL9tLN_Awlr2tpaK5KGrJVgegfGWSNBI5JQ1ljdKRCgHeAoQh-9D4RKig5hRCHJ-bCNPubyjJHK9yg0sfcHLVc-Gw:1xCf0s:kiWfRdh3Mu8aJ3bszZO20nIMhcr8KKE8wFaoXiB6iAo','2026-10-16 15:17:30.444128'),('wou4dk39fkqzie9dtczwu8nlksuqz8fa','.eJxVj8sOwiAQRf-FtSEg5eXSvd9ABobaai0NFDfGf5cmNdHM7p57TzIv4qCug6slZjciORFODr-Zh3CP8wbwBvM10ZDmNY-ebhW600IvCeN03rt_ggHK0NZKSRQajRFMd5Zpa7RgCgC5NNqoo2ScKcug56GL3gcEKfgRWA9coPWhSWupkMfkcpqaMD6WKQKmBpacnjFi-n7AtiPvD9QWRwQ:1xHl1E:JzC7d9fdwo7v9sRncpAEetwLjcyER7YPyxBETHVpBpw','2026-10-30 16:42:56.118524'),('wvwejc2aq2k4qch2kioqmnc5ydqygzl7','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHkzi:Zzvcl2izg9gbhBrDV1zTFOHHvxxQDPjAub7EGNBJJP8','2026-10-30 16:41:22.511859'),('x1wyna2c0j0ag6x39rcimmh485qibkhf','.eJxVjMsOwiAQRf-FtSFDKS-X7v0GMjDUVmsxUFbGf7dNutDtPeeeN_PY1tG3moqfiJ2ZYKffLWB8pGUHdMfllnnMy1qmwHeFH7Tya6Y0Xw73LzBiHbe31oqkIWslmN6BcdZI0IgklDVWdwoEaAc4iNinECKhkqJDGFBIciFu0VYblin7kuctmJ6vOSFl9vkCda0_8Q:1xHkwm:c7gA8xEUEBT90zdWSiwheOnPLOad7XQ92j-Xs-wvFEA','2026-10-30 16:38:20.113113'),('xnofdq27nmc74m5vadrblko05fpaw3ue','.eJxVkMFOwzAMhl8F5Yyqxm1Tj9t235Vr5SQOLXTxlKwcQLw76VaJIvtif79_W_5WAy23cVgyp2Hy6kWBet73LLkPjivw7xTfpHISb2my1SqpNpqrs3ieT5v2n8FIeSzTiNB2dRMwNNg6o1tN4Bg8egtQB-JgLJlDb7EzvfMdNRZ7Z8FC8GjgUEyXvFCa5H4m_JVRLjZxWfFKkXOmp-MX7dRJ5sL4cp2ZvOzAel0huu6gQdCoC7sm-WT2sv1C148oqX5-Ac3lYQM:1xCfJ3:Is8y9S9HaC89-ESEtXjDBlX5ECfQhEWT8ucvLMd2HLI','2026-10-16 15:36:17.608676'),('y6o2psafo4ip4l1qdj15vcx2z6u44ugi','e30:1x67M6:Zp_iUC0kEBIGqUp7Kks22NW3pHVz_WuDh9XTuGpFzAI','2026-09-28 14:08:22.075525'),('zg3vzycpwgfh9iyhzmgwjpewnc6a1isb','.eJxVjDsOwjAQBe_iGlm7cfyjpOcM1trr4ACypTipEHeHSCmgfTPzXiLQtpaw9byEmcVZoDj9bpHSI9cd8J3qrcnU6rrMUe6KPGiX18b5eTncv4NCvXxrYzQry84psKMH651VYIgYtbPODBoQjAeaMI05xsSkFQ4EE6FiH5N4fwCkxjcI:1xCf0e:VGbHzpqDm2eqaED0rDWSYXX6gJ1aSeaIvptw61sq5Wc','2026-10-16 15:17:16.387835'),('zo88lhwjjc28pvcmbggk89m17sywxnlm','e30:1x67Mx:LfEiB2WqKMMZFCWmO3lfmqel_iTmxrstG-2p8w9dzp8','2026-09-28 14:09:15.675533'),('zzq2zhks5ytal9t7fzvmeyqcedbxcapy','e30:1x7EWa:4zEpX9PoharjignxpKzi1YcdoX6-4-jm0WA9b-47ZLk','2026-10-01 15:59:48.481646');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hallazgo`
--

DROP TABLE IF EXISTS `hallazgo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hallazgo` (
  `numero_hallazgo` int NOT NULL AUTO_INCREMENT,
  `cantidad_sistema` int NOT NULL,
  `cantidad_fisica` int NOT NULL,
  `diferencia` int NOT NULL,
  `sesion_conteo` varchar(50) NOT NULL,
  `tipo_hallazgo` varchar(20) NOT NULL,
  `resultado_inventario` varchar(255) NOT NULL,
  `observaciones` longtext NOT NULL,
  `fecha_hallazgo` datetime(6) NOT NULL,
  `codigo_agenda` int NOT NULL,
  `codigo_producto` int NOT NULL,
  PRIMARY KEY (`numero_hallazgo`),
  KEY `hallazgo_codigo_agenda_7fe54805_fk_agenda_in` (`codigo_agenda`),
  KEY `hallazgo_codigo_producto_89cbb8f6_fk_producto_codigo_producto` (`codigo_producto`),
  CONSTRAINT `hallazgo_codigo_agenda_7fe54805_fk_agenda_in` FOREIGN KEY (`codigo_agenda`) REFERENCES `agenda_inventario` (`codigo_agenda`),
  CONSTRAINT `hallazgo_codigo_producto_89cbb8f6_fk_producto_codigo_producto` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hallazgo`
--

LOCK TABLES `hallazgo` WRITE;
/*!40000 ALTER TABLE `hallazgo` DISABLE KEYS */;
/*!40000 ALTER TABLE `hallazgo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lote`
--

DROP TABLE IF EXISTS `lote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lote` (
  `codigo_lote` int NOT NULL AUTO_INCREMENT,
  `costo_unitario` decimal(12,2) NOT NULL,
  `costo_total` decimal(12,2) NOT NULL,
  `fecha_registro` datetime(6) NOT NULL,
  `codigo_bodega` int DEFAULT NULL,
  `codigo_presentacion` int NOT NULL,
  `codigo_producto` int NOT NULL,
  `cantidad_inicial` int unsigned NOT NULL,
  `stock_actual` int unsigned NOT NULL,
  `numero_lote` varchar(100) NOT NULL,
  PRIMARY KEY (`codigo_lote`),
  UNIQUE KEY `numero_lote` (`numero_lote`),
  KEY `lote_codigo_presentacion_ebb60bd3_fk_presentac` (`codigo_presentacion`),
  KEY `lote_codigo_producto_62417e1c_fk_producto_codigo_producto` (`codigo_producto`),
  KEY `lote_codigo_bodega_3f356842_fk_bodega_codigo_bodega` (`codigo_bodega`),
  CONSTRAINT `lote_codigo_bodega_3f356842_fk_bodega_codigo_bodega` FOREIGN KEY (`codigo_bodega`) REFERENCES `bodega` (`codigo_bodega`),
  CONSTRAINT `lote_codigo_presentacion_ebb60bd3_fk_presentac` FOREIGN KEY (`codigo_presentacion`) REFERENCES `presentacion_producto` (`codigo_presentacion`),
  CONSTRAINT `lote_codigo_producto_62417e1c_fk_producto_codigo_producto` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`),
  CONSTRAINT `lote_chk_1` CHECK ((`cantidad_inicial` >= 0)),
  CONSTRAINT `lote_chk_2` CHECK ((`stock_actual` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lote`
--

LOCK TABLES `lote` WRITE;
/*!40000 ALTER TABLE `lote` DISABLE KEYS */;
INSERT INTO `lote` VALUES (7,10000.00,100000.00,'2026-10-15 14:03:32.852771',1,4598,4108,10,0,'LOT-08-CAJA COCA COLA');
/*!40000 ALTER TABLE `lote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marca`
--

DROP TABLE IF EXISTS `marca`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marca` (
  `codigo_marca` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` longtext NOT NULL,
  `estado` varchar(20) NOT NULL,
  PRIMARY KEY (`codigo_marca`)
) ENGINE=InnoDB AUTO_INCREMENT=206 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marca`
--

LOCK TABLES `marca` WRITE;
/*!40000 ALTER TABLE `marca` DISABLE KEYS */;
INSERT INTO `marca` VALUES (1,'corona','Cervezas','activo'),(2,'Águila','Cervezas','activo'),(3,'Águila Imperial','Cervezas','activo'),(4,'Águila Light','Cervezas','activo'),(5,'Águila Zero','Cervezas','activo'),(6,'Andina','Cervezas','activo'),(7,'Andina Light','Cervezas','activo'),(8,'Andina Refajo','Cervezas','activo'),(9,'Bacana','Cervezas','activo'),(10,'Budweiser','Cervezas','activo'),(11,'Club Colombia','Cervezas','activo'),(12,'Club Dorada','Cervezas','activo'),(13,'Club Negra','Cervezas','activo'),(14,'Club Roja','Cervezas','activo'),(15,'Club Trigo','Cervezas','activo'),(16,'Cola y Pola','Cervezas','activo'),(17,'Corona Cero','Cervezas','activo'),(18,'Coronita','Cervezas','activo'),(19,'Costeña','Cervezas','activo'),(20,'Heineken','Cervezas','activo'),(21,'Heineken 0.0','Cervezas','activo'),(22,'Kaufmann','Cervezas','activo'),(23,'Modelo','Cervezas','activo'),(24,'Miller Lite','Cervezas','activo'),(25,'Poker','Cervezas','activo'),(26,'Redd’s','Cervezas','activo'),(27,'Sol','Cervezas','activo'),(28,'Stella Artois','Cervezas','activo'),(29,'Tecate','Cervezas','activo'),(30,'Tres Cordilleras','Cervezas','activo'),(31,'Líder','Licores nacionales','activo'),(32,'Onix','Licores nacionales','activo'),(33,'Ron Boyacá','Licores nacionales','activo'),(34,'Amarillo','Licores nacionales','activo'),(35,'Ron Caldas','Licores nacionales','activo'),(36,'Ron Crema Caldas','Licores nacionales','activo'),(37,'Molendero','Licores nacionales','activo'),(38,'Cóctel Caldas','Licores nacionales','activo'),(39,'Ginebra Bosque de Indias','Licores nacionales','activo'),(40,'Aguardiente Antioqueño','Licores nacionales','activo'),(41,'Aguardiente Blanco','Licores nacionales','activo'),(42,'NatuMalta','Maltas y bebidas','activo'),(43,'Pony','Maltas y bebidas','activo'),(44,'Zalva','Maltas y bebidas','activo'),(45,'Pool','Aguas, energizantes y bebidas','activo'),(46,'Agua Vida','Aguas, energizantes y bebidas','activo'),(47,'Zend','Aguas, energizantes y bebidas','activo'),(48,'Cifrut','Aguas, energizantes y bebidas','activo'),(49,'Pulp','Aguas, energizantes y bebidas','activo'),(50,'Néctar','Aguas, energizantes y bebidas','activo'),(51,'Saviloe','Aguas, energizantes y bebidas','activo'),(52,'Sporade','Aguas, energizantes y bebidas','activo'),(53,'Vive 100','Aguas, energizantes y bebidas','activo'),(54,'Electrolit','Aguas, energizantes y bebidas','activo'),(55,'Hidralite','Aguas, energizantes y bebidas','activo'),(56,'Amper','Aguas, energizantes y bebidas','activo'),(57,'Red Bull','Aguas, energizantes y bebidas','activo'),(58,'Speed','Aguas, energizantes y bebidas','activo'),(59,'Brisa','Gaseosas y refrescos','activo'),(60,'Coca-Cola','Gaseosas y refrescos','activo'),(61,'Coca-Cola Zero','Gaseosas y refrescos','activo'),(62,'Fuze Tea','Gaseosas y refrescos','activo'),(63,'Kola Román','Gaseosas y refrescos','activo'),(64,'Manantial','Gaseosas y refrescos','activo'),(65,'Monster','Gaseosas y refrescos','activo'),(66,'Powerade','Gaseosas y refrescos','activo'),(67,'Quatro','Gaseosas y refrescos','activo'),(68,'Schweppes','Gaseosas y refrescos','activo'),(69,'Sprite','Gaseosas y refrescos','activo'),(70,'Valle','Gaseosas y refrescos','activo'),(71,'Big Cola','Gaseosas y refrescos','activo'),(72,'Postobón','Gaseosas y refrescos','activo'),(73,'Pepsi','Gaseosas y refrescos','activo'),(74,'Mr. Tea','Gaseosas y refrescos','activo'),(75,'Acqua','Gaseosas y refrescos','activo'),(76,'Bretaña','Gaseosas y refrescos','activo'),(77,'Canadá Dry','Gaseosas y refrescos','activo'),(78,'Cristal','Gaseosas y refrescos','activo'),(79,'Hatsu','Gaseosas y refrescos','activo'),(80,'Hit','Gaseosas y refrescos','activo'),(81,'H2O','Gaseosas y refrescos','activo'),(82,'Duos','Gaseosas y refrescos','activo'),(83,'EconoLitro','Gaseosas y refrescos','activo'),(84,'Squash','Gaseosas y refrescos','activo'),(85,'Tropicola','Gaseosas y refrescos','activo'),(86,'Tutti Frutti','Gaseosas y refrescos','activo'),(87,'Gatorade','Gaseosas y refrescos','activo'),(88,'Mustang','Cigarrillos y encendedores','activo'),(89,'Mustang Blanco','Cigarrillos y encendedores','activo'),(90,'Mustang Foresta','Cigarrillos y encendedores','activo'),(91,'Lucki','Cigarrillos y encendedores','activo'),(92,'L&M','Cigarrillos y encendedores','activo'),(93,'Marlboro','Cigarrillos y encendedores','activo'),(94,'Caribe','Cigarrillos y encendedores','activo'),(95,'Piel Roja','Cigarrillos y encendedores','activo'),(96,'Yama','Cigarrillos y encendedores','activo'),(97,'BIC','Cigarrillos y encendedores','activo'),(98,'Buchanan\'s','Whisky','activo'),(99,'Old Parr','Whisky','activo'),(100,'Johnnie Walker','Whisky','activo'),(101,'Chivas Regal','Whisky','activo'),(102,'Clan MacGregor','Whisky','activo'),(103,'Glenlivet','Whisky','activo'),(104,'Dewar\'s','Whisky','activo'),(105,'Jack Daniel\'s','Whisky','activo'),(106,'Ballantine\'s','Whisky','activo'),(107,'Black & White','Whisky','activo'),(108,'Something Special','Whisky','activo'),(109,'Passport','Whisky','activo'),(110,'VAT 69','Whisky','activo'),(111,'John Thomas','Whisky','activo'),(112,'Jameson','Whisky','activo'),(113,'Sir Edwards','Whisky','activo'),(114,'Harry','Whisky','activo'),(115,'Grants','Whisky','activo'),(116,'Singleton','Whisky','activo'),(117,'Grands','Whisky','activo'),(118,'Haward','Whisky / Ginebra','activo'),(119,'Black Jack','Whisky / Cremas de whisky','activo'),(120,'Castle House','Whisky','activo'),(121,'Jägermeister','Whisky','activo'),(122,'Smirnoff','Vodka','activo'),(123,'Absolut','Vodka','activo'),(124,'Tropcaya','Vodka','activo'),(125,'Stalinaya','Vodka','activo'),(126,'El Jimador','Tequila','activo'),(127,'Newton','Tequila','activo'),(128,'Puerta Negra','Tequila','activo'),(129,'Don Julio','Tequila','activo'),(130,'José Cuervo','Tequila','activo'),(131,'Tres Caballos','Tequila','activo'),(132,'Olmeca','Tequila','activo'),(133,'1800','Tequila','activo'),(134,'Los Cuates','Tequila','activo'),(135,'Patrón','Tequila','activo'),(136,'Altos','Tequila','activo'),(137,'Bacardí','Ron','activo'),(138,'Ron Trópico','Ron','activo'),(139,'Ron Santero','Ron','activo'),(140,'Baileys','Cremas de whisky','activo'),(141,'Copacabana','Cremas de whisky','activo'),(142,'Castel Hause','Cremas de whisky','activo'),(143,'Savors','Cremas de whisky','activo'),(144,'Whisleys','Cremas de whisky','activo'),(145,'Coloma','Cremas de whisky','activo'),(146,'Brymor','Cremas de whisky','activo'),(147,'Excelso','Cremas de whisky','activo'),(148,'Surtilégio','Cremas de whisky','activo'),(149,'Majestic','Champañas y espumantes','activo'),(150,'Gran Brindis','Champañas y espumantes','activo'),(151,'Peterlongo','Champañas y espumantes','activo'),(152,'Casanova','Champañas y espumantes','activo'),(153,'Alejandría','Champañas y espumantes','activo'),(154,'Monserrate','Champañas y espumantes','activo'),(155,'Frizzantino','Champañas y espumantes','activo'),(156,'Gran Celebración','Champañas y espumantes','activo'),(157,'Piccini','Champañas y espumantes','activo'),(158,'Alteza','Champañas y espumantes','activo'),(159,'Lambrusco','Champañas y espumantes','activo'),(160,'JP Chenet','Champañas y espumantes','activo'),(161,'Porttuse','Champañas y espumantes','activo'),(162,'Grajales','Vinos','activo'),(163,'Waltier','Vinos','inactivo'),(164,'Moscato Passito','Vinos','activo'),(165,'Embajador','Vinos','activo'),(166,'Casillero del Diablo','Vinos','activo'),(167,'Dubonet','Vinos','activo'),(168,'Mani Shewtiz','Vinos','activo'),(169,'Frontera','Vinos','activo'),(170,'Gato Negro','Vinos','activo'),(171,'Sangre de Boe','Vinos','activo'),(172,'Liebfraumilch','Vinos','activo'),(173,'Sanzón','Vinos','activo'),(174,'Cariñoso','Vinos','activo'),(175,'Moscatel','Vinos','activo'),(176,'Cinzano','Vinos','activo'),(177,'Dulce Amador','Vinos','activo'),(178,'Closs','Vinos','activo'),(179,'La Feria','Vinos','activo'),(180,'Tocornal','Vinos','activo'),(181,'Pazzito','Vinos','activo'),(182,'Polero','Vinos','activo'),(183,'Tres Medallas','Vinos','activo'),(184,'Rosaleda','Vinos','activo'),(185,'La Merced','Vinos','activo'),(186,'Viña Maipo','Vinos','activo'),(187,'Viña Piña','Vinos','activo'),(188,'Covier','Vinos','activo'),(189,'Arizo','Vinos','activo'),(190,'London','Ginebra','activo'),(191,'Gordon\'s','Ginebra','activo'),(192,'Sterling','Ginebra','activo'),(193,'Piña Colada Reagee','Otros licores y cócteles','activo'),(194,'Piña Colada Mavi','Otros licores y cócteles','activo'),(195,'Manzanilla Poderosa','Otros licores y cócteles','activo'),(196,'Piña Colada Isleña','Otros licores y cócteles','activo'),(197,'Paris Ice','Otros licores y cócteles','activo'),(198,'Sabajón','Otros licores y cócteles','activo'),(199,'Sabajón Apolo','Otros licores y cócteles','activo'),(200,'Piña Colada Tahití','Otros licores y cócteles','activo'),(201,'Brandy Domeco','Otros licores y cócteles','activo'),(202,'Brandy Cinco Estrellas','Otros licores y cócteles','activo'),(203,'Brandy Grajales','Otros licores y cócteles','activo'),(204,'Brandy Gran Brindis','Otros licores y cócteles','activo'),(205,'Four Loko','Otros licores y cócteles','activo');
/*!40000 ALTER TABLE `marca` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `metodo_pago`
--

DROP TABLE IF EXISTS `metodo_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `metodo_pago` (
  `codigo_metodo` int NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `valor` decimal(12,2) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  `efectivo` decimal(12,2) NOT NULL,
  `transaccion` decimal(12,2) NOT NULL,
  `observacion` longtext,
  `codigo_compra` int DEFAULT NULL,
  PRIMARY KEY (`codigo_metodo`),
  KEY `metodo_pago_codigo_compra_caa37707_fk_compra_codigo_compra` (`codigo_compra`),
  CONSTRAINT `metodo_pago_codigo_compra_caa37707_fk_compra_codigo_compra` FOREIGN KEY (`codigo_compra`) REFERENCES `compra` (`codigo_compra`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `metodo_pago`
--

LOCK TABLES `metodo_pago` WRITE;
/*!40000 ALTER TABLE `metodo_pago` DISABLE KEYS */;
INSERT INTO `metodo_pago` VALUES (1,'2026-09-22 12:36:42.946690',30000.00,'FAC-TEST-001',30000.00,0.00,'Abono de compra vía Efectivo - Factura FAC-TEST-001',1),(2,'2026-09-24 13:14:13.420952',25000.00,'FAC-6755',25000.00,0.00,'Abono de compra vía Efectivo - Factura FAC-6755',2),(3,'2026-09-24 13:34:02.986639',50000.00,'FAC-6755',50000.00,0.00,'Abono de compra vía Efectivo - Factura FAC-6755',3),(5,'2026-09-25 13:10:16.121009',20000.00,'FAC 01',20000.00,0.00,'Abono de compra vía Efectivo - Factura FAC 01',6),(10,'2026-09-25 13:28:50.331923',190000.00,'Abono Compra #6',0.00,190000.00,'Pago vía Nequi',6),(18,'2026-10-08 13:17:00.000000',900000.00,'Abono Compra #29',900000.00,0.00,'Abono vía Efectivo',29),(19,'2026-10-08 13:21:11.809195',200000.00,'FAC-2026',0.00,200000.00,'Pago inicial vía Nequi - Factura FAC-2026',30),(20,'2026-10-08 13:23:00.000000',25000.00,'Abono Compra #30',25000.00,0.00,'Abono vía Efectivo',30),(21,'2026-10-09 20:14:12.969746',0.01,'asass21132131321qwdeqeqweq',0.00,0.01,'Abono vía Breb - Factura asass21132131321qwdeqeqweq',3),(22,'2026-10-08 20:22:00.000000',10000.00,'Abono Compra #1',10000.00,0.00,'Abono vía Efectivo',1),(23,'2026-10-09 20:30:34.938915',1.00,'1',1.00,0.00,'Pago inicial vía Efectivo - Factura 1',32),(24,'2026-10-15 13:14:07.388838',50000.00,'FAC-123',0.00,50000.00,'Pago inicial vía Nequi - Factura FAC-123',34),(25,'2026-10-15 15:16:04.632116',250000.00,'fac_349',0.00,250000.00,'Pago inicial vía Nequi - Factura fac_349',35);
/*!40000 ALTER TABLE `metodo_pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pago_venta`
--

DROP TABLE IF EXISTS `pago_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago_venta` (
  `codigo_pago` int NOT NULL AUTO_INCREMENT,
  `fecha_pago` datetime(6) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `observaciones` longtext,
  `codigo_metodo` int NOT NULL,
  `codigo_venta` int NOT NULL,
  PRIMARY KEY (`codigo_pago`),
  KEY `pago_venta_codigo_metodo_ff393d20_fk_metodo_pago_codigo_metodo` (`codigo_metodo`),
  KEY `pago_venta_codigo_venta_018c3668_fk_venta_codigo_venta` (`codigo_venta`),
  CONSTRAINT `pago_venta_codigo_metodo_ff393d20_fk_metodo_pago_codigo_metodo` FOREIGN KEY (`codigo_metodo`) REFERENCES `metodo_pago` (`codigo_metodo`),
  CONSTRAINT `pago_venta_codigo_venta_018c3668_fk_venta_codigo_venta` FOREIGN KEY (`codigo_venta`) REFERENCES `venta` (`codigo_venta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago_venta`
--

LOCK TABLES `pago_venta` WRITE;
/*!40000 ALTER TABLE `pago_venta` DISABLE KEYS */;
/*!40000 ALTER TABLE `pago_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `presentacion_producto`
--

DROP TABLE IF EXISTS `presentacion_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `presentacion_producto` (
  `codigo_presentacion` int NOT NULL AUTO_INCREMENT,
  `precio_venta` decimal(12,2) NOT NULL,
  `cantidad` int unsigned NOT NULL,
  `observaciones` longtext,
  `codigo_producto` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`codigo_presentacion`),
  KEY `presentacion_product_codigo_producto_99c19100_fk_producto_` (`codigo_producto`),
  CONSTRAINT `presentacion_product_codigo_producto_99c19100_fk_producto_` FOREIGN KEY (`codigo_producto`) REFERENCES `producto` (`codigo_producto`),
  CONSTRAINT `presentacion_producto_chk_1` CHECK ((`cantidad` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4641 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `presentacion_producto`
--

LOCK TABLES `presentacion_producto` WRITE;
/*!40000 ALTER TABLE `presentacion_producto` DISABLE KEYS */;
INSERT INTO `presentacion_producto` VALUES (1,50000.00,10,'',1,'cocacola',1),(4120,0.00,1,NULL,3630,'Unidad',1),(4121,0.00,13,NULL,3631,'Canasta x13',1),(4122,0.00,1,NULL,3632,'Unidad',1),(4123,0.00,1,NULL,3633,'Unidad',1),(4124,0.00,30,NULL,3634,'Canasta x30',1),(4125,0.00,13,NULL,3635,'Canasta x13',1),(4126,0.00,1,NULL,3636,'Unidad',1),(4127,0.00,1,NULL,3637,'Unidad',1),(4128,0.00,1,NULL,3638,'Unidad',1),(4129,0.00,30,NULL,3639,'Canasta x30',1),(4130,0.00,13,NULL,3640,'Canasta x13',1),(4131,0.00,1,NULL,3641,'Unidad',1),(4132,0.00,1,NULL,3642,'Unidad',1),(4133,0.00,16,NULL,3643,'Canasta x16',1),(4134,0.00,1,NULL,3644,'Unidad',1),(4135,0.00,1,NULL,3645,'Unidad',1),(4136,0.00,1,NULL,3646,'Unidad',1),(4137,0.00,1,NULL,3647,'Unidad',1),(4138,0.00,1,NULL,3648,'Unidad',1),(4139,0.00,16,NULL,3649,'Canasta x16',1),(4140,0.00,16,NULL,3650,'Canasta x16',1),(4141,0.00,6,NULL,3651,'Canasta x6',1),(4142,0.00,6,NULL,3652,'Canasta x6',1),(4143,0.00,6,NULL,3653,'Canasta x6',1),(4144,0.00,1,NULL,3654,'Unidad',1),(4145,0.00,1,NULL,3655,'Unidad',1),(4146,0.00,1,NULL,3656,'Unidad',1),(4147,0.00,1,NULL,3657,'Unidad',1),(4148,0.00,6,NULL,3658,'Canasta x6',1),(4149,0.00,6,NULL,3659,'Canasta x6',1),(4150,0.00,6,NULL,3660,'Canasta x6',1),(4151,0.00,6,NULL,3661,'Canasta x6',1),(4152,0.00,6,NULL,3662,'Canasta x6',1),(4153,0.00,6,NULL,3663,'Canasta x6',1),(4154,0.00,1,NULL,3664,'Unidad',1),(4155,0.00,1,NULL,3665,'Unidad',1),(4156,0.00,6,NULL,3666,'Canasta x6',1),(4157,0.00,24,NULL,3667,'Canasta x24',1),(4158,0.00,6,NULL,3668,'Canasta x6',1),(4159,0.00,1,NULL,3669,'Unidad',1),(4160,0.00,6,NULL,3670,'Canasta x6',1),(4161,0.00,1,NULL,3671,'Unidad',1),(4162,0.00,1,NULL,3672,'Unidad',1),(4163,0.00,1,NULL,3673,'Unidad',1),(4164,0.00,6,NULL,3674,'Canasta x6',1),(4165,0.00,1,NULL,3675,'Unidad',1),(4166,0.00,1,NULL,3676,'Unidad',1),(4167,0.00,1,NULL,3677,'Unidad',1),(4168,0.00,6,NULL,3678,'Canasta x6',1),(4169,0.00,1,NULL,3679,'Unidad',1),(4170,0.00,6,NULL,3680,'Canasta x6',1),(4171,0.00,1,NULL,3681,'Unidad',1),(4172,0.00,6,NULL,3682,'Canasta x6',1),(4173,0.00,1,NULL,3683,'Unidad',1),(4174,0.00,1,NULL,3684,'Unidad',1),(4175,0.00,1,NULL,3685,'Unidad',1),(4176,0.00,1,NULL,3686,'Unidad',1),(4177,0.00,1,NULL,3687,'Unidad',1),(4178,0.00,1,NULL,3688,'Unidad',1),(4179,0.00,1,NULL,3689,'Unidad',1),(4180,0.00,1,NULL,3690,'Unidad',1),(4181,0.00,1,NULL,3691,'Unidad',1),(4182,0.00,30,NULL,3692,'Canasta x30',1),(4183,0.00,1,NULL,3693,'Unidad',1),(4184,0.00,30,NULL,3694,'Canasta x30',1),(4185,0.00,24,NULL,3695,'Canasta x24',1),(4186,0.00,1,NULL,3696,'Unidad',1),(4187,0.00,24,NULL,3697,'Canasta x24',1),(4188,0.00,30,NULL,3698,'Canasta x30',1),(4189,0.00,1,NULL,3699,'Unidad',1),(4190,0.00,24,NULL,3700,'Canasta x24',1),(4191,0.00,1,NULL,3701,'Unidad',1),(4192,0.00,1,NULL,3702,'Unidad',1),(4193,0.00,1,NULL,3703,'Unidad',1),(4194,0.00,1,NULL,3704,'Unidad',1),(4195,0.00,1,NULL,3705,'Unidad',1),(4196,0.00,1,NULL,3706,'Unidad',1),(4197,0.00,1,NULL,3707,'Unidad',1),(4198,0.00,1,NULL,3708,'Unidad',1),(4199,0.00,1,NULL,3709,'Unidad',1),(4200,0.00,1,NULL,3710,'Unidad',1),(4201,0.00,1,NULL,3711,'Unidad',1),(4202,0.00,1,NULL,3712,'Unidad',1),(4203,0.00,1,NULL,3713,'Unidad',1),(4204,0.00,1,NULL,3714,'Unidad',1),(4205,0.00,1,NULL,3715,'Unidad',1),(4206,0.00,1,NULL,3716,'Unidad',1),(4207,0.00,1,NULL,3717,'Unidad',1),(4208,0.00,1,NULL,3718,'Unidad',1),(4209,0.00,1,NULL,3719,'Unidad',1),(4210,0.00,1,NULL,3720,'Unidad',1),(4211,0.00,1,NULL,3721,'Unidad',1),(4212,0.00,1,NULL,3722,'Unidad',1),(4213,0.00,1,NULL,3723,'Unidad',1),(4214,0.00,1,NULL,3724,'Unidad',1),(4215,0.00,1,NULL,3725,'Unidad',1),(4216,0.00,1,NULL,3726,'Unidad',1),(4217,0.00,1,NULL,3727,'Unidad',1),(4218,0.00,1,NULL,3728,'Unidad',1),(4219,0.00,1,NULL,3729,'Unidad',1),(4220,0.00,1,NULL,3730,'Unidad',1),(4221,0.00,1,NULL,3731,'Unidad',1),(4222,0.00,1,NULL,3732,'Unidad',1),(4223,0.00,1,NULL,3733,'Unidad',1),(4224,0.00,1,NULL,3734,'Unidad',1),(4225,0.00,1,NULL,3735,'Unidad',1),(4226,0.00,1,NULL,3736,'Unidad',1),(4227,0.00,1,NULL,3737,'Unidad',1),(4228,0.00,1,NULL,3738,'Unidad',1),(4229,0.00,1,NULL,3739,'Unidad',1),(4230,0.00,1,NULL,3740,'Unidad',1),(4231,0.00,1,NULL,3741,'Unidad',1),(4232,0.00,1,NULL,3742,'Unidad',1),(4233,0.00,1,NULL,3743,'Unidad',1),(4234,0.00,1,NULL,3744,'Unidad',1),(4235,0.00,1,NULL,3745,'Unidad',1),(4236,0.00,1,NULL,3746,'Unidad',1),(4237,0.00,1,NULL,3747,'Unidad',1),(4238,0.00,1,NULL,3748,'Unidad',1),(4239,0.00,1,NULL,3749,'Unidad',1),(4240,0.00,1,NULL,3750,'Unidad',1),(4241,0.00,1,NULL,3751,'Unidad',1),(4242,0.00,1,NULL,3752,'Unidad',1),(4243,0.00,1,NULL,3753,'Unidad',1),(4244,0.00,1,NULL,3754,'Unidad',1),(4245,0.00,1,NULL,3755,'Unidad',1),(4246,0.00,1,NULL,3756,'Unidad',1),(4247,0.00,1,NULL,3757,'Unidad',1),(4248,0.00,1,NULL,3758,'Unidad',1),(4249,0.00,1,NULL,3759,'Unidad',1),(4250,0.00,1,NULL,3760,'Unidad',1),(4251,0.00,1,NULL,3761,'Unidad',1),(4252,0.00,1,NULL,3762,'Unidad',1),(4253,0.00,1,NULL,3763,'Unidad',1),(4254,0.00,1,NULL,3764,'Unidad',1),(4255,0.00,1,NULL,3765,'Unidad',1),(4256,0.00,1,NULL,3766,'Unidad',1),(4257,0.00,1,NULL,3767,'Unidad',1),(4258,0.00,1,NULL,3768,'Unidad',1),(4259,0.00,1,NULL,3769,'Unidad',1),(4260,0.00,1,NULL,3770,'Unidad',1),(4261,0.00,1,NULL,3771,'Unidad',1),(4262,0.00,1,NULL,3772,'Unidad',1),(4263,0.00,1,NULL,3773,'Unidad',1),(4264,0.00,1,NULL,3774,'Unidad',1),(4265,0.00,1,NULL,3775,'Unidad',1),(4266,0.00,1,NULL,3776,'Unidad',1),(4267,0.00,1,NULL,3777,'Unidad',1),(4268,0.00,1,NULL,3778,'Unidad',1),(4269,0.00,1,NULL,3779,'Unidad',1),(4270,0.00,1,NULL,3780,'Unidad',1),(4271,0.00,1,NULL,3781,'Unidad',1),(4272,0.00,1,NULL,3782,'Unidad',1),(4273,0.00,1,NULL,3783,'Unidad',1),(4274,0.00,1,NULL,3784,'Unidad',1),(4275,0.00,1,NULL,3785,'Unidad',1),(4276,0.00,1,NULL,3786,'Unidad',1),(4277,0.00,1,NULL,3787,'Unidad',1),(4278,0.00,1,NULL,3788,'Unidad',1),(4279,0.00,1,NULL,3789,'Unidad',1),(4280,0.00,1,NULL,3790,'Unidad',1),(4281,0.00,1,NULL,3791,'Unidad',1),(4282,0.00,1,NULL,3792,'Unidad',1),(4283,0.00,1,NULL,3793,'Unidad',1),(4284,0.00,1,NULL,3794,'Unidad',1),(4285,0.00,1,NULL,3795,'Unidad',1),(4286,0.00,1,NULL,3796,'Unidad',1),(4287,0.00,1,NULL,3797,'Unidad',1),(4288,0.00,1,NULL,3798,'Unidad',1),(4289,0.00,1,NULL,3799,'Unidad',1),(4290,0.00,1,NULL,3800,'Unidad',1),(4291,0.00,1,NULL,3801,'Unidad',1),(4292,0.00,1,NULL,3802,'Unidad',1),(4293,0.00,1,NULL,3803,'Unidad',1),(4294,0.00,1,NULL,3804,'Unidad',1),(4295,0.00,1,NULL,3805,'Unidad',1),(4296,0.00,1,NULL,3806,'Unidad',1),(4297,0.00,1,NULL,3807,'Unidad',1),(4298,0.00,1,NULL,3808,'Unidad',1),(4299,0.00,1,NULL,3809,'Unidad',1),(4300,0.00,1,NULL,3810,'Unidad',1),(4301,0.00,1,NULL,3811,'Unidad',1),(4302,0.00,1,NULL,3812,'Unidad',1),(4303,0.00,1,NULL,3813,'Unidad',1),(4304,0.00,1,NULL,3814,'Unidad',1),(4305,0.00,1,NULL,3815,'Unidad',1),(4306,0.00,1,NULL,3816,'Unidad',1),(4307,0.00,1,NULL,3817,'Unidad',1),(4308,0.00,1,NULL,3818,'Unidad',1),(4309,0.00,1,NULL,3819,'Unidad',1),(4310,0.00,1,NULL,3820,'Unidad',1),(4311,0.00,1,NULL,3821,'Unidad',1),(4312,0.00,1,NULL,3822,'Unidad',1),(4313,0.00,1,NULL,3823,'Unidad',1),(4314,0.00,1,NULL,3824,'Unidad',1),(4315,0.00,1,NULL,3825,'Unidad',1),(4316,0.00,1,NULL,3826,'Unidad',1),(4317,0.00,1,NULL,3827,'Unidad',1),(4318,0.00,1,NULL,3828,'Unidad',1),(4319,0.00,1,NULL,3829,'Unidad',1),(4320,0.00,1,NULL,3830,'Unidad',1),(4321,0.00,1,NULL,3831,'Unidad',1),(4322,0.00,1,NULL,3832,'Unidad',1),(4323,0.00,1,NULL,3833,'Unidad',1),(4324,0.00,1,NULL,3834,'Unidad',1),(4325,0.00,1,NULL,3835,'Unidad',1),(4326,0.00,1,NULL,3836,'Unidad',1),(4327,0.00,1,NULL,3837,'Unidad',1),(4328,0.00,1,NULL,3838,'Unidad',1),(4329,0.00,1,NULL,3839,'Unidad',1),(4330,0.00,1,NULL,3840,'Unidad',1),(4331,0.00,1,NULL,3841,'Unidad',1),(4332,0.00,1,NULL,3842,'Unidad',1),(4333,0.00,1,NULL,3843,'Unidad',1),(4334,0.00,1,NULL,3844,'Unidad',1),(4335,0.00,1,NULL,3845,'Unidad',1),(4336,0.00,1,NULL,3846,'Unidad',1),(4337,0.00,1,NULL,3847,'Unidad',1),(4338,0.00,1,NULL,3848,'Unidad',1),(4339,0.00,1,NULL,3849,'Unidad',1),(4340,0.00,1,NULL,3850,'Unidad',1),(4341,0.00,1,NULL,3851,'Unidad',1),(4342,0.00,1,NULL,3852,'Unidad',1),(4343,0.00,1,NULL,3853,'Unidad',1),(4344,0.00,1,NULL,3854,'Unidad',1),(4345,0.00,1,NULL,3855,'Unidad',1),(4346,0.00,1,NULL,3856,'Unidad',1),(4347,0.00,1,NULL,3857,'Unidad',1),(4348,0.00,1,NULL,3858,'Unidad',1),(4349,0.00,1,NULL,3859,'Unidad',1),(4350,0.00,1,NULL,3860,'Unidad',1),(4351,0.00,1,NULL,3861,'Unidad',1),(4352,0.00,1,NULL,3862,'Unidad',1),(4353,0.00,1,NULL,3863,'Unidad',1),(4354,0.00,1,NULL,3864,'Unidad',1),(4355,0.00,1,NULL,3865,'Unidad',1),(4356,0.00,1,NULL,3866,'Unidad',1),(4357,0.00,1,NULL,3867,'Unidad',1),(4358,0.00,1,NULL,3868,'Unidad',1),(4359,0.00,1,NULL,3869,'Unidad',1),(4360,0.00,1,NULL,3870,'Unidad',1),(4361,0.00,1,NULL,3871,'Unidad',1),(4362,0.00,1,NULL,3872,'Unidad',1),(4363,0.00,1,NULL,3873,'Unidad',1),(4364,0.00,1,NULL,3874,'Unidad',1),(4365,0.00,1,NULL,3875,'Unidad',1),(4366,0.00,1,NULL,3876,'Unidad',1),(4367,0.00,1,NULL,3877,'Unidad',1),(4368,0.00,1,NULL,3878,'Unidad',1),(4369,0.00,1,NULL,3879,'Unidad',1),(4370,0.00,1,NULL,3880,'Unidad',1),(4371,0.00,1,NULL,3881,'Unidad',1),(4372,0.00,1,NULL,3882,'Unidad',1),(4373,0.00,1,NULL,3883,'Unidad',1),(4374,0.00,1,NULL,3884,'Unidad',1),(4375,0.00,1,NULL,3885,'Unidad',1),(4376,0.00,1,NULL,3886,'Unidad',1),(4377,0.00,1,NULL,3887,'Unidad',1),(4378,0.00,1,NULL,3888,'Unidad',1),(4379,0.00,1,NULL,3889,'Unidad',1),(4380,0.00,1,NULL,3890,'Unidad',1),(4381,0.00,1,NULL,3891,'Unidad',1),(4382,0.00,1,NULL,3892,'Unidad',1),(4383,0.00,1,NULL,3893,'Unidad',1),(4384,0.00,1,NULL,3894,'Unidad',1),(4385,0.00,1,NULL,3895,'Unidad',1),(4386,0.00,1,NULL,3896,'Unidad',1),(4387,0.00,1,NULL,3897,'Unidad',1),(4388,0.00,1,NULL,3898,'Unidad',1),(4389,0.00,1,NULL,3899,'Unidad',1),(4390,0.00,1,NULL,3900,'Unidad',1),(4391,0.00,1,NULL,3901,'Unidad',1),(4392,0.00,1,NULL,3902,'Unidad',1),(4393,0.00,1,NULL,3903,'Unidad',1),(4394,0.00,1,NULL,3904,'Unidad',1),(4395,0.00,1,NULL,3905,'Unidad',1),(4396,0.00,1,NULL,3906,'Unidad',1),(4397,0.00,1,NULL,3907,'Unidad',1),(4398,0.00,1,NULL,3908,'Unidad',1),(4399,0.00,1,NULL,3909,'Unidad',1),(4400,0.00,1,NULL,3910,'Unidad',1),(4401,0.00,1,NULL,3911,'Unidad',1),(4402,0.00,1,NULL,3912,'Unidad',1),(4403,0.00,1,NULL,3913,'Unidad',1),(4404,0.00,1,NULL,3914,'Unidad',1),(4405,0.00,1,NULL,3915,'Unidad',1),(4406,0.00,1,NULL,3916,'Unidad',1),(4407,0.00,1,NULL,3917,'Unidad',1),(4408,0.00,1,NULL,3918,'Unidad',1),(4409,0.00,1,NULL,3919,'Unidad',1),(4410,0.00,1,NULL,3920,'Unidad',1),(4411,0.00,1,NULL,3921,'Unidad',1),(4412,0.00,1,NULL,3922,'Unidad',1),(4413,0.00,1,NULL,3923,'Unidad',1),(4414,0.00,1,NULL,3924,'Unidad',1),(4415,0.00,1,NULL,3925,'Unidad',1),(4416,0.00,1,NULL,3926,'Unidad',1),(4417,0.00,1,NULL,3927,'Unidad',1),(4418,0.00,1,NULL,3928,'Unidad',1),(4419,0.00,1,NULL,3929,'Unidad',1),(4420,0.00,1,NULL,3930,'Unidad',1),(4421,0.00,1,NULL,3931,'Unidad',1),(4422,0.00,1,NULL,3932,'Unidad',1),(4423,0.00,1,NULL,3933,'Unidad',1),(4424,0.00,1,NULL,3934,'Unidad',1),(4425,0.00,1,NULL,3935,'Unidad',1),(4426,0.00,1,NULL,3936,'Unidad',1),(4427,0.00,1,NULL,3937,'Unidad',1),(4428,0.00,1,NULL,3938,'Unidad',1),(4429,0.00,1,NULL,3939,'Unidad',1),(4430,0.00,1,NULL,3940,'Unidad',1),(4431,0.00,1,NULL,3941,'Unidad',1),(4432,0.00,1,NULL,3942,'Unidad',1),(4433,0.00,1,NULL,3943,'Unidad',1),(4434,0.00,1,NULL,3944,'Unidad',1),(4435,0.00,1,NULL,3945,'Unidad',1),(4436,0.00,1,NULL,3946,'Unidad',1),(4437,0.00,1,NULL,3947,'Unidad',1),(4438,0.00,1,NULL,3948,'Unidad',1),(4439,0.00,1,NULL,3949,'Unidad',1),(4440,0.00,1,NULL,3950,'Unidad',1),(4441,0.00,1,NULL,3951,'Unidad',1),(4442,0.00,1,NULL,3952,'Unidad',1),(4443,0.00,1,NULL,3953,'Unidad',1),(4444,0.00,1,NULL,3954,'Unidad',1),(4445,0.00,1,NULL,3955,'Unidad',1),(4446,0.00,1,NULL,3956,'Unidad',1),(4447,0.00,1,NULL,3957,'Unidad',1),(4448,0.00,1,NULL,3958,'Unidad',1),(4449,0.00,1,NULL,3959,'Unidad',1),(4450,0.00,1,NULL,3960,'Unidad',1),(4451,0.00,1,NULL,3961,'Unidad',1),(4452,0.00,1,NULL,3962,'Unidad',1),(4453,0.00,1,NULL,3963,'Unidad',1),(4454,0.00,1,NULL,3964,'Unidad',1),(4455,0.00,1,NULL,3965,'Unidad',1),(4456,0.00,1,NULL,3966,'Unidad',1),(4457,0.00,1,NULL,3967,'Unidad',1),(4458,0.00,1,NULL,3968,'Unidad',1),(4459,0.00,1,NULL,3969,'Unidad',1),(4460,0.00,1,NULL,3970,'Unidad',1),(4461,0.00,1,NULL,3971,'Unidad',1),(4462,0.00,1,NULL,3972,'Unidad',1),(4463,0.00,1,NULL,3973,'Unidad',1),(4464,0.00,1,NULL,3974,'Unidad',1),(4465,0.00,1,NULL,3975,'Unidad',1),(4466,0.00,1,NULL,3976,'Unidad',1),(4467,0.00,1,NULL,3977,'Unidad',1),(4468,0.00,1,NULL,3978,'Unidad',1),(4469,0.00,1,NULL,3979,'Unidad',1),(4470,0.00,1,NULL,3980,'Unidad',1),(4471,0.00,1,NULL,3981,'Unidad',1),(4472,0.00,1,NULL,3982,'Unidad',1),(4473,0.00,1,NULL,3983,'Unidad',1),(4474,0.00,1,NULL,3984,'Unidad',1),(4475,0.00,30,NULL,3985,'Canasta x30',1),(4476,0.00,6,NULL,3986,'Canasta x6',1),(4477,0.00,24,NULL,3987,'Canasta x24',1),(4478,0.00,6,NULL,3988,'Canasta x6',1),(4479,0.00,1,NULL,3989,'Unidad',1),(4480,0.00,6,NULL,3990,'Canasta x6',1),(4481,0.00,15,NULL,3991,'Canasta x15',1),(4482,0.00,30,NULL,3992,'Canasta x30',1),(4483,0.00,30,NULL,3993,'Canasta x30',1),(4484,0.00,1,NULL,3994,'Unidad',1),(4485,0.00,12,NULL,3995,'Canasta x12',1),(4486,0.00,1,NULL,3996,'Unidad',1),(4487,0.00,1,NULL,3997,'Unidad',1),(4488,0.00,1,NULL,3998,'Unidad',1),(4489,0.00,1,NULL,3999,'Unidad',1),(4490,0.00,1,NULL,4000,'Unidad',1),(4491,0.00,1,NULL,4001,'Unidad',1),(4492,0.00,1,NULL,4002,'Unidad',1),(4493,0.00,12,NULL,4003,'Canasta x12',1),(4494,0.00,1,NULL,4004,'Unidad',1),(4495,0.00,1,NULL,4005,'Unidad',1),(4496,0.00,1,NULL,4006,'Unidad',1),(4497,0.00,1,NULL,4007,'Unidad',1),(4498,0.00,1,NULL,4008,'Unidad',1),(4499,0.00,1,NULL,4009,'Unidad',1),(4500,0.00,1,NULL,4010,'Unidad',1),(4501,0.00,12,NULL,4011,'Canasta x12',1),(4502,0.00,9,NULL,4012,'Canasta x9',1),(4503,0.00,8,NULL,4013,'Canasta x8',1),(4504,0.00,6,NULL,4014,'Canasta x6',1),(4505,0.00,1,NULL,4015,'Unidad',1),(4506,0.00,1,NULL,4016,'Unidad',1),(4507,0.00,1,NULL,4017,'Unidad',1),(4508,0.00,1,NULL,4018,'Unidad',1),(4509,0.00,1,NULL,4019,'Unidad',1),(4510,0.00,1,NULL,4020,'Unidad',1),(4511,0.00,1,NULL,4021,'Unidad',1),(4512,0.00,8,NULL,4022,'Canasta x8',1),(4513,0.00,1,NULL,4023,'Unidad',1),(4514,0.00,1,NULL,4024,'Unidad',1),(4515,0.00,1,NULL,4025,'Unidad',1),(4516,0.00,1,NULL,4026,'Unidad',1),(4517,0.00,1,NULL,4027,'Unidad',1),(4518,0.00,1,NULL,4028,'Unidad',1),(4519,0.00,12,NULL,4029,'Canasta x12',1),(4520,0.00,1,NULL,4030,'Unidad',1),(4521,0.00,1,NULL,4031,'Unidad',1),(4522,0.00,1,NULL,4032,'Unidad',1),(4523,0.00,1,NULL,4033,'Unidad',1),(4524,0.00,1,NULL,4034,'Unidad',1),(4525,0.00,1,NULL,4035,'Unidad',1),(4526,0.00,1,NULL,4036,'Unidad',1),(4527,0.00,1,NULL,4037,'Unidad',1),(4528,0.00,1,NULL,4038,'Unidad',1),(4529,0.00,1,NULL,4039,'Unidad',1),(4530,0.00,12,NULL,4040,'Canasta x12',1),(4531,0.00,24,NULL,4041,'Canasta x24',1),(4532,0.00,1,NULL,4042,'Unidad',1),(4533,0.00,12,NULL,4043,'Canasta x12',1),(4534,0.00,1,NULL,4044,'Unidad',1),(4535,0.00,12,NULL,4045,'Canasta x12',1),(4536,0.00,1,NULL,4046,'Unidad',1),(4537,0.00,12,NULL,4047,'Canasta x12',1),(4538,0.00,1,NULL,4048,'Unidad',1),(4539,0.00,15,NULL,4049,'Canasta x15',1),(4540,0.00,15,NULL,4050,'Canasta x15',1),(4541,0.00,1,NULL,4051,'Unidad',1),(4542,0.00,1,NULL,4052,'Unidad',1),(4543,0.00,8,NULL,4053,'Canasta x8',1),(4544,0.00,8,NULL,4054,'Canasta x8',1),(4545,0.00,12,NULL,4055,'Canasta x12',1),(4546,0.00,6,NULL,4056,'Canasta x6',1),(4547,0.00,1,NULL,4057,'Unidad',1),(4548,0.00,15,NULL,4058,'Canasta x15',1),(4549,0.00,12,NULL,4059,'Canasta x12',1),(4550,0.00,15,NULL,4060,'Canasta x15',1),(4551,0.00,1,NULL,4061,'Unidad',1),(4552,0.00,1,NULL,4062,'Unidad',1),(4553,0.00,1,NULL,4063,'Unidad',1),(4554,0.00,1,NULL,4064,'Unidad',1),(4555,0.00,1,NULL,4065,'Unidad',1),(4556,0.00,1,NULL,4066,'Unidad',1),(4557,0.00,1,NULL,4067,'Unidad',1),(4558,0.00,1,NULL,4068,'Unidad',1),(4559,0.00,1,NULL,4069,'Unidad',1),(4560,0.00,6,NULL,4070,'Canasta x6',1),(4561,0.00,6,NULL,4071,'Canasta x6',1),(4562,0.00,1,NULL,4072,'Unidad',1),(4563,0.00,1,NULL,4073,'Unidad',1),(4564,0.00,1,NULL,4074,'Unidad',1),(4565,0.00,1,NULL,4075,'Unidad',1),(4566,0.00,1,NULL,4076,'Unidad',1),(4567,0.00,1,NULL,4077,'Unidad',1),(4568,0.00,1,NULL,4078,'Unidad',1),(4569,0.00,24,NULL,4079,'Canasta x24',1),(4570,0.00,24,NULL,4080,'Canasta x24',1),(4571,0.00,1,NULL,4081,'Unidad',1),(4572,0.00,1,NULL,4082,'Unidad',1),(4573,0.00,6,NULL,4083,'Canasta x6',1),(4574,0.00,6,NULL,4084,'Canasta x6',1),(4575,0.00,1,NULL,4085,'Unidad',1),(4576,0.00,1,NULL,4086,'Unidad',1),(4577,0.00,1,NULL,4087,'Unidad',1),(4578,0.00,1,NULL,4088,'Unidad',1),(4579,0.00,2,NULL,4089,'Canasta x2',1),(4580,0.00,6,NULL,4090,'Canasta x6',1),(4581,0.00,12,NULL,4091,'Canasta x12',1),(4582,0.00,6,NULL,4092,'Canasta x6',1),(4583,0.00,1,NULL,4093,'Unidad',1),(4584,0.00,6,NULL,4094,'Canasta x6',1),(4585,0.00,12,NULL,4095,'Canasta x12',1),(4586,0.00,12,NULL,4096,'Canasta x12',1),(4587,0.00,1,NULL,4097,'Unidad',1),(4588,0.00,24,NULL,4098,'Canasta x24',1),(4589,0.00,1,NULL,4099,'Unidad',1),(4590,0.00,1,NULL,4100,'Unidad',1),(4591,0.00,12,NULL,4101,'Canasta x12',1),(4592,0.00,12,NULL,4102,'Canasta x12',1),(4593,0.00,12,NULL,4103,'Canasta x12',1),(4594,0.00,1,NULL,4104,'Unidad',1),(4595,0.00,1,NULL,4105,'Unidad',1),(4596,0.00,12,NULL,4106,'Canasta x12',1),(4597,0.00,15,NULL,4107,'Canasta x15',1),(4598,50000.00,12,'None',4108,'Canasta x12',1),(4599,0.00,1,NULL,4109,'Unidad',1),(4600,0.00,1,NULL,4110,'Unidad',1),(4601,0.00,1,NULL,4111,'Unidad',1),(4602,0.00,24,NULL,4112,'Canasta x24',1),(4603,0.00,1,NULL,4113,'Unidad',1),(4604,0.00,24,NULL,4114,'Canasta x24',1),(4605,0.00,24,NULL,4115,'Canasta x24',1),(4606,0.00,12,NULL,4116,'Canasta x12',1),(4607,0.00,1,NULL,4117,'Unidad',1),(4608,0.00,1,NULL,4118,'Unidad',1),(4609,0.00,12,NULL,4119,'Canasta x12',1),(4610,0.00,12,NULL,4120,'Canasta x12',1),(4611,0.00,1,NULL,4121,'Unidad',1),(4612,0.00,12,NULL,4122,'Canasta x12',1),(4613,0.00,1,NULL,4123,'Unidad',1),(4614,0.00,1,NULL,4124,'Unidad',1),(4615,0.00,1,NULL,4125,'Unidad',1),(4616,0.00,1,NULL,4126,'Unidad',1),(4617,0.00,1,NULL,4127,'Unidad',1),(4618,0.00,1,NULL,4128,'Unidad',1),(4619,0.00,1,NULL,4129,'Unidad',1),(4620,0.00,1,NULL,4130,'Unidad',1),(4621,0.00,1,NULL,4131,'Unidad',1),(4622,0.00,24,NULL,4132,'Canasta x24',1),(4623,0.00,30,NULL,4133,'Canasta x30',1),(4624,0.00,1,NULL,4134,'Unidad',1),(4625,0.00,4,NULL,4135,'Canasta x4',1),(4626,0.00,1,NULL,4136,'Unidad',1),(4627,0.00,1,NULL,4137,'Unidad',1),(4628,0.00,1,NULL,4138,'Unidad',1),(4629,0.00,1,NULL,4139,'Unidad',1),(4630,0.00,1,NULL,4140,'Unidad',1),(4631,0.00,1,NULL,4141,'Unidad',1),(4632,0.00,1,NULL,4142,'Unidad',1),(4633,0.00,1,NULL,4143,'Unidad',1),(4634,0.00,1,NULL,4144,'Unidad',1),(4635,0.00,1,NULL,4145,'Unidad',1),(4636,0.00,1,NULL,4146,'Unidad',1),(4637,0.00,1,NULL,4147,'Unidad',1),(4638,0.00,1,NULL,4148,'Unidad',1),(4639,0.00,1,NULL,4149,'Unidad',1),(4640,0.00,1,NULL,4150,'Unidad',1);
/*!40000 ALTER TABLE `presentacion_producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto` (
  `codigo_producto` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) NOT NULL,
  `descripcion` longtext NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `codigo_categoria` int DEFAULT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`codigo_producto`),
  KEY `producto_codigo_categoria_03e2a6bb_fk_categoria_codigo_categoria` (`codigo_categoria`),
  CONSTRAINT `producto_codigo_categoria_03e2a6bb_fk_categoria_codigo_categoria` FOREIGN KEY (`codigo_categoria`) REFERENCES `categoria` (`codigo_categoria`)
) ENGINE=InnoDB AUTO_INCREMENT=4151 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto`
--

LOCK TABLES `producto` WRITE;
/*!40000 ALTER TABLE `producto` DISABLE KEYS */;
INSERT INTO `producto` VALUES (1,'cocacola','Bebidas sin alcohol','2026-09-17',53,1),(3630,'AGUILA','Cervezas',NULL,49,1),(3631,'AGUILA 1 LT *13','Cervezas',NULL,49,1),(3632,'AGUILA IMPERIAL','Cervezas',NULL,49,1),(3633,'AGUILA 750','Cervezas',NULL,49,1),(3634,'BACANA X 30','Cervezas',NULL,49,1),(3635,'CLUB 850 *13','Cervezas',NULL,49,1),(3636,'CLUB COL','Cervezas',NULL,49,1),(3637,'CORONA RET','Cervezas',NULL,49,1),(3638,'CLUB ROJA','Cervezas',NULL,49,1),(3639,'COLA Y POLA X 30','Cervezas',NULL,49,1),(3640,'POKER 1 LT x13','Cervezas',NULL,49,1),(3641,'COSTEÑA','Cervezas',NULL,49,1),(3642,'CLUB TRIGO','Cervezas',NULL,49,1),(3643,'COSTEÑA 750 *16','Cervezas',NULL,49,1),(3644,'POKER 750','Cervezas',NULL,49,1),(3645,'LIGHT','Cervezas',NULL,49,1),(3646,'POKER','Cervezas',NULL,49,1),(3647,'LIGHT 1.000','Cervezas',NULL,49,1),(3648,'LIGHT 750','Cervezas',NULL,49,1),(3649,'ANDINA 750*16','Cervezas',NULL,49,1),(3650,'TEKATE 750 X16','Cervezas',NULL,49,1),(3651,'AGUILA 269 x6','Cervezas',NULL,49,1),(3652,'AGUILA LATA x6','Cervezas',NULL,49,1),(3653,'AZTECA X6','Cervezas',NULL,49,1),(3654,'BACANA LATA','Cervezas',NULL,49,1),(3655,'BACANA 269','Cervezas',NULL,49,1),(3656,'CLUB 473','Cervezas',NULL,49,1),(3657,'CLUB TRIGO LT','Cervezas',NULL,49,1),(3658,'BUDW LATA 269x6','Cervezas',NULL,49,1),(3659,'BUDWISER BT 250x6','Cervezas',NULL,49,1),(3660,'CLUB DORADA lata 330 x6','Cervezas',NULL,49,1),(3661,'CLUB NEGRA lata x6','Cervezas',NULL,49,1),(3662,'CLUB ROJA lata x6','Cervezas',NULL,49,1),(3663,'COLA Y POLA 1,5LTS X6','Cervezas',NULL,49,1),(3664,'COLA Y POLA 330 SIX','Cervezas',NULL,49,1),(3665,'águila Zero lata','Cervezas',NULL,49,1),(3666,'CORONA 330 bt x6','Cervezas',NULL,49,1),(3667,'CORONA CERO X 24','Cervezas',NULL,49,1),(3668,'CORONA LATA 269 x6','Cervezas',NULL,49,1),(3669,'CORONA LATA 473','Cervezas',NULL,49,1),(3670,'CORONITA 210 x6','Cervezas',NULL,49,1),(3671,'KAWFFMAN','Cervezas',NULL,49,1),(3672,'MODELO X SXP','Cervezas',NULL,49,1),(3673,'Corona de Zero lata','Cervezas',NULL,49,1),(3674,'LIGHT LATA 330X6','Cervezas',NULL,49,1),(3675,'LIKES 300 X UND','Cervezas',NULL,49,1),(3676,'MICHELOB 269 lata','Cervezas',NULL,49,1),(3677,'Poker 473','Cervezas',NULL,49,1),(3678,'POKER LATA 330X6','Cervezas',NULL,49,1),(3679,'REDDS LATA','Cervezas',NULL,49,1),(3680,'STELLA Bt x6','Cervezas',NULL,49,1),(3681,'STELLA LT SXP','Cervezas',NULL,49,1),(3682,'AGUILA 473 X6','Cervezas',NULL,49,1),(3683,'AGUILA 473 X6 Light','Cervezas',NULL,49,1),(3684,'águila light 269','Cervezas',NULL,49,1),(3685,'ANDINA LATA 310','Cervezas',NULL,49,1),(3686,'ANDINA LATA 269','Cervezas',NULL,49,1),(3687,'ANDINA LIGHT 269','Cervezas',NULL,49,1),(3688,'ANDINA LIGHT BOTELLA','Cervezas',NULL,49,1),(3689,'Heineken 0.0','Cervezas',NULL,49,1),(3690,'ANDINA REFAJO LATA','Cervezas',NULL,49,1),(3691,'ANDINA REFAJO 1.5','Cervezas',NULL,49,1),(3692,'ANDINA X 30','Cervezas',NULL,49,1),(3693,'HEINEKEN 269 lata','Cervezas',NULL,49,1),(3694,'HEINEKEN 250 x 30','Cervezas',NULL,49,1),(3695,'HEINEKEN 250 x 24','Cervezas',NULL,49,1),(3696,'HEINEKEN 310 LATA','Cervezas',NULL,49,1),(3697,'HEINEKEN 330 *24','Cervezas',NULL,49,1),(3698,'CENTRAL 330*30','Cervezas',NULL,49,1),(3699,'CENTRAL 330*LATA','Cervezas',NULL,49,1),(3700,'SOL 330*24','Cervezas',NULL,49,1),(3701,'SOL 250 X 24 BOT','Cervezas',NULL,49,1),(3702,'SOL LATA 310','Cervezas',NULL,49,1),(3703,'TEKATE 330 BOTELLA','Cervezas',NULL,49,1),(3704,'TECATE LATA','Cervezas',NULL,49,1),(3705,'MILLER LITE 250','Cervezas',NULL,49,1),(3706,'TRES COR*24 310cc Rose Lata','Cervezas',NULL,49,1),(3707,'TRES CORDILLERAS*24 300cc Rose','Cervezas',NULL,49,1),(3708,'TRES CORDILLERAS*24 300cc','Cervezas',NULL,49,1),(3709,'LIDER BOTELLA','Aguardientes y rones',NULL,50,1),(3710,'LIDER GARRAFA','Aguardientes y rones',NULL,50,1),(3711,'LIDER MEDIA','Aguardientes y rones',NULL,50,1),(3712,'LIDER 750 PET','Aguardientes y rones',NULL,50,1),(3713,'LIDER 2 LTS','Aguardientes y rones',NULL,50,1),(3714,'LIDER QUARTO AZUL','Aguardientes y rones',NULL,50,1),(3715,'LIDER ROJO BOTELLA','Aguardientes y rones',NULL,50,1),(3716,'LIDER ROJO MEDIA','Aguardientes y rones',NULL,50,1),(3717,'LIDER ROJO QUARTO','Aguardientes y rones',NULL,50,1),(3718,'LIDER VERDE 2 LITROS','Aguardientes y rones',NULL,50,1),(3719,'LIDER VERDE BOTELLA','Aguardientes y rones',NULL,50,1),(3720,'LIDER VERDE MEDIA','Aguardientes y rones',NULL,50,1),(3721,'LIDER BOTELLA PET VERDE','Aguardientes y rones',NULL,50,1),(3722,'LIDER QUARTO VERDE','Aguardientes y rones',NULL,50,1),(3723,'ONIX EDICION LIMITADA','Aguardientes y rones',NULL,50,1),(3724,'ONIX SELLO NEGRO ENVEGECIDO','Aguardientes y rones',NULL,50,1),(3725,'ONIX GARRAFA','Aguardientes y rones',NULL,50,1),(3726,'ONIX BOTELLA 24ª','Aguardientes y rones',NULL,50,1),(3727,'ONIX BOTELLA 24ª 375','Aguardientes y rones',NULL,50,1),(3728,'ONIX BOTELLA 24ª PET','Aguardientes y rones',NULL,50,1),(3729,'ONIX BOTELLA','Aguardientes y rones',NULL,50,1),(3730,'ONIX MEDIA','Aguardientes y rones',NULL,50,1),(3731,'ONIX 24 QUARTO','Aguardientes y rones',NULL,50,1),(3732,'ONIX SIN AZÚCAR 750','Aguardientes y rones',NULL,50,1),(3733,'ONIX SIN AZÚCAR 375','Aguardientes y rones',NULL,50,1),(3734,'ONIX SIN AZÚCAR 175','Aguardientes y rones',NULL,50,1),(3735,'ANTIOQUEÑO 750','Aguardientes y rones',NULL,50,1),(3736,'ANTIOQUEÑO 375','Aguardientes y rones',NULL,50,1),(3737,'ANTIOQUEÑO 750 VERDE','Aguardientes y rones',NULL,50,1),(3738,'ANTIOQUEÑO 375 VERDE','Aguardientes y rones',NULL,50,1),(3739,'AGUARDIENTE BLANCO','Aguardientes y rones',NULL,50,1),(3740,'RON BOYACA 5 AÑOS','Aguardientes y rones',NULL,50,1),(3741,'RON BOYACA 8 AÑOS','Aguardientes y rones',NULL,50,1),(3742,'RON BOYACA 12 AÑOS','Aguardientes y rones',NULL,50,1),(3743,'RON BOYACA BOTELLA','Aguardientes y rones',NULL,50,1),(3744,'RON BOYACA MEDIA','Aguardientes y rones',NULL,50,1),(3745,'RON BOYACÁ QUARTO','Aguardientes y rones',NULL,50,1),(3746,'AMARILLO 750','Aguardientes y rones',NULL,50,1),(3747,'AMARILLO 375','Aguardientes y rones',NULL,50,1),(3748,'AMARILLO 1 LT TBK','Aguardientes y rones',NULL,50,1),(3749,'AMARILLO GARRAFA','Aguardientes y rones',NULL,50,1),(3750,'AMARILLO 1 LT BOT','Aguardientes y rones',NULL,50,1),(3751,'RON CALDAS BOTELLA OSCURO','Aguardientes y rones',NULL,50,1),(3752,'RON CALDAS 1.000','Aguardientes y rones',NULL,50,1),(3753,'RON CALDAS BOTELLA','Aguardientes y rones',NULL,50,1),(3754,'RON CALDAS MEDIA','Aguardientes y rones',NULL,50,1),(3755,'RON CALDAS QUARTO','Aguardientes y rones',NULL,50,1),(3756,'RON CALDAS 5 AÑOS BOTELLA','Aguardientes y rones',NULL,50,1),(3757,'RON CALDAS 5 AÑOS MEDIA','Aguardientes y rones',NULL,50,1),(3758,'RON CALDAS 8 AÑOS BOTELLA','Aguardientes y rones',NULL,50,1),(3759,'RON CALDAS 8 AÑOS MEDIA','Aguardientes y rones',NULL,50,1),(3760,'RON CALDAS BLANCA','Aguardientes y rones',NULL,50,1),(3761,'RON CREMA','Aguardientes y rones',NULL,50,1),(3762,'RON CALDAS 15 AÑOS','Aguardientes y rones',NULL,50,1),(3763,'RON CALDAS LICOR 750','Aguardientes y rones',NULL,50,1),(3764,'RON CALDAS LICOR 375','Aguardientes y rones',NULL,50,1),(3765,'MOLENDERO','Aguardientes y rones',NULL,50,1),(3766,'RON TROPICO','Aguardientes y rones',NULL,50,1),(3767,'RON SANTERO X 750ML','Aguardientes y rones',NULL,50,1),(3768,'BACARDI LIMON X 750 ML','Aguardientes y rones',NULL,50,1),(3769,'BACARDI LIMON X 375ML','Aguardientes y rones',NULL,50,1),(3770,'BACARDI CARTA BLANCA X 980ML','Aguardientes y rones',NULL,50,1),(3771,'BACARDI CARTA BLANCA X 750 ML','Aguardientes y rones',NULL,50,1),(3772,'BACARDI CARTA BLANCA X 1750 ML','Aguardientes y rones',NULL,50,1),(3773,'BACARDI AÑEJO','Aguardientes y rones',NULL,50,1),(3774,'BACARDI MOJITO','Aguardientes y rones',NULL,50,1),(3775,'BACARDI ZOMBIE','Aguardientes y rones',NULL,50,1),(3776,'BACARDI BAHAMA','Aguardientes y rones',NULL,50,1),(3777,'BACARDI MANDARINA','Aguardientes y rones',NULL,50,1),(3778,'BACARDI X 200ML RON','Aguardientes y rones',NULL,50,1),(3779,'WHISKY BUCHANANS X 1000 master','Destilados importados',NULL,51,1),(3780,'WHISKY BUCHANANS X 750 master','Destilados importados',NULL,51,1),(3781,'WHISKY BUCHANANS TWO SOULS X 750ML','Destilados importados',NULL,51,1),(3782,'WHISKY BUCHANANS 12 AÑOS X 1000ML','Destilados importados',NULL,51,1),(3783,'WHISKY BUCHANANS 12 AÑOS X 750ML','Destilados importados',NULL,51,1),(3784,'WHISKY BUCHANANS 12 AÑOS X 375ML','Destilados importados',NULL,51,1),(3785,'WHISKY BUCHANANS 12 AÑOS X 200ML','Destilados importados',NULL,51,1),(3786,'WHISKY OLD PAR X 1000ML','Destilados importados',NULL,51,1),(3787,'WHISKY OLD PAR X 750ML','Destilados importados',NULL,51,1),(3788,'WHISKY OLD PAR X 500ML','Destilados importados',NULL,51,1),(3789,'WHISKY JHONNIE WALKER DOBLE BLACK X 700ML','Destilados importados',NULL,51,1),(3790,'WHISKY JHONNIE WALKER BLACK X 1000ML','Destilados importados',NULL,51,1),(3791,'WHISKY JHONNIE WALKER BLACK X 700ML','Destilados importados',NULL,51,1),(3792,'WHISKY JHONNIE WALKER BLACK X 375ML','Destilados importados',NULL,51,1),(3793,'WHISKY JHONNIE WALKER RED X 1000ML','Destilados importados',NULL,51,1),(3794,'WHISKY JHONNIE WALKER RED X 700ML','Destilados importados',NULL,51,1),(3795,'WHISKY JHONNIE WALKER RED X 375ML','Destilados importados',NULL,51,1),(3796,'WHISKY JHONNIE WALKER RED X 200ML','Destilados importados',NULL,51,1),(3797,'WHISKY CHIVAS 13 AÑOS X 1000ML','Destilados importados',NULL,51,1),(3798,'WHISKY CHIVAS EXTRA X 750ML','Destilados importados',NULL,51,1),(3799,'WHISKY CHIVAS EXTRA VASOS','Destilados importados',NULL,51,1),(3800,'WHISKY CHIVAS EXTRA X 375ML','Destilados importados',NULL,51,1),(3801,'WHISKY CHIVAS 12 AÑOS X 1000ML','Destilados importados',NULL,51,1),(3802,'WHISKY CHIVAS 12 Años X 700ML','Destilados importados',NULL,51,1),(3803,'WHISKY CHIVAS 12 AÑOS X 375ML','Destilados importados',NULL,51,1),(3804,'WHISKY ROYAL CHOICE','Destilados importados',NULL,51,1),(3805,'CLAN MAGREGOR 750','Destilados importados',NULL,51,1),(3806,'CLAN MAGREGOR 375','Destilados importados',NULL,51,1),(3807,'THE GLENLIVET','Destilados importados',NULL,51,1),(3808,'DEWARS 12 AÑOS','Destilados importados',NULL,51,1),(3809,'WHISKY JACK DANIELS X 750ML HONEY','Destilados importados',NULL,51,1),(3810,'WHISKY JACK DANIELS X 750ML MNZ','Destilados importados',NULL,51,1),(3811,'WHISKY JACK DANIELS X 750ML N\'7','Destilados importados',NULL,51,1),(3812,'WHISKY JACK DANIELS X 375ML','Destilados importados',NULL,51,1),(3813,'WHISKY JACK DANIELS X 200ML','Destilados importados',NULL,51,1),(3814,'WHISKY JACK DANIELS X 50ML','Destilados importados',NULL,51,1),(3815,'BALLANTINES X 1000ML','Destilados importados',NULL,51,1),(3816,'BALLANTINES X 700ML','Destilados importados',NULL,51,1),(3817,'BALLANTINES X 375ML','Destilados importados',NULL,51,1),(3818,'BALLANTINES X 200ML','Destilados importados',NULL,51,1),(3819,'WHISKY BLACK AND WHITE X 1000ML','Destilados importados',NULL,51,1),(3820,'WHISKY BLACK AND WHITE X 1500ML','Destilados importados',NULL,51,1),(3821,'WHISKY BLACK AND WHITE X 700ML','Destilados importados',NULL,51,1),(3822,'WHISKY BLACK AND WHITE X 375ML','Destilados importados',NULL,51,1),(3823,'WHISKY BLACK AND WHITE X 200ML','Destilados importados',NULL,51,1),(3824,'WHISKY SOMETHING SPECIAL X 1000ML','Destilados importados',NULL,51,1),(3825,'WHISKY SOMETHING SPECIAL X 700ML','Destilados importados',NULL,51,1),(3826,'WHISKY SOMETHING SPECIAL X 375ML','Destilados importados',NULL,51,1),(3827,'WHISKY SOMETHING SPECIAL X 200 ML','Destilados importados',NULL,51,1),(3828,'WHISKY PASSPORT X 1000ML','Destilados importados',NULL,51,1),(3829,'WHISKY PASSPORT X 700ML','Destilados importados',NULL,51,1),(3830,'WHISKY PASSPORT X 500ML','Destilados importados',NULL,51,1),(3831,'WHISKY PASSPORT X 200ML','Destilados importados',NULL,51,1),(3832,'WHISKY VAT 69','Destilados importados',NULL,51,1),(3833,'JOHN THOMAS X 750ML','Destilados importados',NULL,51,1),(3834,'JOHN THOMAS X 375ML','Destilados importados',NULL,51,1),(3835,'JOHN THOMAS AZUL X 375ML','Destilados importados',NULL,51,1),(3836,'JOHN THOMAS AZUL X 750 ML','Destilados importados',NULL,51,1),(3837,'JAMESON X 750 ML','Destilados importados',NULL,51,1),(3838,'JAMESON X 375 ML','Destilados importados',NULL,51,1),(3839,'SIR EDWARDS X 750ML','Destilados importados',NULL,51,1),(3840,'SIR EDWARS X 375 ML','Destilados importados',NULL,51,1),(3841,'WHISKY HARRY 700','Destilados importados',NULL,51,1),(3842,'WHISKY GRANS X 1.750','Destilados importados',NULL,51,1),(3843,'WHISKY GRANS X 1000','Destilados importados',NULL,51,1),(3844,'WHISKY GRANS X 700','Destilados importados',NULL,51,1),(3845,'WHISKY GRANS X 350','Destilados importados',NULL,51,1),(3846,'WHISKY GRANS X 200','Destilados importados',NULL,51,1),(3847,'WHISKY SINGLETON 12 AÑOS X 750ML','Destilados importados',NULL,51,1),(3848,'WHISKY GRANDS CAJA AZUL X 750ML','Destilados importados',NULL,51,1),(3849,'WHISKY GRANDS DUGGANS X 750ML','Destilados importados',NULL,51,1),(3850,'WHISKY HAWARD','Destilados importados',NULL,51,1),(3851,'WHISKY BLACK JAC 750','Destilados importados',NULL,51,1),(3852,'WHISKY BLACK JAC 375','Destilados importados',NULL,51,1),(3853,'WHISKY CASTLE HAUSE','Destilados importados',NULL,51,1),(3854,'VODKA SMIRNOFF TAMARINDO X 750ML','Destilados importados',NULL,51,1),(3855,'VODKA SMIRNOFF LULO X 1000ML','Destilados importados',NULL,51,1),(3856,'VODKA SMIRNOFF LULO X 750ML','Destilados importados',NULL,51,1),(3857,'VODKA SMIRNOFF LULO X 375ML','Destilados importados',NULL,51,1),(3858,'VODKA ABSOLUT ORIGINAL X 700ML','Destilados importados',NULL,51,1),(3859,'VODKA ABSOLUT ORIGINAL X 375ML','Destilados importados',NULL,51,1),(3860,'VODKA ABSOLUT CITRON X 700ML','Destilados importados',NULL,51,1),(3861,'VODKA ABSOLUT MANDARIN X 700ML','Destilados importados',NULL,51,1),(3862,'VODKA TROPCAYA','Destilados importados',NULL,51,1),(3863,'VODKA STALINAYA X 700 ML','Destilados importados',NULL,51,1),(3864,'TEQUILA EL JIMADOR REP X 1000','Destilados importados',NULL,51,1),(3865,'TEQUILA EL JIMADOR X 750ML','Destilados importados',NULL,51,1),(3866,'TEQUILA EL JIMADOR X 750ML Cristalino','Destilados importados',NULL,51,1),(3867,'TEQUILA EL JIMADOR X 375ML','Destilados importados',NULL,51,1),(3868,'TEQUILA EL JIMADOR BLANCO','Destilados importados',NULL,51,1),(3869,'TEQUILA NEWTON 1 LT','Destilados importados',NULL,51,1),(3870,'TEQUILA NEWTON 1 LT REP','Destilados importados',NULL,51,1),(3871,'TEQUILA PUERTA NEGRA','Destilados importados',NULL,51,1),(3872,'TEQUILA DON JULIO Blanco','Destilados importados',NULL,51,1),(3873,'TEQUILA JOSE CUERVO REPOSADO X 750ML','Destilados importados',NULL,51,1),(3874,'TEQUILA JOSE CUERVO REPOSADO X 375ML','Destilados importados',NULL,51,1),(3875,'TEQUILA JOSE CUERVO AZUL X 750ML','Destilados importados',NULL,51,1),(3876,'TEQUILA 3 CABALLOS REPOSADO X 1000ML','Destilados importados',NULL,51,1),(3877,'TEQUILA 3 CABALLOS GOLD X 750ML','Destilados importados',NULL,51,1),(3878,'TEQUILA 3 CABALLOS GOLD X 375 ML','Destilados importados',NULL,51,1),(3879,'TEQUILA 3 CABALLOS GOLD X 1000','Destilados importados',NULL,51,1),(3880,'TEQUILA OLMECA REPOSADO X 1000ML','Destilados importados',NULL,51,1),(3881,'TEQUILA OLMECA REPOSADO X 750ML','Destilados importados',NULL,51,1),(3882,'TEQUILA OLMECA REPOSADO X 375ML','Destilados importados',NULL,51,1),(3883,'TEQUILA OLMECA PLATA X 750ML','Destilados importados',NULL,51,1),(3884,'TEQUILA OLMECA PLATA X 375ML','Destilados importados',NULL,51,1),(3885,'TEQUILA OLMECA DARK CHOCOLATE 700 ML','Destilados importados',NULL,51,1),(3886,'TEQUILA 1800 REPOSADO','Destilados importados',NULL,51,1),(3887,'TEQUILA PATRON AÑEJO X 700 ML','Destilados importados',NULL,51,1),(3888,'TEQUILA PATRON X 700 ML','Destilados importados',NULL,51,1),(3889,'TEQUILA ALTOS X 700 ML','Destilados importados',NULL,51,1),(3890,'GINEBRA BOSQUE DE INDIAS','Destilados importados',NULL,51,1),(3891,'GINEBRA LONDON 750','Destilados importados',NULL,51,1),(3892,'GINEBRA GORDON 750','Destilados importados',NULL,51,1),(3893,'GINEBRA STERLING','Destilados importados',NULL,51,1),(3894,'GINEBRA HAWARD','Destilados importados',NULL,51,1),(3895,'BRANDY DOMECO 750','Destilados importados',NULL,51,1),(3896,'BRANDY DOMECO 375','Destilados importados',NULL,51,1),(3897,'BRANDY DOMECO 250','Destilados importados',NULL,51,1),(3898,'BRANDY CINCO ESTRELLAS X375','Destilados importados',NULL,51,1),(3899,'BRANDY CINCO ESTRELA X 700','Destilados importados',NULL,51,1),(3900,'BRANDY GRAJALES 375','Destilados importados',NULL,51,1),(3901,'BRANDY GRAJALES 750','Destilados importados',NULL,51,1),(3902,'BRANDY Gran Brindis 750','Destilados importados',NULL,51,1),(3903,'BRANDY Gran Brindis 375','Destilados importados',NULL,51,1),(3904,'CREMA DE WHISKY BAILEYS X 1000 ML','Licores dulces y vinos',NULL,52,1),(3905,'CREMA DE WHISKY BAILEYS X 750 ML','Licores dulces y vinos',NULL,52,1),(3906,'CREMA DE WHISKY BAILEYS X 375 ML','Licores dulces y vinos',NULL,52,1),(3907,'CREMA DE WHISKY BAILEYS TIRAMISU','Licores dulces y vinos',NULL,52,1),(3908,'CREMA DE WHISKY COPACABANA X 750 ML','Licores dulces y vinos',NULL,52,1),(3909,'CREMA DE WHISKY CASTEL HAUSE X 750 ML','Licores dulces y vinos',NULL,52,1),(3910,'CREMA DE WHISKY BLACK JACK X 750 ML','Licores dulces y vinos',NULL,52,1),(3911,'CREMA DE WHISKY BLACK JACK X 375 ML','Licores dulces y vinos',NULL,52,1),(3912,'CREMA WHISKY CASTLE HOUSE 375','Licores dulces y vinos',NULL,52,1),(3913,'CREMA WHISKY SAVORS 750','Licores dulces y vinos',NULL,52,1),(3914,'CREMA WHISKY SAVORS 375','Licores dulces y vinos',NULL,52,1),(3915,'CREMA DE WHISKY WHISLEYS 700','Licores dulces y vinos',NULL,52,1),(3916,'CREMA COLOMA','Licores dulces y vinos',NULL,52,1),(3917,'CREMA BRYMOR','Licores dulces y vinos',NULL,52,1),(3918,'CREMA EXCELSO','Licores dulces y vinos',NULL,52,1),(3919,'CREMA SURTILEGIO','Licores dulces y vinos',NULL,52,1),(3920,'PIÑA COLADA REAGEE X 750ML','Licores dulces y vinos',NULL,52,1),(3921,'PIÑA COLADA MAVI X 750ML','Licores dulces y vinos',NULL,52,1),(3922,'MANZANILLA PODEROSA X 750 ML','Licores dulces y vinos',NULL,52,1),(3923,'PIÑA COLADA ISLEÑA','Licores dulces y vinos',NULL,52,1),(3924,'PIÑA COLADA TAHITI','Licores dulces y vinos',NULL,52,1),(3925,'SABAJON','Licores dulces y vinos',NULL,52,1),(3926,'SABAJON APOLO','Licores dulces y vinos',NULL,52,1),(3927,'WHISKY JAGERMEISTER X MINI','Licores dulces y vinos',NULL,52,1),(3928,'WHISKY JAGERMEISTER X 375 ML','Licores dulces y vinos',NULL,52,1),(3929,'WHISKY JAGERMEISTER X 700 ML','Licores dulces y vinos',NULL,52,1),(3930,'VINO GRAJALES WALTIER','Licores dulces y vinos',NULL,52,1),(3931,'VINO MOSCATO PASSITO','Licores dulces y vinos',NULL,52,1),(3932,'VINO EMBAJADOR','Licores dulces y vinos',NULL,52,1),(3933,'VINO CASILLERO DEL DIABLO X 750 ML','Licores dulces y vinos',NULL,52,1),(3934,'VINO CASILLERO DEL DIABLO X 375 ML','Licores dulces y vinos',NULL,52,1),(3935,'VINO DUBONET 375','Licores dulces y vinos',NULL,52,1),(3936,'VINO DUBONET 700','Licores dulces y vinos',NULL,52,1),(3937,'VINO MANI SHEWTIZ','Licores dulces y vinos',NULL,52,1),(3938,'VINO SECO FRONTERA X 750 ML','Licores dulces y vinos',NULL,52,1),(3939,'VINO GATO NEGRO X 750ML','Licores dulces y vinos',NULL,52,1),(3940,'VINO GATO NEGRO X 375ML','Licores dulces y vinos',NULL,52,1),(3941,'VINO GRAJALES SEMI SECO X 750 ML','Licores dulces y vinos',NULL,52,1),(3942,'VINO SANGRE DE BOI','Licores dulces y vinos',NULL,52,1),(3943,'VINO LIEBFRAUMILCH','Licores dulces y vinos',NULL,52,1),(3944,'VINO SANZON X 750 ML','Licores dulces y vinos',NULL,52,1),(3945,'VINO CARIÑOSO X 750 ML','Licores dulces y vinos',NULL,52,1),(3946,'VINO MOSCATEL 750 ML','Licores dulces y vinos',NULL,52,1),(3947,'VINO GRAN BRINDIS TINTO X 750 ML','Licores dulces y vinos',NULL,52,1),(3948,'VINO CINZANO 1000','Licores dulces y vinos',NULL,52,1),(3949,'VINO MOSCATEL DE MISA','Licores dulces y vinos',NULL,52,1),(3950,'VINO DULCE AMADOR TINTO X 750ML','Licores dulces y vinos',NULL,52,1),(3951,'VINO CLOSS','Licores dulces y vinos',NULL,52,1),(3952,'VINO LA FERIA','Licores dulces y vinos',NULL,52,1),(3953,'VINO TOCORNAL','Licores dulces y vinos',NULL,52,1),(3954,'VINO PAZZITO','Licores dulces y vinos',NULL,52,1),(3955,'VINO POLERO','Licores dulces y vinos',NULL,52,1),(3956,'VINO TRES MEDALLAS','Licores dulces y vinos',NULL,52,1),(3957,'VINO ROSALEDA','Licores dulces y vinos',NULL,52,1),(3958,'VINO LA MERCED','Licores dulces y vinos',NULL,52,1),(3959,'VINO CHILENO CATA TINTO 1 LITRO','Licores dulces y vinos',NULL,52,1),(3960,'VINO VIÑA MAIPO','Licores dulces y vinos',NULL,52,1),(3961,'VINO VIÑA PIÑA','Licores dulces y vinos',NULL,52,1),(3962,'VINO COVIER 700','Licores dulces y vinos',NULL,52,1),(3963,'VINO TINTO ARIZO CAJAS','Licores dulces y vinos',NULL,52,1),(3964,'CHAMPIN','Licores dulces y vinos',NULL,52,1),(3965,'CHAMPAÑA MAGESTIC X 750 ML','Licores dulces y vinos',NULL,52,1),(3966,'CHAMPAÑA GRAN BRINDIS X 750','Licores dulces y vinos',NULL,52,1),(3967,'CHAMPAÑA GRAN BRINDIS X 2600','Licores dulces y vinos',NULL,52,1),(3968,'CHAMPAÑA PETERLONGO','Licores dulces y vinos',NULL,52,1),(3969,'CHAMPAÑA PETERLONGO 2600','Licores dulces y vinos',NULL,52,1),(3970,'CHAMPAÑA CASANOVA','Licores dulces y vinos',NULL,52,1),(3971,'CHAMPAÑA ALEJANDRIA X 750 ML','Licores dulces y vinos',NULL,52,1),(3972,'CHAMPAÑA MONSERRATE 2600','Licores dulces y vinos',NULL,52,1),(3973,'CAMPAÑA FRIZZANTINO','Licores dulces y vinos',NULL,52,1),(3974,'CHAMPAÑA GRAN CELEBRACIÓN 2600','Licores dulces y vinos',NULL,52,1),(3975,'CHAMPAÑA GRAN CELEBRACIÓN 750','Licores dulces y vinos',NULL,52,1),(3976,'CHAMPAÑA PICCINI','Licores dulces y vinos',NULL,52,1),(3977,'CHAMPAÑA ALTEZA','Licores dulces y vinos',NULL,52,1),(3978,'CHAMPAÑA LAMBRUSCO','Licores dulces y vinos',NULL,52,1),(3979,'JP CHENET X 200','Licores dulces y vinos',NULL,52,1),(3980,'JP CHENET X 750','Licores dulces y vinos',NULL,52,1),(3981,'JP CHENET LATA','Licores dulces y vinos',NULL,52,1),(3982,'Champaña Porttuse','Licores dulces y vinos',NULL,52,1),(3983,'GRAN BRINDIS 2600','Licores dulces y vinos',NULL,52,1),(3984,'PERTER LONGO 2500','Licores dulces y vinos',NULL,52,1),(3985,'NATUMALTA 330*30','Bebidas sin alcohol',NULL,53,1),(3986,'NATUMALTA 200 X 6','Bebidas sin alcohol',NULL,53,1),(3987,'PET 330 X24','Bebidas sin alcohol',NULL,53,1),(3988,'PONY 1.5 LTS X 6','Bebidas sin alcohol',NULL,53,1),(3989,'PONY 2 LTS','Bebidas sin alcohol',NULL,53,1),(3990,'PONY LATA X6','Bebidas sin alcohol',NULL,53,1),(3991,'PONY LITRO X 15','Bebidas sin alcohol',NULL,53,1),(3992,'PONY M-330 X 30','Bebidas sin alcohol',NULL,53,1),(3993,'PONY MINI 200 x30','Bebidas sin alcohol',NULL,53,1),(3994,'PONY MINI SIX GO','Bebidas sin alcohol',NULL,53,1),(3995,'ZALVA X 12','Bebidas sin alcohol',NULL,53,1),(3996,'BIG COLA 1.75','Bebidas sin alcohol',NULL,53,1),(3997,'BIG COLA 400','Bebidas sin alcohol',NULL,53,1),(3998,'BIG COLA 3 LTS','Bebidas sin alcohol',NULL,53,1),(3999,'COCA 237','Bebidas sin alcohol',NULL,53,1),(4000,'COCA ZERO 237','Bebidas sin alcohol',NULL,53,1),(4001,'COCA ZERO 2.5 LT','Bebidas sin alcohol',NULL,53,1),(4002,'COCA 350','Bebidas sin alcohol',NULL,53,1),(4003,'COCA ZERO 1,375 X12','Bebidas sin alcohol',NULL,53,1),(4004,'COCA ZERO 250','Bebidas sin alcohol',NULL,53,1),(4005,'COCA ZERO 350','Bebidas sin alcohol',NULL,53,1),(4006,'COCA COLA 600','Bebidas sin alcohol',NULL,53,1),(4007,'COCA COLA LATA X 12 235','Bebidas sin alcohol',NULL,53,1),(4008,'COCA COLA LATA X 12 330','Bebidas sin alcohol',NULL,53,1),(4009,'COCA ZERO 400','Bebidas sin alcohol',NULL,53,1),(4010,'COCA-COLA PET 250','Bebidas sin alcohol',NULL,53,1),(4011,'COCACOLA 1,5 LTS X 12','Bebidas sin alcohol',NULL,53,1),(4012,'COCACOLA 2 LITRO RET X9','Bebidas sin alcohol',NULL,53,1),(4013,'COCACOLA 2,25 x 8','Bebidas sin alcohol',NULL,53,1),(4014,'COCACOLA 3LTS X 6','Bebidas sin alcohol',NULL,53,1),(4015,'COCACOLA 400','Bebidas sin alcohol',NULL,53,1),(4016,'COCACOLA LITRO PET','Bebidas sin alcohol',NULL,53,1),(4017,'COCACOLA LITRO RET','Bebidas sin alcohol',NULL,53,1),(4018,'KOLA ROMAN 1.5','Bebidas sin alcohol',NULL,53,1),(4019,'KOLA ROMAN 250 PET','Bebidas sin alcohol',NULL,53,1),(4020,'KOLA ROMAN 400','Bebidas sin alcohol',NULL,53,1),(4021,'QUATRO 1,5','Bebidas sin alcohol',NULL,53,1),(4022,'QUATRO 2.5 *8','Bebidas sin alcohol',NULL,53,1),(4023,'QUATRO 237','Bebidas sin alcohol',NULL,53,1),(4024,'QUATRO 250 PET','Bebidas sin alcohol',NULL,53,1),(4025,'QUATRO 3 LtS','Bebidas sin alcohol',NULL,53,1),(4026,'QUATRO 350','Bebidas sin alcohol',NULL,53,1),(4027,'QUATRO 400 PET','Bebidas sin alcohol',NULL,53,1),(4028,'SCHWE PET 400 ml SODA','Bebidas sin alcohol',NULL,53,1),(4029,'SCHWEPPES 1,5 LTS GINGER X 12','Bebidas sin alcohol',NULL,53,1),(4030,'SCHWEPPES 1,5 LTS SODA','Bebidas sin alcohol',NULL,53,1),(4031,'SCHWEPPES AGUA TONICA','Bebidas sin alcohol',NULL,53,1),(4032,'SCHWPET 400 ml GINGER','Bebidas sin alcohol',NULL,53,1),(4033,'SODA 350','Bebidas sin alcohol',NULL,53,1),(4034,'SPRITE 1,5','Bebidas sin alcohol',NULL,53,1),(4035,'SPRITE 237','Bebidas sin alcohol',NULL,53,1),(4036,'SPRITE 3 LT','Bebidas sin alcohol',NULL,53,1),(4037,'SPRITE 350','Bebidas sin alcohol',NULL,53,1),(4038,'SPRITE 400 PET','Bebidas sin alcohol',NULL,53,1),(4039,'BILACK','Bebidas sin alcohol',NULL,53,1),(4040,'BRETAÑA 1.5 LTS x12','Bebidas sin alcohol',NULL,53,1),(4041,'Bretaña 300ml x 24','Bebidas sin alcohol',NULL,53,1),(4042,'BRETAÑA 350','Bebidas sin alcohol',NULL,53,1),(4043,'CANADRY 1,5 X12','Bebidas sin alcohol',NULL,53,1),(4044,'DUOS 3 LTS','Bebidas sin alcohol',NULL,53,1),(4045,'ECONOLITRO x12','Bebidas sin alcohol',NULL,53,1),(4046,'POST 250','Bebidas sin alcohol',NULL,53,1),(4047,'POST 250 PET x 12','Bebidas sin alcohol',NULL,53,1),(4048,'POST 350','Bebidas sin alcohol',NULL,53,1),(4049,'POST 400 PET x15','Bebidas sin alcohol',NULL,53,1),(4050,'POST 500 PET x15','Bebidas sin alcohol',NULL,53,1),(4051,'POSTOBON 1,5','Bebidas sin alcohol',NULL,53,1),(4052,'POSTOBON 1.25 Lts','Bebidas sin alcohol',NULL,53,1),(4053,'Pepsi 2,5 LTS x8','Bebidas sin alcohol',NULL,53,1),(4054,'POSTOBON 2,5 LTS x8','Bebidas sin alcohol',NULL,53,1),(4055,'POSTOBON 250 PET CERO X 12','Bebidas sin alcohol',NULL,53,1),(4056,'POSTOBON 3 LITROS X 6','Bebidas sin alcohol',NULL,53,1),(4057,'SQUASH','Bebidas sin alcohol',NULL,53,1),(4058,'TROPICOLA 400ml x15','Bebidas sin alcohol',NULL,53,1),(4059,'TROPICOLA 1,5 x12','Bebidas sin alcohol',NULL,53,1),(4060,'TUTTI FRTY 400 X 15','Bebidas sin alcohol',NULL,53,1),(4061,'TUTTI FRUTY 250','Bebidas sin alcohol',NULL,53,1),(4062,'TUTTI FRUTY 1.5','Bebidas sin alcohol',NULL,53,1),(4063,'ELECTROLIT','Bebidas sin alcohol',NULL,53,1),(4064,'HIDRALITE','Bebidas sin alcohol',NULL,53,1),(4065,'AGUA PET POOL 300','Bebidas sin alcohol',NULL,53,1),(4066,'AGUA PET POOL 600','Bebidas sin alcohol',NULL,53,1),(4067,'AGUA PET POOL 600 gas','Bebidas sin alcohol',NULL,53,1),(4068,'AGUA VIDA 7','Bebidas sin alcohol',NULL,53,1),(4069,'AGUA VIDA LT','Bebidas sin alcohol',NULL,53,1),(4070,'AGUA ZEND X 6','Bebidas sin alcohol',NULL,53,1),(4071,'AMPER 473 X6','Bebidas sin alcohol',NULL,53,1),(4072,'POOL 250','Bebidas sin alcohol',NULL,53,1),(4073,'CIELO 620','Bebidas sin alcohol',NULL,53,1),(4074,'CIELO 1 LT','Bebidas sin alcohol',NULL,53,1),(4075,'CIFRUT 250','Bebidas sin alcohol',NULL,53,1),(4076,'CIFRUT 400','Bebidas sin alcohol',NULL,53,1),(4077,'PULP 400','Bebidas sin alcohol',NULL,53,1),(4078,'NECTAR 300','Bebidas sin alcohol',NULL,53,1),(4079,'SAVILOE 320X24','Bebidas sin alcohol',NULL,53,1),(4080,'SAVILOE 420 X24','Bebidas sin alcohol',NULL,53,1),(4081,'SPORADE 500','Bebidas sin alcohol',NULL,53,1),(4082,'SPORADE 1.2','Bebidas sin alcohol',NULL,53,1),(4083,'VIVE 100 BT 240X6','Bebidas sin alcohol',NULL,53,1),(4084,'VIVE 100 BT 380X6','Bebidas sin alcohol',NULL,53,1),(4085,'BOTELLON BRISA','Bebidas sin alcohol',NULL,53,1),(4086,'BRISA * 24 600','Bebidas sin alcohol',NULL,53,1),(4087,'BRISA 280','Bebidas sin alcohol',NULL,53,1),(4088,'BRISA AGUA SABORES 280','Bebidas sin alcohol',NULL,53,1),(4089,'BRISA AGUA BIDON 6 Lts X2','Bebidas sin alcohol',NULL,53,1),(4090,'BRISA LITRO X6','Bebidas sin alcohol',NULL,53,1),(4091,'BRISA MANZANA 1.5 X 12','Bebidas sin alcohol',NULL,53,1),(4092,'BRISA SABORES 600 X6','Bebidas sin alcohol',NULL,53,1),(4093,'BRISA x24 600 con gas','Bebidas sin alcohol',NULL,53,1),(4094,'FUZE TEA 400 X6','Bebidas sin alcohol',NULL,53,1),(4095,'MANATIAL GAS x12','Bebidas sin alcohol',NULL,53,1),(4096,'MANATIAL x12','Bebidas sin alcohol',NULL,53,1),(4097,'MANATIAL x12 Vidrio','Bebidas sin alcohol',NULL,53,1),(4098,'MOSTER LATA 473ml X 24','Bebidas sin alcohol',NULL,53,1),(4099,'POWERADE X6 500ML','Bebidas sin alcohol',NULL,53,1),(4100,'SOPORTE BOTELLON','Bebidas sin alcohol',NULL,53,1),(4101,'VALLE 1.5 X 12','Bebidas sin alcohol',NULL,53,1),(4102,'VALLE 250*12','Bebidas sin alcohol',NULL,53,1),(4103,'VALLE FRESH 400 x 12','Bebidas sin alcohol',NULL,53,1),(4104,'VALLE 2.5','Bebidas sin alcohol',NULL,53,1),(4105,'MR TE 1.5','Bebidas sin alcohol',NULL,53,1),(4106,'MR TE 300*12','Bebidas sin alcohol',NULL,53,1),(4107,'ACQUA 400*15','Bebidas sin alcohol',NULL,53,1),(4108,'ACQUA 250*12','Bebidas sin alcohol',NULL,53,1),(4109,'CRISTAL 3.125','Bebidas sin alcohol',NULL,53,1),(4110,'CRISTAL 250 X 12 GAS','Bebidas sin alcohol',NULL,53,1),(4111,'CRISTAL GARRAFA 5 LT','Bebidas sin alcohol',NULL,53,1),(4112,'CRISTAL 300*24','Bebidas sin alcohol',NULL,53,1),(4113,'CRISTAL 6 LTS','Bebidas sin alcohol',NULL,53,1),(4114,'CRISTAL 600 ml x 24','Bebidas sin alcohol',NULL,53,1),(4115,'CRISTAL 600ML CON GAS X 24','Bebidas sin alcohol',NULL,53,1),(4116,'CRISTAL ALOE 330 x12','Bebidas sin alcohol',NULL,53,1),(4117,'CRISTAL BOTELLON','Bebidas sin alcohol',NULL,53,1),(4118,'GATORADE LITE','Bebidas sin alcohol',NULL,53,1),(4119,'CRISTAL LITRO x 12','Bebidas sin alcohol',NULL,53,1),(4120,'GATORADE x12','Bebidas sin alcohol',NULL,53,1),(4121,'H20 1.5','Bebidas sin alcohol',NULL,53,1),(4122,'H2O 250 x12','Bebidas sin alcohol',NULL,53,1),(4123,'HATSU SODA','Bebidas sin alcohol',NULL,53,1),(4124,'HATSU TE 250','Bebidas sin alcohol',NULL,53,1),(4125,'HIT 1 lt pet','Bebidas sin alcohol',NULL,53,1),(4126,'HIT 1,5','Bebidas sin alcohol',NULL,53,1),(4127,'HIT 250','Bebidas sin alcohol',NULL,53,1),(4128,'HIT 300','Bebidas sin alcohol',NULL,53,1),(4129,'HIT 350','Bebidas sin alcohol',NULL,53,1),(4130,'HIT 500','Bebidas sin alcohol',NULL,53,1),(4131,'HIT TBK LT','Bebidas sin alcohol',NULL,53,1),(4132,'HIT TETRA CAJA 200 X 24','Bebidas sin alcohol',NULL,53,1),(4133,'MR TEA 250*30','Bebidas sin alcohol',NULL,53,1),(4134,'MR TEA 500','Bebidas sin alcohol',NULL,53,1),(4135,'RED BULL 250X4','Bebidas sin alcohol',NULL,53,1),(4136,'SPEDD BOTELLA','Bebidas sin alcohol',NULL,53,1),(4137,'SPEDD LATA 310','Bebidas sin alcohol',NULL,53,1),(4138,'SPEED LITRO','Bebidas sin alcohol',NULL,53,1),(4139,'SPEED 400','Bebidas sin alcohol',NULL,53,1),(4140,'VODKA SMIRNOFF ICE LATA 269ML','Destilados importados',NULL,51,1),(4141,'VODKA SMIRNOFF ICE X 275ML','Destilados importados',NULL,51,1),(4142,'LOS CUATES 473','Destilados importados',NULL,51,1),(4143,'LOS CUATES 269','Destilados importados',NULL,51,1),(4144,'COCTEL CALDAS 295','Aguardientes y rones',NULL,50,1),(4145,'GINEBRA GORDON 250 LATA','Destilados importados',NULL,51,1),(4146,'PARIS ICE BLACK','Licores dulces y vinos',NULL,52,1),(4147,'PARIS ICE ROSE','Licores dulces y vinos',NULL,52,1),(4148,'FOUR LOCKO 355','Licores dulces y vinos',NULL,52,1),(4149,'FOUR LOCKO 473','Licores dulces y vinos',NULL,52,1),(4150,'BRETAÑA LATA CON ALCOHOL','Licores dulces y vinos',NULL,52,1);
/*!40000 ALTER TABLE `producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedor`
--

DROP TABLE IF EXISTS `proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedor` (
  `nit_proveedores` varchar(50) NOT NULL,
  `nombre_empresa` varchar(200) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `correo` varchar(254) NOT NULL,
  `tipo_proveedor` varchar(50) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `observacion` longtext,
  `fecha_registro` datetime(6) NOT NULL,
  PRIMARY KEY (`nit_proveedores`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedor`
--

LOCK TABLES `proveedor` WRITE;
/*!40000 ALTER TABLE `proveedor` DISABLE KEYS */;
INSERT INTO `proveedor` VALUES ('101010','coca cola','3256868868','juanaaa@gmail.com','distribuidor','activo',NULL,'2026-09-22 11:43:42.002003'),('10101010010','ginger','3256868868','juanaaa@gmail.com','distribuidor','activo',NULL,'2026-09-14 14:18:03.540905'),('1052382184','va.','3223838570','yuva@gmail.com','distribuidor','activo',NULL,'2026-10-23 13:04:23.858686'),('99999999','OO,.','3223838570','yu@gmail.com','distribuidor','activo',NULL,'2026-10-16 16:39:31.548381'),('99999999999','ooo.','3223838570','yu@gmail.com','distribuidor','activo',NULL,'2026-10-16 16:42:13.609963'),('9999999999998','coca cola','2222222222222','ahhh@gmail.com','distribuidor','activo',NULL,'2026-10-18 22:23:25.577556');
/*!40000 ALTER TABLE `proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `documento` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `correo` varchar(254) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `tipo_identificacion` varchar(20) NOT NULL,
  `rol` varchar(50) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `foto` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_admin` tinyint(1) NOT NULL,
  PRIMARY KEY (`documento`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES ('','2026-10-08 14:22:23.869804','1052382181','Vanessa','Aza','yurivanesaazaaa@gmail.com',NULL,'CC','admin','activo','',1,1),('','2026-10-16 15:12:39.357811','12345678','Admin','CYS','admin@cys.com',NULL,'CC','admin','activo','',1,1),('',NULL,'999999','claude_test_tmp','','999999@cys.com',NULL,'CC','admin','activo','',1,0);
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios_registroactividad`
--

DROP TABLE IF EXISTS `usuarios_registroactividad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_registroactividad` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha_hora` datetime(6) NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `usuario_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `usuarios_registroact_usuario_id_dba1007e_fk_usuarios_` (`usuario_id`),
  CONSTRAINT `usuarios_registroact_usuario_id_dba1007e_fk_usuarios_` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios_registroactividad`
--

LOCK TABLES `usuarios_registroactividad` WRITE;
/*!40000 ALTER TABLE `usuarios_registroactividad` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuarios_registroactividad` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios_usuario`
--

DROP TABLE IF EXISTS `usuarios_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_usuario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
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
  `tipo_id` varchar(5) NOT NULL,
  `identificacion` varchar(20) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `rol` varchar(20) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `reset_token` varchar(64) DEFAULT NULL,
  `reset_token_expira` datetime(6) DEFAULT NULL,
  `foto` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `identificacion` (`identificacion`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios_usuario`
--

LOCK TABLES `usuarios_usuario` WRITE;
/*!40000 ALTER TABLE `usuarios_usuario` DISABLE KEYS */;
INSERT INTO `usuarios_usuario` VALUES (1,'pbkdf2_sha256$1500000$fhCBglaSCpM016EUp1kzb1$aT4xVgQhFpcBQaR3kyR7zjZ+lUV63OF1Ht5g3hvjDvg=','2026-10-28 13:48:12.356184',1,'vanessa','','','yurivanesaaza@gmail.com',1,1,'2026-09-10 12:58:49.754529','CC','1052382184',NULL,'empleado',1,NULL,NULL,''),(2,'pbkdf2_sha256$1500000$mqKserC8lEIvkLUlajVbym$FCpHyyf58NVjbaeTEpoVH7e7KtU1x5BKyjR2zYv9y7U=','2026-10-08 12:05:37.344584',0,'1052382181','Vanessa','Aza','yurivanesaazaaa@gmail.com',0,1,'2026-09-10 13:01:43.534050','CC','1052382181','3223838570','empleado',1,NULL,NULL,''),(16,'pbkdf2_sha256$1200000$pi228eCUEkT2oOmfmbhHm1$/vBQE1N6DJdjKZdBRwDhSoSKGXkT9zFbLPUPIpZl5/s=','2026-10-16 14:18:55.432039',1,'yuri@','','','azavanessa04@gmail.com',1,1,'2026-10-16 13:28:52.385428','CC','46453067',NULL,'empleado',1,NULL,NULL,'');
/*!40000 ALTER TABLE `usuarios_usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios_usuario_groups`
--

DROP TABLE IF EXISTS `usuarios_usuario_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_usuario_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuarios_usuario_groups_usuario_id_group_id_4ed5b09e_uniq` (`usuario_id`,`group_id`),
  KEY `usuarios_usuario_groups_group_id_e77f6dcf_fk_auth_group_id` (`group_id`),
  CONSTRAINT `usuarios_usuario_gro_usuario_id_7a34077f_fk_usuarios_` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios_usuario` (`id`),
  CONSTRAINT `usuarios_usuario_groups_group_id_e77f6dcf_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios_usuario_groups`
--

LOCK TABLES `usuarios_usuario_groups` WRITE;
/*!40000 ALTER TABLE `usuarios_usuario_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuarios_usuario_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios_usuario_user_permissions`
--

DROP TABLE IF EXISTS `usuarios_usuario_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_usuario_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuarios_usuario_user_pe_usuario_id_permission_id_217cadcd_uniq` (`usuario_id`,`permission_id`),
  KEY `usuarios_usuario_use_permission_id_4e5c0f2f_fk_auth_perm` (`permission_id`),
  CONSTRAINT `usuarios_usuario_use_permission_id_4e5c0f2f_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `usuarios_usuario_use_usuario_id_60aeea80_fk_usuarios_` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios_usuario_user_permissions`
--

LOCK TABLES `usuarios_usuario_user_permissions` WRITE;
/*!40000 ALTER TABLE `usuarios_usuario_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuarios_usuario_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `venta`
--

DROP TABLE IF EXISTS `venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `venta` (
  `codigo_venta` int NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `total_venta` decimal(12,2) NOT NULL,
  `metodo_pago` varchar(50) NOT NULL,
  `codigo_caja` int DEFAULT NULL,
  `descuento_porcentaje` decimal(5,2) NOT NULL,
  `pago_daviplata` decimal(12,2) NOT NULL,
  `pago_efectivo` decimal(12,2) NOT NULL,
  `pago_nequi` decimal(12,2) NOT NULL,
  `pago_tarjeta` decimal(12,2) NOT NULL,
  `pago_transferencia` decimal(12,2) NOT NULL,
  `total_con_descuento` decimal(12,2) NOT NULL,
  `vendedor_id` bigint DEFAULT NULL,
  `cliente_email` varchar(150) DEFAULT NULL,
  `cliente_nombre` varchar(150) DEFAULT NULL,
  `observacion` longtext,
  `saldo_pendiente` decimal(12,2) NOT NULL,
  PRIMARY KEY (`codigo_venta`),
  KEY `venta_codigo_caja_5661d7dc_fk_caja_codigo_caja` (`codigo_caja`),
  KEY `venta_vendedor_id_2a24288d_fk_usuarios_usuario_id` (`vendedor_id`),
  CONSTRAINT `venta_codigo_caja_5661d7dc_fk_caja_codigo_caja` FOREIGN KEY (`codigo_caja`) REFERENCES `caja` (`codigo_caja`),
  CONSTRAINT `venta_vendedor_id_2a24288d_fk_usuarios_usuario_id` FOREIGN KEY (`vendedor_id`) REFERENCES `usuarios_usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `venta`
--

LOCK TABLES `venta` WRITE;
/*!40000 ALTER TABLE `venta` DISABLE KEYS */;
INSERT INTO `venta` VALUES (1,'2026-10-16 15:05:08.442463',50000.00,'efectivo',1,0.00,0.00,500000.00,0.00,0.00,0.00,50000.00,16,NULL,'Consumidor final',NULL,0.00),(2,'2026-10-18 22:27:21.934435',50000.00,'efectivo',2,0.00,0.00,500000.00,0.00,0.00,0.00,50000.00,16,NULL,'Consumidor final',NULL,0.00),(3,'2026-10-19 11:37:24.214952',500000.00,'efectivo',2,0.00,0.00,500000.00,0.00,0.00,0.00,500000.00,16,NULL,'Consumidor final','',0.00);
/*!40000 ALTER TABLE `venta` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-28  8:48:13
