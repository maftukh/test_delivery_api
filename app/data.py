import re
from datetime import datetime, timezone
import typing as tp

import iso8601
import sqlalchemy as db
from sqlalchemy.engine import Engine

from config import *
from app.utils import *


def init_db():
    """
    Инициализируем Engine для нашей базы данных и 2 таблицы:
    orders: хранятся заказы и их статус (курьер и время его назначения, статус и время выполнения)
    couriers: хранится информация про курьеров

    Для простоты выбрал БД SQLite, но все на SQLAlchemy, поэтому можно на другие БД перейти относительно несложно
    """
    engine = db.create_engine(DATABASE_URI)
    metadata = db.MetaData()
    orders = db.Table('orders', metadata,
                      db.Column('order_id', db.Integer, nullable=False, primary_key=True),
                      db.Column('weight', db.Float, nullable=False),
                      db.Column('region', db.Integer, nullable=False),
                      db.Column('delivery_hours', db.String, nullable=False),
                      db.Column('courier_id', db.Integer, nullable=True),
                      db.Column('assign_time', db.DateTime, nullable=True),
                      db.Column('complete', db.Boolean, nullable=False, default=False),
                      db.Column('complete_time', db.DateTime, nullable=True),
                      db.Column('assigned_type_coef', db.Integer, nullable=False, default=0)
                      )
    metadata.create_all(engine)

    couriers = db.Table('couriers', metadata,
                        db.Column('courier_id', db.Integer, nullable=False, primary_key=True),
                        db.Column('courier_type', db.String, nullable=False),
                        db.Column('regions', db.String, nullable=False),
                        db.Column('working_hours', db.String, nullable=False)
                        )
    metadata.create_all(engine)
    return engine, orders, couriers


class Order:
    def __init__(self, engine: Engine, table: db.Table):
        self.engine = engine
        self.table = table
        self.id_col = 'order_id'
        self.valid_cols = ['order_id', 'weight', 'region', 'delivery_hours']

    def insert_row(self, data: dict):
        with self.engine.connect() as con:
            id = data[self.id_col]
            query = db.insert(self.table).values(order_id=data['order_id'],
                                                 weight=data['weight'],
                                                 region=data['region'],
                                                 delivery_hours=",".join(data['delivery_hours']))
            # courier_id=db.sql.null())
            con.execute(query)
        return id

    @staticmethod
    def validate_data(data: dict):
        if not isinstance(data['order_id'], int):
            raise ValueError
        if not is_valid_weight(data['weight']):
            raise ValueError
        if not isinstance(data['region'], int):
            raise ValueError
        for w_hour in data['delivery_hours']:
            if not re.match('(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]-(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]', w_hour):
                raise ValueError

    def add(self, data: dict):
        """
        Валидирует список курьеров и добавляет их в базу. Возвращает список добавленных айди и флаг успеха
        В случае невалидных данных возвращает список невалидных айди, база не обновляется
        """
        exceptions = []
        for elem in data:
            try:
                validate_keys(self.valid_cols, elem)
                self.validate_data(elem)
            except (KeyError, ValueError):
                exceptions.append(elem['order_id'])
        if exceptions:
            return exceptions, False
        ids = []
        for elem in data:
            ids.append(self.insert_row(elem))
        return ids, True

    def get_courier_orders(self, courier_id: int, completed: bool = False):
        with self.engine.connect() as conn:
            if completed:
                select = db.select(self.table) \
                    .where(self.table.columns.courier_id == courier_id,
                           self.table.columns.complete == True)
            else:
                select = db.select(self.table) \
                    .where(self.table.columns.courier_id == courier_id)
            data = conn.execute(select).fetchall()
        return data

    def cancel_orders(self, orders: tp.List[dict]):
        with self.engine.connect() as con:
            query = self.table.update() \
                .where(self.table.columns.order_id.in_(orders)) \
                .values(courier_id=None, assign_time=None,
                        assigned_type_coef=0)
            con.execute(query)

    def assign_courier(self, courier_id: int, courier_type: str, orders: tp.List[int]):
        assign_time = datetime.now(timezone.utc).astimezone()

        with self.engine.connect() as con:
            query = self.table.update() \
                .where(self.table.columns.order_id.in_(orders)) \
                .values(courier_id=courier_id,
                        assign_time=assign_time,
                        assigned_type_coef=coefficient_dict[courier_type])
            con.execute(query)

        return assign_time.isoformat()

    def orders_for_courier(self, courier: dict):
        regions = list(map(int, courier['regions'].split(',')))
        max_weight = weight_dict[courier['courier_type']]
        hours = courier['working_hours'].split(',')

        select = self.table.select().where(
            self.table.columns.region.in_(regions),
            self.table.columns.weight <= max_weight,
            self.table.columns.complete == False,
            self.table.columns.courier_id == None
        )
        with self.engine.connect() as con:
            rel_orders = con.execute(select).fetchall()
        if not rel_orders:
            return [], None
        matching_orders = match_orders_by_hours(hours, rel_orders)
        assign_time = self.assign_courier(courier['courier_id'], courier['courier_type'], matching_orders)
        return matching_orders, assign_time

    def validate_assignment(self, order_id: int, courier_id: int):
        with self.engine.connect() as con:
            resp = con.execute(self.table.select() \
                               .where(self.table.columns.order_id == order_id)).fetchone()
        if resp['courier_id'] != courier_id:
            raise AssertionError

    def complete_order(self, order_id: int, complete_time: datetime):
        complete_time = iso8601.parse_date(complete_time)
        with self.engine.connect() as con:
            con.execute(self.table.update()
                        .where(self.table.columns.order_id == order_id) \
                        .values(complete=True, complete_time=complete_time))

    def get_existing_ids(self, order_ids: tp.List[int]):
        with self.engine.connect() as con:
            select = db.select(self.table.columns.courier_id) \
                .where(self.table.columns.order_id.in_(order_ids))
            existing_ids = con.execute(select).fetchall()
        return [el[0] for el in existing_ids]


class Courier:
    def __init__(self, engine: Engine, table: db.Table):
        self.engine = engine
        self.table = table
        self.id_col = 'courier_id'
        self.valid_cols = ['courier_id', 'courier_type', 'regions', 'working_hours']

    def insert_row(self, data: dict):
        with self.engine.connect() as con:
            id = data[self.id_col]
            query = db.insert(self.table).values(courier_id=data['courier_id'],
                                                 courier_type=data['courier_type'],
                                                 regions=",".join(map(str, data['regions'])),
                                                 working_hours=",".join(data['working_hours']))
            con.execute(query)
        return id

    @staticmethod
    def validate_data(data: dict):
        if not isinstance(data['courier_id'], int):
            raise ValueError
        if not is_valid_type(data['courier_type']):
            raise ValueError
        for region in data['regions']:
            if not isinstance(region, int):
                raise ValueError
        for w_hour in data['working_hours']:
            if not re.match('(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]-(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]', w_hour):
                raise ValueError

    def add(self, data: dict):
        """
        Валидирует список курьеров и добавляет их в базу. Возвращает список добавленных айди и флаг успеха
        В случае невалидных данных возвращает список невалидных айди, база не обновляется
        """
        exceptions = []
        for elem in data:
            try:
                validate_keys(self.valid_cols, elem)
                self.validate_data(elem)
            except (KeyError, ValueError):
                exceptions.append(elem['courier_id'])
        if exceptions:
            return exceptions, False
        ids = []
        for elem in data:
            ids.append(self.insert_row(elem))
        return ids, True

    def get_by_id(self, courier_id: int):
        with self.engine.connect() as con:
            select = db.select(self.table) \
                .where(self.table.columns.courier_id == courier_id)
            data = con.execute(select).fetchone()
        return data

    def get_existing_ids(self, courier_ids: tp.List[int]):
        with self.engine.connect() as con:
            select = db.select(self.table.columns.courier_id) \
                .where(self.table.columns.courier_id.in_(courier_ids))
            existing_ids = con.execute(select).fetchall()
        return [el[0] for el in existing_ids]

    def update_data(self, courier_id: int, data: dict):
        try:
            validate_keys(self.valid_cols, data, raise_missing=False)
        except ValueError:
            return None
        with self.engine.connect() as conn:
            # Update data
            upd = db.update(self.table) \
                .where(self.table.columns.courier_id == courier_id) \
                .values(**data)
            conn.execute(upd)

        # Return updated data
        updated_data = self.get_by_id(courier_id)
        return dict(zip(self.valid_cols,
                        list(updated_data)))
