from config.config import logger
from opendemic.database import RDBManager
from helpers.formatting import mysql_db_format_value, quote_wrap
import uuid


def subscribe_to_newsletter(phone: str = None, email: str = None) -> (bool, str):
	if phone is not None or email is not None:
		rdb = RDBManager()
		try:
			existing_contact, err = rdb.execute(
				sql_query="""
					SELECT `id`
					FROM `contact`
					WHERE
						`phone_number` = {}
						OR
						`email` = {}
					LIMIT 1
				""".format(
					mysql_db_format_value(value=phone),
					mysql_db_format_value(value=email)
				)
			)
		except Exception as e:
			logger.error(e)
			return False, "An error occurred while processing your registration. Please try again."
		else:
			err = None

			if len(existing_contact) == 1 and 'id' in existing_contact[0]:
				contact_id = existing_contact[0]['id']
				try:
					_, err = rdb.execute(
						sql_query="""
							UPDATE `contact`
							SET
								`phone_number` = IF({} is not null, {}, `phone_number`),
								`email` = IF({} is not null, {}, `email`)
							WHERE
								`id` = {}
								""".format(
							mysql_db_format_value(value=phone),
							quote_wrap(phone),
							mysql_db_format_value(value=email),
							mysql_db_format_value(value=email),
							mysql_db_format_value(value=contact_id)
						)
					)
				except Exception as e:
					logger.error(e)
			else:
				new_contact_id = str(uuid.uuid4())
				try:
					_, err = rdb.execute(
						sql_query="""
							INSERT IGNORE INTO `contact` (`id`, `phone_number`, `email`)
							VALUES
								({}, {}, {})
								""".format(
							mysql_db_format_value(value=new_contact_id),
							quote_wrap(phone),
							mysql_db_format_value(value=email)
						)
					)
				except Exception as e:
					logger.error(e)

			return err is None, "Subscribed!"
	else:
		return False, "Seems like you didn't provide any contact information. Please try again."
