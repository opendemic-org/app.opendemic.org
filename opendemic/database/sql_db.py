import pymysql
import pymysql.cursors
from config.config import CONFIG


class RDBManager(object):
	def __init__(self):
		self.connection = pymysql.connect(
			host=CONFIG.get('rds-aurora-mysql-opendemic-host'),
			port=CONFIG.getint('rds-aurora-mysql-opendemic-port'),
			user=CONFIG.get('rds-aurora-mysql-opendemic-username'),
			password=CONFIG.get('rds-aurora-mysql-opendemic-password'),
			db=CONFIG.get('rds-aurora-mysql-opendemic-database'),
			charset='utf8mb4',
			cursorclass=pymysql.cursors.DictCursor
		)

	def __del__(self):
		try:
			self.connection.close()
		except AttributeError as e:
			print(e)

	def pre_execute(self, sql_query: str):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(sql_query)
				row_count = cursor.rowcount

				# Commit
				self.connection.commit()

				# Return result
				return row_count

		except BaseException as e:
			print(e)

	def execute(self, sql_query: str):
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(sql_query)
				row_count = cursor.rowcount
				result = cursor.fetchall()

				# Commit
				self.connection.commit()

				# Return result
				return result, row_count

		except BaseException as e:
			print(e)