import requests
from tests.utils_for_test import *


def test_type_error():
    response = requests.post("http://0.0.0.0:8080/couriers",
                             json = {"data": [
                                 create_courier_dict(i, 'type', generate_set_of_regions(), [generate_delivery_hours()])
                                 for i in range(10)
                             ]})
    assert response.status_code == 400
    assert response.json() == {"validation_error": {
            "couriers": [{"id": i} for i in range(10)]
        }}


def test_data_error():
    response = requests.post("http://0.0.0.0:8080/couriers",
                             json={"data": [
                                 {"courier_id": 0}
                             ]})
    assert response.status_code == 400
    assert response.json() == {"validation_error": {
        "couriers": [{"id": 0}]
    }}


def test_basic():
    response = requests.post("http://0.0.0.0:8080/couriers",
                             json = {"data": [
                                 create_courier_dict(i, generate_courier_type(),
                                                     generate_set_of_regions(), [generate_delivery_hours()])
                                 for i in range(10)
                             ]})
    assert response.status_code == 201
    assert response.json() == {"couriers": [{"id": i} for i in range(10)]}
