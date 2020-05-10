from config.config import CONFIG, logger
from opendemic.database import generate_db_uri, RDBManager
from urllib.request import urlopen
import json
import sqlalchemy
import pandas as pd
from pandas.core.frame import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp
from scipy.ndimage import gaussian_filter1d
import scipy.stats as sps
import numpy as np
from numpy import ndarray
from datetime import date
from typing import Tuple, List
_NYC_FIPS = 'NYC_FIPS'
_NYC_COUNTIES_FIPS_TO_NAME = {
	'36061': 'New York',
	'36047': 'Kings',
	'36081': 'Queens',
	'36005': 'Bronx',
	'36085': 'Richmond'
}
_GAMMA: float = 1 / 7
_RT_MAX: int = 12
_RT_RANGE: ndarray = np.linspace(0, _RT_MAX, _RT_MAX * 100 + 1)


class TimeSeriesDimensionError(Exception):
	pass


def high_density_interval(pmf: ndarray, p: float = 0.9) -> Tuple[float, float]:
	_pmf: ndarray = np.squeeze(pmf)
	if _pmf.ndim != 1:
		raise ValueError('Credible region can be computed only for 1d probability mass vectors.')
	cumsum: ndarray = np.cumsum(_pmf)
	total_p: ndarray = cumsum - cumsum[:, None]
	lows, highs = (total_p > p).nonzero()
	best: int = (highs - lows).argmin()
	_low: float = _RT_RANGE[lows[best]]
	_high: float = _RT_RANGE[highs[best]]
	return _low, _high


def get_posteriors(ts: ndarray, sigma: float = 0.25) -> Tuple[ndarray, float]:
	"""
	Get the posterior probability for each time step and the log-likelihood of
	the representation.

	Args:
		ts : ndarray
			One dimensional array representation of the time series of the
			number of new cases in each time point.
		sigma : float
			Scale parameter of the gaussian update of the prior distribution.
	Returns:
		tuple of length 2 with:
			* 2d numpy array with one row per time point and one column per
				tested Rt. Each row of the matrix encodes the posterior
				probability distribution at a specific timepoint. The array of
				the tested Rt-s is defined as
				`opendemic.modelling.systrom.RT_RANGE`.
			* float with the log-likelihood of the model.
	Raises:
		ValueError : if the passed time series is not one-dimensional.
	"""
	_ts: ndarray = np.squeeze(ts)
	if _ts.ndim != 1:
		raise TimeSeriesDimensionError('The time series must be a 1d array.')
	sigma: float = float(sigma)
	lam: ndarray = _ts[:-1] * np.exp(_GAMMA * (_RT_RANGE[:, None] - 1))
	likelihood: ndarray = sps.poisson.pmf(_ts[1:], lam)
	likelihood /= np.sum(likelihood, axis=0)
	transition: ndarray = sps.norm(loc=_RT_RANGE, scale=sigma).pdf(_RT_RANGE[:, None])
	transition /= transition.sum(axis=0)
	prior0: ndarray = np.ones_like(_RT_RANGE)
	prior0 /= len(prior0)
	prior0 /= prior0.sum()
	posteriors: ndarray = np.zeros((_ts.size, prior0.size))
	posteriors[0] = prior0
	llhood: float = 0.0
	for i in range(1, _ts.size):
		prior: ndarray = transition @ posteriors[i - 1]
		posterior_num: ndarray = likelihood[:, i - 1] * prior
		posterior_den: float = posterior_num.sum()
		posteriors[i] = posterior_num / posterior_den
		llhood += np.log(posterior_den)

	return posteriors, llhood


def prepare_cases(cases: DataFrame) -> Tuple[List[float], List[float], List[Timestamp]]:
	_cases: ndarray = np.asarray(cases, dtype=np.float32)
	diff_cases: ndarray = np.diff(_cases)
	idx_start: int = 0
	for i, v in enumerate(diff_cases):
		if v < 15:
			idx_start: int = i + 1
		else:
			break
	portion: float = 0.2
	tolerable_crop: float = np.ceil(portion * _cases.size)
	if idx_start > tolerable_crop:
		idx_start: int = int(np.ceil(tolerable_crop))
	_cases: ndarray = _cases[idx_start:]
	new_cases: ndarray = np.ceil(gaussian_filter1d(np.diff(_cases), 3))
	_smoothed_new_cases: ndarray = np.insert(new_cases, 0, _cases[0])
	zero_case_idx: list = np.where(_smoothed_new_cases <= 0)[0].tolist()
	return (
		np.delete(_cases, zero_case_idx),
		np.delete(_smoothed_new_cases, zero_case_idx),
		np.delete(cases[idx_start:].index.to_list(), zero_case_idx)
	)


def compute_rt(smoothed_new_cases: ndarray) -> Tuple[ndarray, ndarray, ndarray]:
	"""
	Compute the time series of Rt with the corresponding credible interval.

	Args:
		smoothed_new_cases: 1d np.ndarray
			Time series of the number of new cases for each day.
	Returns:
		Tuple with 3 one-dimensional np.ndarray-s.:
		- time series of Rt;
		- time series of lower boundary of high intensity interval;
		- time series of higher boundary of high intensity interval.
	"""
	posteriors, _ = get_posteriors(ts=smoothed_new_cases)
	rts: ndarray = np.asarray([_RT_RANGE[i] for i in np.argmax(posteriors, axis=1)])
	lows: ndarray = np.zeros(posteriors.shape[0])
	highs: ndarray = np.zeros_like(lows)
	for i, pmf in enumerate(posteriors):
		_low, _high = high_density_interval(pmf=pmf)
		lows[i] = _low
		highs[i] = _high
	return rts, lows, highs


def get_us_county_data() -> DataFrame:
	_counties_full: DataFrame = pd.read_csv(
		'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv',
		usecols=[0, 1, 2, 3, 4],
		parse_dates=['date'],
		squeeze=True
	)
	_counties_full['fips'] = _counties_full['fips'].apply(lambda x: str(int(x)) if not pd.isna(x) else np.NaN)
	_counties_full.loc[_counties_full['county'] == 'New York City', 'fips'] = _NYC_FIPS
	_counties_full = _counties_full[~pd.isna(_counties_full['fips'])]
	_counties_full.set_index(['fips', 'date'], inplace=True)
	_counties_full.sort_index(inplace=True)
	_counties_full: DataFrame = _counties_full.loc[_counties_full.index.get_level_values('date') != pd.to_datetime(date.today())]
	return _counties_full


def coord_to_fips(lat: float, lng: float) -> Tuple[str, str, str]:
	results_response_key: str = 'results'
	county_fips_response_key: str = 'county_fips'
	county_name_response_key: str = 'county_name'
	state_name_response_key: str = 'state_name'
	with urlopen("https://geo.fcc.gov/api/census/area?lat={}&lon={}&format=json".format(lat, lng)) as url:
		data: str = json.loads(url.read().decode())
	if results_response_key in data:
		if len(data[results_response_key]) >= 1:
			if county_fips_response_key in data[results_response_key][0]:
				fips: str = data[results_response_key][0][county_fips_response_key]
				county_name: str = data[results_response_key][0][county_name_response_key]
				if fips in _NYC_COUNTIES_FIPS_TO_NAME.keys():
					fips: str = _NYC_FIPS
					county_name: str = "New York City"
				return (
					fips,
					county_name,
					data[results_response_key][0][state_name_response_key]
				)
	return None, None, None


def update_rt_estimates_usa():
	counties_full: DataFrame = get_us_county_data()
	all_fips: List[str] = counties_full.index.get_level_values('fips').unique().to_list()
	all_estimates: List[DataFrame] = []
	for fips in all_fips:
		try:
			county_data = counties_full.xs(fips)
		except KeyError as ke:
			logger.error(ke)
		if len(county_data) <= 1:
			continue
		county_name = county_data.iloc[0]['county']
		state_name = county_data.iloc[0]['state']
		country_code = 'USA'
		cases = county_data['cases']
		_, smoothed, index_dates = prepare_cases(cases=cases)
		try:
			rt, low, high = compute_rt(smoothed_new_cases=smoothed)
		except TimeSeriesDimensionError	as e:
			logger.error(e)
			continue
		rt_region_estimate = DataFrame({
			'rt_estimate': rt,
			'rt_low': low,
			'rt_high': high,
			'date': index_dates,
			'country_code': country_code,
			'first_administrative_division_name': state_name,
			'region_code': fips,
			'region_name': county_name
		})
		all_estimates.append(rt_region_estimate)

	all_estimates_df = pd.concat(all_estimates)
	all_estimates_df.reset_index(inplace=True, drop=True)
	database_connection = sqlalchemy.create_engine(generate_db_uri())
	all_estimates_tbl_name: str = 'rt_estimates'
	all_estimates_tmp_tbl_name: str = 'rt_estimates_tmp'
	all_estimates_df.to_sql(name=all_estimates_tmp_tbl_name, con=database_connection, if_exists='replace', index=False)
	with database_connection.begin() as cnx:
		insert_sql: str = """
			INSERT IGNORE INTO {}({}, `modified`)
			SELECT {}, UTC_TIMESTAMP() FROM {} as t
			ON DUPLICATE KEY UPDATE
				`rt_estimate` = t.`rt_estimate`,
				`rt_low` = t.`rt_low`,
				`rt_high` = t.`rt_high`,
				`modified` = UTC_TIMESTAMP()
		""".format(
			all_estimates_tbl_name,
			', '.join(list(all_estimates_df.columns)),
			', '.join(list(all_estimates_df.columns)),
			all_estimates_tmp_tbl_name
		)
		cnx.execute(insert_sql)
		delete_tmp_table_sql: str = "DROP TABLE IF EXISTS {}".format(all_estimates_tmp_tbl_name)
		cnx.execute(delete_tmp_table_sql)


class RtEstimate(object):
	def __init__(
		self,
		_date: List[date] = None,
		rt_estimate: List[float] = None,
		rt_low: List[float] = None,
		rt_high: List[float] = None
	):
		self._date: List[date] = _date
		self._rt_estimate: List[float] = rt_estimate
		self._rt_low: List[float] = rt_low
		self._rt_high: List[float] = rt_high

	@property
	def date(self) -> List[date]:
		return self._date

	@property
	def rt_estimate(self) -> List[float]:
		return self._rt_estimate

	@property
	def rt_low(self) -> List[float]:
		return self._rt_low

	@property
	def rt_high(self) -> List[float]:
		return self._rt_high


def fetch_usa_rt_estimate(fips: str) -> RtEstimate:
	rdb: RDBManager = RDBManager(reader=True)
	rt_estimates_data, err = rdb.execute(
		sql_query="""
			SELECT
				`date`,
				`rt_estimate`,
				`rt_low`,
				`rt_high`
			FROM `rt_estimates`
			WHERE
				`country_code` = 'USA'
				AND
				`region_code` = '{}'
			ORDER BY `date` ASC
		""".format(fips)
	)
	if err is not None:
		logger.error(err)
	if len(rt_estimates_data) > 0:
		rt_estimate = RtEstimate(
			_date=[item['date'] for item in rt_estimates_data],
			rt_estimate=[float(item['rt_estimate']) for item in rt_estimates_data],
			rt_low=[float(item['rt_low']) for item in rt_estimates_data],
			rt_high=[float(item['rt_high']) for item in rt_estimates_data]
		)
		return rt_estimate
	return RtEstimate()
