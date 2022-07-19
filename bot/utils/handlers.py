from typing import Dict, List, Tuple

from aiogram.dispatcher.storage import FSMContext
from aiogram.types import CallbackQuery, Message, ParseMode
from aiogram.utils.exceptions import WrongFileIdentifier

from bot.entities import Product
from bot.states import MonitorProducts
from bot.views.product_info import render_product, render_product_list
from .keyboard import create_pages_from_products, get_keyboard_for_page
from .common import BUTTONS, MESSAGES


def get_ui_for_monitor_command(products: List[Product]) -> Tuple[str, Tuple[str]]:
    if not products:
        return MESSAGES['monitor_no_products'], (BUTTONS['add'],)

    message = MESSAGES['monitor_list'].format(render_product_list(products))
    return message, (*BUTTONS.values(),)


async def send_products_info(call: CallbackQuery, products: List[Product]) -> None:
    for product in products:
        await call.message.answer(
            render_product(product),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        try:
            await call.message.answer_photo(product.img, product.title)
        except WrongFileIdentifier:
            await call.message.answer(
                MESSAGES['info_photo_error'].format(product.title)
            )


async def get_pages(state: FSMContext) -> List[List[Dict]]:
    async with state.proxy() as data:
        products = data['products']

    return create_pages_from_products(products)


async def monitor_info_button_handler(message: Message, state: FSMContext) -> None:
    pages = await get_pages(state)
    await state.update_data(current_page=1, checked_products=[])

    await message.answer(
        MESSAGES['info_start'],
        reply_markup=get_keyboard_for_page(pages)
    )

    await MonitorProducts.on_getting_product_info.set()


async def monitor_add_button_handler(message: Message, state: FSMContext) -> None:
    await message.answer(MESSAGES['add_start'])
    await MonitorProducts.on_adding_product.set()


async def monitor_remove_button_handler(message: Message, state: FSMContext) -> None:
    pages = await get_pages(state)
    await state.update_data(current_page=1, checked_products=[])

    await message.answer(
        MESSAGES['remove_start'],
        reply_markup=get_keyboard_for_page(pages)
    )
    await MonitorProducts.on_removing_product.set()


monitor_menu_handlers = {
    BUTTONS['info']: monitor_info_button_handler,
    BUTTONS['add']: monitor_add_button_handler,
    BUTTONS['remove']: monitor_remove_button_handler
}
