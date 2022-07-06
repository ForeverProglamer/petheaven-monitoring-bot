from typing import Any, Dict, Callable, Iterable, List, Union
from json import load


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
