from typing import Dict, List, Set

from bot.entities import Notification, Product, ProductOption


MAX_MESSAGES_PER_SECOND = 30


def group_product_options_by_ids(product_ids: List, data_to_group: List[List]) -> Dict[int, List[ProductOption]]:
    groups_from_data = set([item[-1] for item in data_to_group])
    grouped_data = {
        group: [] for group in product_ids if group in groups_from_data
    }

    for item in data_to_group:
        grouped_data[item[-1]].append(ProductOption._make(item[:-1]))
    
    return grouped_data


def to_products(data: List[List]) -> List[Product]:
    product_option_start_index = 9

    products_data = list(set(
        item[:product_option_start_index] for item in data
    ))

    product_options = [
        [*item[product_option_start_index:], item[0]] for item in data
    ]

    grouped_data = group_product_options_by_ids(
        [item[0] for item in products_data],
        product_options
    )

    return [
        Product._make((*item, grouped_data[item[0]]))
        for item in products_data
    ]


def choose_notifications(notifications: Set[Notification]) -> List[Notification]:
    notifications_to_send = []
    receivers = set()

    for n in notifications:
        if n.receiver_id not in receivers:
            notifications_to_send.append(n)
            receivers.add(n.receiver_id)

        if len(notifications_to_send) >= MAX_MESSAGES_PER_SECOND:
            return notifications_to_send

    return notifications_to_send
