-- 1.0
CREATE TABLE IF NOT EXISTS `geolocations` (
  `human_id` char(36) NOT NULL,
  `created` timestamp NOT NULL,
  `modified` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `fever` tinyint(1) DEFAULT NULL,
  `shortness_of_breath` tinyint(1) DEFAULT NULL,
  `cough` tinyint(1) DEFAULT NULL,
  `latitude` decimal(14,10) DEFAULT NULL,
  `longitude` decimal(14,10) DEFAULT NULL,
  PRIMARY KEY (`human_id`,`created`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `humans` (
  `id` char(36) NOT NULL,
  `telegram_human_id` int(20) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL,
  `modified` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `email` varchar(254) DEFAULT NULL,
  `biological_sex` char(1) DEFAULT NULL,
  `birth_year` int(10) DEFAULT NULL,
  `is_admin` tinyint(1) NOT NULL DEFAULT '0',
  `tag` varchar(254) DEFAULT NULL,
  `utm_source` varchar(254) DEFAULT NULL,
  `utm_medium` varchar(254) DEFAULT NULL,
  `utm_campaign` varchar(254) DEFAULT NULL,
  `utm_term` varchar(254) DEFAULT NULL,
  `utm_content` varchar(254) DEFAULT NULL,
  `current_tz` varchar(254) NOT NULL DEFAULT 'America/New_York',
  `fingerprint` char(64) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `log` (
  `id` int(20) unsigned NOT NULL AUTO_INCREMENT,
  `human_id` char(36) DEFAULT '',
  `telegram_human_id` int(20) DEFAULT NULL,
  `from` varchar(254) NOT NULL DEFAULT '',
  `to` varchar(254) NOT NULL DEFAULT '',
  `action_type` varchar(254) NOT NULL DEFAULT '',
  `action_value` text,
  `created` timestamp NOT NULL,
  `created_local` datetime DEFAULT NULL,
  `message_id` int(20) DEFAULT NULL,
  `elapsed_seconds` int(10) DEFAULT NULL,
  `tag` varchar(254) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31651 DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `symptoms` (
  `human_id` char(36) NOT NULL,
  `created` timestamp NOT NULL,
  `modified` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `symptom` varchar(254) DEFAULT NULL,
  `value` decimal(14,4) DEFAULT NULL,
  PRIMARY KEY (`human_id`,`created`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `timezones` (
  `timezone_name` varchar(32) NOT NULL,
  `area` multipolygon NOT NULL,
  `offset` char(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


-- 1.1
ALTER TABLE `humans` ADD COLUMN `fingerprint` CHAR(64) DEFAULT NULL;