from flask import request, jsonify, abort, render_template, redirect
from app import app, db
from app.data import Courier, Order


weight_dict = {
    'foot': 10,
    'bike': 15,
    'car': 50
}


def is_valid_type(type: str):
    if type in {'foot', 'bike', 'car'}:
        return True
    return False


def recalculate_orders(courier_id: int):
    pass


@app.route('/couriers', methods=['POST'])
def couriers():
    """
    Принимает json с данными о курьерах и заносит в базу
    """
    if not request.json or 'data' not in request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400

    exceptions = []
    imported = []
    for courier in request.json['data']:
        try:
            db.session.add(Courier(
                courier['courier_id'],
                courier['courier_type'],
                courier['regions'],
                courier['working_hours']
            ))
            if is_valid_type(courier['courier_type']):
                imported.append(courier['courier_id'])
            else:
                exceptions.append(courier['courier_id'])
        except (ValueError, KeyError):
            exceptions.append(courier['courier_id'])
    if exceptions:
        db.session.rollback()
        return jsonify({"validation_error": {
            "couriers": [{"id": i} for i in exceptions]
        }}), 400
    else:
        db.session.commit()
        return jsonify({"couriers": [{"id": i} for i in imported]}), 201


@app.route('/couriers/<int:courier_id>', methods=['PATCH'])
def patch_couriers(courier_id: int):
    if not request.json:
        return jsonify({'validation_error': {
            'reason': 'No data given'
        }}), 400
    courier = Courier.query.filter_by(courier_courier_id=courier_id)
    for key, value in request.json:
        courier[key] = value
    recalculate_orders(courier_id)
