CREATE TABLE `humans` (
  `id` char(36) NOT NULL,
  `telegram_human_id` int(20) unsigned DEFAULT NULL,
  `created` timestamp NOT NULL,
  `modified` timestamp NOT NULL ON UPDATE CURRENT_TIMESTAMP,
  `email` varchar(254) DEFAULT NULL,
  `is_admin` tinyint(1) NOT NULL DEFAULT '0',
  `birth_year` int(10) DEFAULT NULL,
  `tag` varchar(254) DEFAULT NULL,
  `utm_source` varchar(254) DEFAULT NULL,
  `utm_medium` varchar(254) DEFAULT NULL,
  `utm_campaign` varchar(254) DEFAULT NULL,
  `utm_term` varchar(254) DEFAULT NULL,
  `utm_content` varchar(254) DEFAULT NULL,
  PRIMARY KEY (`telegram_human_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `measurements` (
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