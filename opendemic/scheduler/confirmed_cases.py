from config.config import CONFIG, logger
import os
import pandas as pd
import uuid
import numpy as np
import tarfile
from tarfile import TarFile, ExFileObject
import requests
from opendemic.database import generate_db_uri
import sqlalchemy
from sqlalchemy.engine.base import Engine
from io import BytesIO
from typing import List

_CONFIRMED_CASE_DATA_URL: str = "https://github.com/beoutbreakprepared/nCoV2019/blob/master/latest_data/latestdata.tar.gz?raw=true"


def get_existing_source_ids() -> List[str]:
	logger.debug("Getting existing source ids")
	database_connection: Engine = sqlalchemy.create_engine(generate_db_uri())
	with database_connection.begin() as cnx:
		sql_query = sqlalchemy.text("""
			SELECT `source_id`
			FROM `humans`
			WHERE `source` = 'beoutbreakprepared'
		""")
		result = cnx.execute(sql_query)
		result_as_list: list = result.fetchall()
		source_ids_to_remove: str = [item[0] for item in result_as_list]
	return source_ids_to_remove


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
	logger.debug("Cleaning dataset...")
	data: pd.DataFrame = data[~pd.isna(data['ID'])]
	data: pd.DataFrame = data[~pd.isna(data['date_confirmation'])]
	data['date_confirmation'] = pd.to_datetime(data['date_confirmation'].apply(lambda x: x[:10]))
	data['created'] = data['date_confirmation']
	data['modified'] = data['date_confirmation']
	data['latitude'] = pd.to_numeric(data['latitude'])
	data['longitude'] = pd.to_numeric(data['longitude'])
	data['biological_sex'] = data['sex'].apply(lambda x: 'F' if x == 'female' else ('M' if x == 'male' else np.nan))
	data['symptom'] = 'verified_covid19'
	data['source'] = 'beoutbreakprepared'
	data['source_id'] = data['ID']
	data['id'] = data['source_id'].apply(lambda x : str(uuid.uuid4()))
	data['human_id'] = data['id']
	try:
		source_ids_to_remove = get_existing_source_ids()
	except Exception as e:
		logger.error(e)
	else:
		data: pd.DataFrame = data[~data['source_id'].isin(source_ids_to_remove)]
	return data


def get_confirmed_case_data() -> pd.DataFrame:
	logger.debug('Getting confirmed cases from {}'.format(_CONFIRMED_CASE_DATA_URL))
	data_dir: str = 'data'
	target_compressed_file: str = os.path.join(data_dir, 'latest_data.tar.gz')
	if not os.path.exists(data_dir):
		os.makedirs(data_dir)
	response: requests.models.Response = requests.get(_CONFIRMED_CASE_DATA_URL, stream=True)
	if response.status_code == 200:
		with open(target_compressed_file, 'wb') as f:
			f.write(response.raw.read())
	tf: TarFile = tarfile.open(target_compressed_file)
	csv_path: str = tf.getnames()[0]
	file: ExFileObject = tf.extractfile(member=csv_path)
	data: pd.DataFrame = pd.read_csv(BytesIO(file.read()), header=0, sep=",", encoding='utf8')
	if os.path.exists(target_compressed_file):
		os.remove(target_compressed_file)
		os.removedirs(data_dir)
	return clean_data(data=data)


def update_confirmed_cases():
	data: pd.DataFrame = get_confirmed_case_data()
	database_connection: Engine = sqlalchemy.create_engine(generate_db_uri())

	new_data_to_humans: pd.DataFrame = data[['id', 'created', 'modified', 'biological_sex', 'source', 'source_id']]
	new_data_to_humans_tbl_name: str = 'new_data_to_humans_tmp'
	new_data_to_symptoms: pd.DataFrame = data[['human_id', 'created', 'modified', 'symptom']]
	new_data_to_symptoms['value'] = 1.0
	new_data_to_symptoms_tbl_name: str = 'new_data_to_symptoms_tmp'
	new_data_to_geolocations = data[['human_id', 'created', 'modified', 'latitude', 'longitude']]
	new_data_to_geolocations_tbl_name = 'new_data_to_geolocations_tmp'

	for data_to_insert in [
		(new_data_to_humans, new_data_to_humans_tbl_name, "humans"),
		(new_data_to_symptoms, new_data_to_symptoms_tbl_name, "symptoms"),
		(new_data_to_geolocations, new_data_to_geolocations_tbl_name, "geolocations")
	]:
		data_to_insert[0].to_sql(name=data_to_insert[1], con=database_connection, if_exists='replace', index=False)
		with database_connection.begin() as cnx:
			insert_sql: str = """
				INSERT IGNORE INTO {}({})
				SELECT {} FROM {}
			""".format(
				data_to_insert[2],
				', '.join(list(data_to_insert[0].columns)),
				', '.join(list(data_to_insert[0].columns)),
				data_to_insert[1]
			)
			cnx.execute(insert_sql)
			delete_tmp_table_sql: str = "DROP TABLE IF EXISTS {}".format(data_to_insert[1])
			cnx.execute(delete_tmp_table_sql)

