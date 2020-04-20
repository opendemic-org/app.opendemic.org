import pymysql
import pymysql.cursors
import prometheus_client
from time import time
from config.config import CONFIG, logger

QUERY_DURATION = prometheus_client.Histogram('query_ms', 'Query execution time', ['app_name', 'query'])


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
			logger.error(e)

	def pre_execute(self, sql_query: str) -> Exception:
		err = None
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(sql_query)
				self.connection.commit()
		except BaseException as e:
			logger.error(e)
			err = e
		return err

	def execute(self, sql_query: str) -> (list, Exception):
		err = None
		result = []
		starting_time = time()
		try:
			with self.connection.cursor() as cursor:
				cursor.execute(sql_query)
				result = cursor.fetchall()
				QUERY_DURATION.labels('opendemic', sql_query).observe(round(time() - starting_time, 2))
				self.connection.commit()
		except BaseException as e:
			logger.error(e)
			err = e
		return result, err
