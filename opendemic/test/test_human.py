import pytest
from opendemic.database import RDBManager
from opendemic.human import model
from opendemic.human.location import controller

lat = "40.2"
long = "-70.223"


@pytest.fixture
def human():
    rdb = RDBManager()
    records, err = rdb.execute(
        sql_query="""SELECT id FROM `humans` WHERE `fingerprint` is not null LIMIT 1""")
    human_id = records[0][model.HumanProperties.ID.value]
    human = model.Human(human_id=human_id)
    return human


def test_validate_location_url_params_success(human):
    params = create_fake_parameters(human.get_fingerprint(), lat, long, False)
    err = controller.validate_location_url_params(params=params)
    assert len(err) == 0


def test_validate_location_url_params_fail():
    params = create_fake_parameters("123", lat, long, False)
    err = controller.validate_location_url_params(params=params)
    assert len(err) == 1


def test_get_human_from_fingerprint(human):
    returned_human = model.get_human_from_fingerprint(human.get_fingerprint())
    assert human == human


def test_get_risky_humans_geojson(human):
    risky_humans, err = model.get_risky_humans(lat, long, 1, 1)
    assert err is None


def test_create_human(human):
    created_human, err = model.create_human(None, human.get_fingerprint())
    human_exist, retrieved_human = model.verify_human_exists(created_human.id)
    assert human_exist


def create_fake_parameters(fingerprint: str, lat: str, long: str, include_legend: bool):
    params = dict()
    params[controller.LocationResourceFields.FINGERPRINT.value] = fingerprint
    params[controller.LocationResourceFields.LATITUDE.value] = lat
    params[controller.LocationResourceFields.LONGITUDE.value] = long
    params[controller.LocationResourceFields.INCLUDE_LEGEND.value] = include_legend
    return params
