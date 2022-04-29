from typing import Tuple, List, Dict
from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

from bot.entities import Product


select_cb = CallbackData('product', 'product_id')
navigation_cb = CallbackData('nav', 'page_num')
confirm_cb = CallbackData('conf')

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
            f'<b>Price:</b> R{opt.price:.2f}\n'
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


def get_keyboard_for_page(pages: List[List[Dict]], page_num: int = 1, checked_ids: List[int] = []) -> InlineKeyboardMarkup:
    products = pages[page_num-1]
    buttons = [
        InlineKeyboardButton(
            '☑️' + p['title'] if p['id'] in checked_ids else p['title'],
            callback_data=select_cb.new(product_id=p['id'])
        )
        for p in products
    ]

    if page_num > 1:
        buttons.append(InlineKeyboardButton(
            '⬅️ Back',
            callback_data=navigation_cb.new(page_num=page_num-1)
        ))

    if 1 <= page_num < len(pages):
        buttons.append(InlineKeyboardButton(
            '➡️ Next',
            callback_data=navigation_cb.new(page_num=page_num+1)
        ))

    buttons.append(InlineKeyboardButton('🆗 Confirm', callback_data=confirm_cb.new()))

    keyboard = InlineKeyboardMarkup(row_width=1)
    for btn in buttons:
        keyboard.add(btn)

    return keyboard
