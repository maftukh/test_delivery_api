import requests
from tests.utils_for_test import *


def test_weight_error():
    response = requests.post("http://0.0.0.0:8080/orders",
                             json = {"data": [
                                 create_order_dict(i, 0.001 + i * 6, generate_region(), [generate_delivery_hours()])
                                 for i in range(10)
                             ]})
    assert response.status_code == 400
    assert response.json() == {"validation_error": {
            "orders": [{"id": i} for i in [0, 9]]
        }}


def test_data_error():
    response = requests.post("http://0.0.0.0:8080/orders",
                             json={"data": [
                                 {"order_id": 0}
                             ]})
    assert response.status_code == 400
    assert response.json() == {"validation_error": {
        "orders": [{"id": 0}]
    }}


def test_basic():
    response = requests.post("http://0.0.0.0:8080/orders",
                             json = {"data": [
                                 create_order_dict(i, generate_weight(), generate_region(), [generate_delivery_hours()])
                                 for i in range(10)
                             ]})
    assert response.status_code == 201
    assert response.json() == {"orders": [{"id": i} for i in range(10)]}


