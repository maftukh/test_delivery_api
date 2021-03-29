import re
import typing as tp

weight_dict = {
    'foot': 10,
    'bike': 15,
    'car': 50
}

coefficient_dict = {
    'foot': 2,
    'bike': 5,
    'car': 9
}


def is_valid_type(type: str):
    if type in {'foot', 'bike', 'car'}:
        return True
    return False


def is_valid_weight(weight: float):
    if weight < 0.01:
        return False
    elif weight > 50:
        return False
    return True


def recalculate_orders(data: dict, orders: tp.List[dict]):
    removed_orders = []
    try:
        max_weight = weight_dict[data['courier_type']]
        for order in orders:
            if order['weight'] > max_weight:
                removed_orders.append(order['order_id'])
    except KeyError:
        pass

    try:
        regions = data['regions']
        for order in orders:
            if order['region'] not in regions:
                removed_orders.append(order['order_id'])
    except KeyError:
        pass

    try:
        working_hours = data['working_hours']
        for order in orders:
            if not check_hours(working_hours, order['delivery_hours']):
                removed_orders.append(order['order_id'])
    except KeyError:
        pass

    return removed_orders


def validate_keys(valid_cols: tp.List[str], data: dict, raise_missing: bool = True, num: int = 4):
    for key in data:
        if key not in valid_cols:
            raise ValueError
    if raise_missing:
        if len(data) != num:
            raise ValueError


def check_hours(hours_1: tp.List[str], hours_2: tp.List[str]):
    for hour_1 in hours_1:
        split = re.split(':|-', hour_1)
        min_1 = int(split[0]) * 60 + int(split[1])
        max_1 = int(split[2]) * 60 + int(split[3])
        for hour_2 in hours_2:
            split = re.split(':|-', hour_2)
            min_2 = int(split[0]) * 60 + int(split[1])
            max_2 = int(split[2]) * 60 + int(split[3])
            if min_2 <= min_1 < max_2 or min_1 <= min_2 < max_1:
                return True
    return False


def match_orders_by_hours(hours: tp.List[str], rel_orders: tp.List[dict]):
    matching_orders = []
    for elem in rel_orders:
        if check_hours(hours, elem['delivery_hours'].split(',')):
            matching_orders.append(elem['order_id'])
    return matching_orders


def calculate_earnings(orders: tp.List[tp.Any]):
    return sum([order['assigned_type_coef'] * 500 for order in orders])


def calculate_rating(orders: tp.List[tp.Any]):
    orders = sorted(orders, key=lambda x: x['complete_time'])
    prev_complete_time = None
    region_wise_times = dict()
    for order in orders:
        time_since_assigned = order['complete_time'] - order['assign_time']
        if prev_complete_time is None:
            delivery_time = time_since_assigned
        else:
            time_since_previous = order['complete_time'] - prev_complete_time
            delivery_time = min([time_since_previous, time_since_assigned])

        try:
            region_wise_times[order['region']].append(delivery_time)
        except KeyError:
            region_wise_times[order['region']] = [delivery_time]

        prev_complete_time = order['complete_time']

    one_hour: int = 60 * 60
    min_average_time = one_hour
    for key, value in region_wise_times.items():
        region_min = min(value).seconds
        if region_min < min_average_time:
            min_average_time = region_min

    return 5 * (one_hour - min_average_time) / one_hour
