import typing as tp
from app import db


class Order(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    _order_id = db.Column(db.Integer, primary_key=True, name='order_id')
    _weight = db.Column(db.Float, name='weight')
    _region = db.Column(db.Integer, name='region')
    _delivery_hours = db.Column(db.String, name='delivery_hours')
    _courier = db.Column(db.Integer, nullable=True)

    def __init__(self, order_id, weight, region, delivery_hours):
        self._order_id = order_id
        self._weight = weight
        self._region = region
        self._delivery_hours = ",".join(delivery_hours)
        self._courier = None


class Courier(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    _courier_id = db.Column(db.Integer, primary_key=True, name='courier_id')
    _courier_type = db.Column(db.String, name='courier_type')
    _regions = db.Column(db.String, name='regions')
    _working_hours = db.Column(db.String, name='working_hours')

    def __init__(self, courier_id, courier_type, regions, working_hours):
        self._courier_id = courier_id
        self._courier_type = courier_type
        self._regions = ",".join(map(str, regions))
        self._working_hours = ",".join(working_hours)

    @property
    def courier_id(self):
        return self._courier_id

    @courier_id.setter
    def courier_id(self, courier_id: int):
        self._courier_id = courier_id

    @property
    def courier_type(self):
        return self._courier_type

    @courier_type.setter
    def courier_type(self, type: str):
        if type in ['foot', 'bike', 'car']:
            self._courier_type = type
        else:
            raise ValueError("courier_type")

    @property
    def regions(self):
        return list(map(int, self._regions.split(',')))

    @regions.setter
    def regions(self, regions: tp.List[int]):
        self._regions = ",".join(map(str, regions))

    @property
    def working_hours(self):
        return self._working_hours.split(',')

    @working_hours.setter
    def working_hours(self, working_hours: tp.List[str]):
        self._working_hours = ",".join(working_hours)


db.create_all()