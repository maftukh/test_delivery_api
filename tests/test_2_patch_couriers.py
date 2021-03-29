import requests
from tests.utils_for_test import *


def test_error():
    response = requests.patch('http://0.0.0.0:8080/couriers/0',
                              json = {'data': [
                                  {'courier_type': 'car',
                                   'some_other_type': 'changed'},
                              ]})
    assert response.status_code == 400
    assert response.json() == {'validation_error': {
            'reason': 'wrong columns given'
        }}


def test_basic():
    response = requests.patch('http://0.0.0.0:8080/couriers/0',
                              json = {'courier_type': 'car'})
    assert response.status_code == 200 
    assert response.json()['courier_type'] == 'car'

