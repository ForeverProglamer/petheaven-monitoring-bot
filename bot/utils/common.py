from typing import Any, Dict, Callable, Iterable, List, Union 
from json import load

from bot.entities import ProductOption


bot_text_file = 'bot_text.json'


def get_bot_text() -> Dict[str, str]:
    with open(bot_text_file, 'rb') as f:
        return load(f)


bot_text = get_bot_text()
MESSAGES = bot_text['messages']
BUTTONS = bot_text['buttons']


def find_item(func: Callable[[Any], bool], iterable: Iterable) -> Union[Any, None]:
    try:
        return next(filter(func, iterable))
    except StopIteration:
        return None


def find_items(func: Callable[[Any], bool], iterable: Iterable) -> Union[List[Any], List]:
    try:
        return list(filter(func, iterable))
    except StopIteration:
        return []


def group_product_options_by_ids(product_ids: List, data_to_group: List[List]) -> Dict[int, ProductOption]:
    groups_from_data = set([item[-1] for item in data_to_group])
    grouped_data = {
        group: [] for group in product_ids if group in groups_from_data
    }

    for item in data_to_group:
        grouped_data[item[-1]].append(ProductOption._make(item[:-1]))
    
    return grouped_data
                