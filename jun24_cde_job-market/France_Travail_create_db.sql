-- MySQL Script generated by MySQL Workbench
-- Sat Jan 11 17:52:50 2025
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`requirements`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`requirements` ;

CREATE TABLE IF NOT EXISTS `mydb`.`requirements` (
  `requirements` CHAR NOT NULL,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`requirements`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`naf`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`naf` ;

CREATE TABLE IF NOT EXISTS `mydb`.`naf` (
  `naf_code` VARCHAR(10) NOT NULL,
  `label` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`naf_code`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`rome`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`rome` ;

CREATE TABLE IF NOT EXISTS `mydb`.`rome` (
  `rome_code` VARCHAR(5) NOT NULL,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`rome_code`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`activity_sector`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`activity_sector` ;

CREATE TABLE IF NOT EXISTS `mydb`.`activity_sector` (
  `activity_sector_code` INT NOT NULL,
  `label` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`activity_sector_code`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`qualification`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`qualification` ;

CREATE TABLE IF NOT EXISTS `mydb`.`qualification` (
  `qualification_code` INT NOT NULL,
  `label` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`qualification_code`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`companies`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`companies` ;

CREATE TABLE IF NOT EXISTS `mydb`.`companies` (
  `company_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `is_adapted` TINYINT NULL DEFAULT NULL,
  PRIMARY KEY (`company_id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`contact`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`contact` ;

CREATE TABLE IF NOT EXISTS `mydb`.`contact` (
  `contact_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(200) NULL DEFAULT NULL,
  `email` TEXT NULL DEFAULT NULL,
  `address` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`contact_id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`moving`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`moving` ;

CREATE TABLE IF NOT EXISTS `mydb`.`moving` (
  `moving_code` TINYINT NOT NULL,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`moving_code`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`cities`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`cities` ;

CREATE TABLE IF NOT EXISTS `mydb`.`cities` (
  `insee_code` INT NOT NULL,
  `name` VARCHAR(45) NOT NULL,
  `arr` VARCHAR(45) NULL DEFAULT NULL,
  `latitude` VARCHAR(45) NULL DEFAULT NULL,
  `longitude` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`insee_code`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job` (
  `job_id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  `creation_date` TIMESTAMP NOT NULL,
  `update_date` TIMESTAMP NOT NULL,
  `rome_code` VARCHAR(5) NOT NULL,
  `experience_required` CHAR NOT NULL,
  `experience_length_months` INT NULL DEFAULT NULL,
  `experience_detail` VARCHAR(45) NULL DEFAULT NULL,
  `is_alternance` TINYINT NULL DEFAULT NULL,
  `is_disabled_friendly` TINYINT NULL DEFAULT NULL,
  `naf_code` VARCHAR(10) NULL DEFAULT NULL,
  `qualification_code` INT NULL DEFAULT NULL,
  `candidates_missing` TINYINT NULL DEFAULT NULL,
  `activity_sector_code` INT NULL DEFAULT NULL,
  `moving_code` TINYINT NULL DEFAULT NULL,
  `company_id` INT NULL DEFAULT NULL,
  `contact_id` INT NULL DEFAULT NULL,
  `insee_code` INT NULL DEFAULT NULL,
  `internal_id` VARCHAR(12) NULL DEFAULT NULL,
  PRIMARY KEY (`job_id`),
  INDEX `naf_job_idx` (`naf_code` ASC) VISIBLE,
  INDEX `rome_job_fk_idx` (`rome_code` ASC) VISIBLE,
  INDEX `sector_activity_job_fk_idx` (`activity_sector_code` ASC) VISIBLE,
  INDEX `qualification_job_idx` (`qualification_code` ASC) VISIBLE,
  INDEX `job_company_fk_idx` (`company_id` ASC) VISIBLE,
  INDEX `job_contact_fk_idx` (`contact_id` ASC) VISIBLE,
  INDEX `job_moving_fk_idx` (`moving_code` ASC) VISIBLE,
  INDEX `insee_code_fk_idx` (`insee_code` ASC) VISIBLE,
  UNIQUE INDEX `internal_id_UNIQUE` (`internal_id` ASC) VISIBLE,
  INDEX `job_requirement_fk` (`experience_required` ASC) VISIBLE,
  CONSTRAINT `job_requirement_fk`
    FOREIGN KEY (`experience_required`)
    REFERENCES `mydb`.`requirements` (`requirements`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `naf_job_fk`
    FOREIGN KEY (`naf_code`)
    REFERENCES `mydb`.`naf` (`naf_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `rome_job_fk`
    FOREIGN KEY (`rome_code`)
    REFERENCES `mydb`.`rome` (`rome_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `sector_activity_job_fk`
    FOREIGN KEY (`activity_sector_code`)
    REFERENCES `mydb`.`activity_sector` (`activity_sector_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `qualification_job`
    FOREIGN KEY (`qualification_code`)
    REFERENCES `mydb`.`qualification` (`qualification_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_company_fk`
    FOREIGN KEY (`company_id`)
    REFERENCES `mydb`.`companies` (`company_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_contact_fk`
    FOREIGN KEY (`contact_id`)
    REFERENCES `mydb`.`contact` (`contact_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_moving_fk`
    FOREIGN KEY (`moving_code`)
    REFERENCES `mydb`.`moving` (`moving_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `insee_code_fk`
    FOREIGN KEY (`insee_code`)
    REFERENCES `mydb`.`cities` (`insee_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`salary`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`salary` ;

CREATE TABLE IF NOT EXISTS `mydb`.`salary` (
  `salary_id` INT NOT NULL AUTO_INCREMENT,
  `job_id` INT NOT NULL,
  `min_monthly_salary` FLOAT NULL DEFAULT NULL,
  `max_monthly_salary` FLOAT NULL DEFAULT NULL,
  `salary_description` VARCHAR(100) NULL DEFAULT NULL,
  `max_monthly_predicted` FLOAT NULL,
  PRIMARY KEY (`salary_id`),
  INDEX `job_id_idx` (`job_id` ASC) VISIBLE,
  UNIQUE INDEX `job_id_UNIQUE` (`job_id` ASC) VISIBLE,
  CONSTRAINT `salary_job_id_fk`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '	';


-- -----------------------------------------------------
-- Table `mydb`.`benefits`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`benefits` ;

CREATE TABLE IF NOT EXISTS `mydb`.`benefits` (
  `benefits_id` INT NOT NULL AUTO_INCREMENT,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`benefits_id`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`salary_benefits`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`salary_benefits` ;

CREATE TABLE IF NOT EXISTS `mydb`.`salary_benefits` (
  `benefits_id` INT NOT NULL,
  `salary_id` INT NOT NULL,
  PRIMARY KEY (`benefits_id`, `salary_id`),
  INDEX `salary_id_idx` (`salary_id` ASC) VISIBLE,
  CONSTRAINT `salary_benefits_benefits_id_fk`
    FOREIGN KEY (`benefits_id`)
    REFERENCES `mydb`.`benefits` (`benefits_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `salary_benefits_salary_id_fk`
    FOREIGN KEY (`salary_id`)
    REFERENCES `mydb`.`salary` (`salary_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_competency`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_competency` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_competency` (
  `competency_code` INT NOT NULL,
  `job_id` INT NOT NULL,
  `required` CHAR NULL DEFAULT NULL,
  PRIMARY KEY (`competency_code`, `job_id`),
  INDEX `job_comp_req_fk_idx` (`required` ASC) VISIBLE,
  INDEX `job_competency_job_id_fk` (`job_id` ASC) VISIBLE,
  CONSTRAINT `job_competency_job_id_fk`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_comp_req_fk`
    FOREIGN KEY (`required`)
    REFERENCES `mydb`.`requirements` (`requirements`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`competencies`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`competencies` ;

CREATE TABLE IF NOT EXISTS `mydb`.`competencies` (
  `competency_code` INT NOT NULL,
  `label` VARCHAR(300) NULL DEFAULT NULL,
  PRIMARY KEY (`competency_code`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE,
  CONSTRAINT `competency_job_fk`
    FOREIGN KEY (`competency_code`)
    REFERENCES `mydb`.`job_competency` (`competency_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`professional_qualities`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`professional_qualities` ;

CREATE TABLE IF NOT EXISTS `mydb`.`professional_qualities` (
  `professional_quality_id` INT NOT NULL AUTO_INCREMENT,
  `label` TEXT NULL DEFAULT NULL,
  `description` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`professional_quality_id`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_professional_qualities`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_professional_qualities` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_professional_qualities` (
  `professional_quality_id` INT NOT NULL,
  `job_id` INT NOT NULL,
  PRIMARY KEY (`professional_quality_id`, `job_id`),
  INDEX `job_profesionnal_job_id_fk_idx` (`job_id` ASC) VISIBLE,
  CONSTRAINT `job_profesionnal_job_id_fk2`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `pro_job_fk`
    FOREIGN KEY (`professional_quality_id`)
    REFERENCES `mydb`.`professional_qualities` (`professional_quality_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`driver_license`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`driver_license` ;

CREATE TABLE IF NOT EXISTS `mydb`.`driver_license` (
  `driver_license_id` INT NOT NULL AUTO_INCREMENT,
  `label` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`driver_license_id`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_driver_license`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_driver_license` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_driver_license` (
  `job_id` INT NOT NULL,
  `driver_license_id` INT NOT NULL,
  `requirement` CHAR NULL DEFAULT NULL,
  PRIMARY KEY (`driver_license_id`, `job_id`),
  INDEX `driver_license_id_idx` (`driver_license_id` ASC) VISIBLE,
  INDEX `job_driver_license_job_id` (`job_id` ASC) VISIBLE,
  INDEX `job_driver_req` (`requirement` ASC) VISIBLE,
  CONSTRAINT `job_driver_license_job_id`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_driver_license_driver_license_id`
    FOREIGN KEY (`driver_license_id`)
    REFERENCES `mydb`.`driver_license` (`driver_license_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_driver_req`
    FOREIGN KEY (`requirement`)
    REFERENCES `mydb`.`requirements` (`requirements`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`formation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`formation` ;

CREATE TABLE IF NOT EXISTS `mydb`.`formation` (
  `formation_id` INT NOT NULL AUTO_INCREMENT,
  `label` VARCHAR(100) NULL DEFAULT NULL,
  `level` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`formation_id`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_formation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_formation` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_formation` (
  `job_id` INT NOT NULL,
  `formation_id` INT NOT NULL,
  `requirement` CHAR NULL DEFAULT NULL,
  PRIMARY KEY (`job_id`, `formation_id`),
  INDEX `formation_id_idx` (`formation_id` ASC) VISIBLE,
  INDEX `job_formation_requirement` (`requirement` ASC) VISIBLE,
  CONSTRAINT `job_formation_job_id`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_formation_formation_id`
    FOREIGN KEY (`formation_id`)
    REFERENCES `mydb`.`formation` (`formation_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_formation_requirement`
    FOREIGN KEY (`requirement`)
    REFERENCES `mydb`.`requirements` (`requirements`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`language`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`language` ;

CREATE TABLE IF NOT EXISTS `mydb`.`language` (
  `language_id` INT NOT NULL AUTO_INCREMENT,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`language_id`),
  UNIQUE INDEX `label_UNIQUE` (`label` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_language`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_language` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_language` (
  `language_id` INT NOT NULL,
  `job_id` INT NOT NULL,
  `requirement` CHAR NULL DEFAULT NULL,
  PRIMARY KEY (`language_id`, `job_id`),
  INDEX `job_language_fk_idx` (`job_id` ASC) VISIBLE,
  INDEX `language_req_idx` (`requirement` ASC) VISIBLE,
  CONSTRAINT `job_language_fk`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `language_fk`
    FOREIGN KEY (`language_id`)
    REFERENCES `mydb`.`language` (`language_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `language_req`
    FOREIGN KEY (`requirement`)
    REFERENCES `mydb`.`requirements` (`requirements`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`contract_type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`contract_type` ;

CREATE TABLE IF NOT EXISTS `mydb`.`contract_type` (
  `contract_type_id` INT NOT NULL AUTO_INCREMENT,
  `contract_type` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`contract_type_id`),
  UNIQUE INDEX `contract_type_UNIQUE` (`contract_type` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`contract_nature`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`contract_nature` ;

CREATE TABLE IF NOT EXISTS `mydb`.`contract_nature` (
  `contract_nature_id` INT NOT NULL AUTO_INCREMENT,
  `contract_nature` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`contract_nature_id`),
  UNIQUE INDEX `contract_nature_UNIQUE` (`contract_nature` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`job_contract`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`job_contract` ;

CREATE TABLE IF NOT EXISTS `mydb`.`job_contract` (
  `job_id` INT NOT NULL,
  `contract_type_id` INT NOT NULL,
  `contract_nature_id` INT NOT NULL,
  `label` VARCHAR(45) NULL DEFAULT NULL,
  `work_duration` INT NULL DEFAULT NULL,
  `hours_per_week` FLOAT NULL DEFAULT NULL,
  `work_condition` VARCHAR(45) NULL DEFAULT NULL,
  `additional_condition` VARCHAR(45) NULL DEFAULT NULL,
  `partial` TINYINT NULL DEFAULT NULL,
  INDEX `job_contract_fk_idx` (`job_id` ASC) VISIBLE,
  INDEX `job_contract_nature_idx` (`contract_nature_id` ASC) VISIBLE,
  INDEX `job_contract_type_idx` (`contract_type_id` ASC) VISIBLE,
  PRIMARY KEY (`contract_type_id`, `contract_nature_id`, `job_id`),
  CONSTRAINT `job_contract_fk`
    FOREIGN KEY (`job_id`)
    REFERENCES `mydb`.`job` (`job_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_contract_nature_fk`
    FOREIGN KEY (`contract_nature_id`)
    REFERENCES `mydb`.`contract_nature` (`contract_nature_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `job_contract_type_fk`
    FOREIGN KEY (`contract_type_id`)
    REFERENCES `mydb`.`contract_type` (`contract_type_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
