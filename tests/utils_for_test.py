import random
import typing as tp

REGION_RANGE = list(range(10))
NUM_OF_REGIONS = list(range(1,5))


def create_order_dict(o_id, weight, region, hours):
    return {
        'order_id': o_id,
        'weight': weight,
        'region': region,
        'delivery_hours': hours
    }


def create_courier_dict(c_id, c_type, regs, hours):
    return {
        'courier_id': c_id,
        'courier_type': c_type,
        'regions': regs,
        'working_hours': hours
    }


def get_random_from_seq(seq: tp.List[tp.Any]):
    return random.choice(seq)


def generate_courier_type():
    lst = ['foot', 'bike', 'car']
    return get_random_from_seq(lst)


def generate_region():
    lst = REGION_RANGE
    return get_random_from_seq(lst)


def generate_set_of_regions():
    n = random.choice(NUM_OF_REGIONS)
    return random.sample(REGION_RANGE, n)


def generate_weight():
    return random.choice(list(range(50))) + 1 / random.choice(list(range(100)))


def generate_delivery_hours():
    start = get_random_from_seq(list(range(6, 16)))
    return f'{"0" * (1 - start // 10)}{start}:00-{start + 8}:00'