from typing import Tuple, List, Dict
from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from bot.entities import Product


btn_cb = CallbackData('item', 'id', 'action_type')

action_types = ('select', 'forward', 'back')
elements_on_page = 5


def prettify_product_list(products: Tuple[Product]) -> str:
    return ''.join([
        f'<b>{i}.</b> <a href="{p.url}">{p.title}</a>\n'
        for i, p in enumerate(products, 1)
    ])


def prettify_product_info(product: Product) -> str:
    options = ''
    for opt in product.product_options:
        options += (
            f'<b>Option:</b> {opt.title}\n'
            f'<b>Price:</b> R{opt.price}\n'
            f'<b>Availability:</b> {opt.availability}\n'
            '\n'
        )

    return (
        f'<a href="{product.url}"><b>{product.title}</b></a>\n'
        f'<b>Brand:</b> {product.brand}\n'
        f'<b>Product type:</b> {product.product_type}\n'
        f'<b>Rating:</b> {product.rating} / 5.0\n'
        f'<b>Reviews:</b> {product.reviews}\n'
        f'<b>Description:</b> {product.description}\n'
        f'\n{options}'
    )


def create_pages_from_products(products: List[Dict]) -> List[List[Dict]]:
    if len(products) < elements_on_page:
        return [products]

    pages_len = ceil(len(products)/elements_on_page)
    pages = [[] for _ in range(pages_len)]

    i = 0
    for idx, product in enumerate(products):
        if idx != 0 and idx % elements_on_page == 0:
            i += 1
        pages[i].append(product)
    return pages


def get_keyboard_for_page(pages: List[List[Dict]], page_num: int = 1) -> InlineKeyboardMarkup:
    products = pages[page_num-1]
    buttons = [
        InlineKeyboardButton(
            p['title'],
            callback_data=btn_cb.new(id=p['id'], action_type=action_types[0])
        )
        for p in products
    ]

    if page_num > 1:
        buttons.append(InlineKeyboardButton(
            '⬅️',
            callback_data=btn_cb.new(id=page_num-1, action_type=action_types[2])
        ))

    if 1 <= page_num < len(pages):
        buttons.append(InlineKeyboardButton(
            '➡️',
            callback_data=btn_cb.new(id=page_num+1, action_type=action_types[1])
        ))

    keyboard = InlineKeyboardMarkup(row_width=1)
    for btn in buttons:
        keyboard.add(btn)

    return keyboard
