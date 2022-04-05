/*
 Navicat Premium Data Transfer

 Source Server         : con1
 Source Server Type    : MySQL
 Source Server Version : 80028
 Source Host           : localhost:3306
 Source Schema         : ibapi

 Target Server Type    : MySQL
 Target Server Version : 80028
 File Encoding         : 65001

 Date: 05/04/2022 03:12:56
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for accountsummary
-- ----------------------------
DROP TABLE IF EXISTS `accountsummary`;
CREATE TABLE `accountsummary`  (
  `Account` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `TimeStamp` bigint NOT NULL,
  `NetLiquidation` double(50, 6) NULL DEFAULT NULL,
  `TotalCashValue` double(50, 6) NULL DEFAULT NULL,
  `AvailableFunds` double(50, 6) NULL DEFAULT NULL,
  `GrossPositionValue` double(50, 6) NULL DEFAULT NULL,
  PRIMARY KEY (`Account`, `TimeStamp`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for fivesecondbar
-- ----------------------------
DROP TABLE IF EXISTS `fivesecondbar`;
CREATE TABLE `fivesecondbar`  (
  `Contract` varchar(50) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `DateTime` bigint NOT NULL,
  `Open` double(50, 6) NOT NULL,
  `High` double(50, 6) NOT NULL,
  `Low` double(50, 6) NOT NULL,
  `Close` double(50, 6) NOT NULL,
  `Volume` bigint NULL DEFAULT NULL,
  `Average` double(50, 6) NULL DEFAULT NULL,
  `Count` bigint NULL DEFAULT NULL,
  PRIMARY KEY (`Contract`, `DateTime`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for orderstatus
-- ----------------------------
DROP TABLE IF EXISTS `orderstatus`;
CREATE TABLE `orderstatus`  (
  `OrderID` bigint NOT NULL COMMENT 'The unique ID of an order',
  `Contract` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'The code of contract, for example, EUR',
  `Action` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '\'buy\' or \'sell\' ',
  `Status` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'Status of the order',
  `AmountFilled` double(50, 4) NOT NULL COMMENT 'The amount which has been filled',
  `Remaining` double(50, 4) NOT NULL COMMENT 'The amount remainning',
  `AvgFillPrice` double(50, 6) NOT NULL COMMENT 'The average price of filled amount',
  `ClientID` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `LastUpdTime` datetime NULL DEFAULT NULL COMMENT 'The last time this record is updated',
  PRIMARY KEY (`OrderID`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for position
-- ----------------------------
DROP TABLE IF EXISTS `position`;
CREATE TABLE `position`  (
  `Account` varchar(100) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL COMMENT 'The account number',
  `Timestamp` bigint NOT NULL,
  `Contract` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'The unique code of underlying asset',
  `Position` double(100, 4) NULL DEFAULT NULL COMMENT 'The position amount of this contract',
  `AvgCost` double(30, 6) NULL DEFAULT NULL COMMENT 'The average price of current position',
  PRIMARY KEY (`Account`, `Timestamp`, `Contract`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
