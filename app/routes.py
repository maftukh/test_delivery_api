from flask import request, jsonify

from app import app
from app.data import init_db, Courier, Order
from app.utils import *

engine, orders, couriers = init_db()
Couriers = Courier(engine, couriers)
Orders = Order(engine, orders)


@app.route('/couriers', methods=['POST'])
def post_couriers():
    """
    Принимает json с данными о курьерах и заносит в базу
    """
    if not request.json or 'data' not in request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400
    all_ids = [elem['courier_id'] for elem in request.json['data']]

    # Some non-obvious decision: nothing specified about handling duplicates
    # I decided to call a request non-valid if it contains already existing ids
    existing_ids = Couriers.get_existing_ids(all_ids)
    if existing_ids:
        ids = existing_ids
        success = False
    else:
        ids, success = Couriers.add(request.json['data'])
    if success:
        return jsonify({"couriers": [{"id": i} for i in ids]}), 201
    else:
        return jsonify({"validation_error": {
            "couriers": [{"id": i} for i in ids]
        }}), 400


@app.route('/couriers/<int:courier_id>', methods=['PATCH'])
def patch_couriers(courier_id: int):
    if not request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400
    data = Couriers.update_data(courier_id, request.json)
    if data is None:
        return jsonify({'validation_error': {
            'reason': 'wrong columns given'
        }}), 400
    active_orders = Orders.get_courier_orders(courier_id)
    removed_orders = recalculate_orders(request.json, active_orders)
    Orders.cancel_orders(removed_orders)
    return jsonify(data), 200


@app.route('/orders', methods=['POST'])
def post_orders():
    """
    Принимает json с данными о заказах и заносит в базу
    """
    if not request.json or 'data' not in request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400
    all_ids = [elem['order_id'] for elem in request.json['data']]

    # Some non-obvious decision: nothing specified about handling duplicates
    # I decided to call a request non-valid if it contains already existing ids
    existing_ids = Orders.get_existing_ids(all_ids)
    if existing_ids:
        ids = existing_ids
        success = False
    else:
        ids, success = Orders.add(request.json['data'])

    if success:
        return jsonify({"orders": [{"id": i} for i in ids]}), 201
    else:
        return jsonify({"validation_error": {
            "orders": [{"id": i} for i in ids]
        }}), 400


@app.route('/orders/assign', methods=['POST'])
def assign_orders():
    if not request.json or 'courier_id' not in request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400

    courier_data = Couriers.get_by_id(request.json['courier_id'])
    matching_orders, assign_time = Orders.orders_for_courier(courier_data)

    if not matching_orders:
        return jsonify({'orders': []}), 200
    return jsonify({'orders': [{'id': i} for i in matching_orders],
                    'assign_time': assign_time}), 200


@app.route('/orders/complete', methods=['POST'])
def complete_order():
    """
    Отмечает заказ выполненным. Принимает айди курьера, заказа и время выполнения
    """
    if not request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400
    try:
        validate_keys({'order_id', 'courier_id', 'complete_time'}, request.json,
                      raise_missing=True, num=3)
    except (KeyError, ValueError):
        return jsonify({'validation_error': {
            'reason': 'Missing data'
        }}), 400
    try:
        Orders.validate_assignment(request.json['order_id'], request.json['courier_id'])
    except AssertionError:
        return jsonify({'validation_error': {
            'reason': 'Courier was not assigned'
        }}), 400

    Orders.complete_order(request.json['order_id'], request.json['complete_time'])
    return jsonify({'order_id': request.json['order_id']}), 200


@app.route('/couriers/<int:courier_id>', methods=['GET'])
def get_courier_info(courier_id: int):
    data = dict(Couriers.get_by_id(courier_id))
    completed_orders = Orders.get_courier_orders(courier_id=courier_id, completed=True)
    if completed_orders:
        data['earnings'] = calculate_earnings(completed_orders)
        data['rating'] = calculate_rating(completed_orders)
    else:
        data['earnings'] = 0
    return jsonify(data), 200
