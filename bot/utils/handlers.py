from typing import Dict, List

from aiogram.dispatcher.storage import FSMContext
from aiogram.types import Message

from .render import get_keyboard_for_page, create_pages_from_products
from bot.states import MonitorProducts
from .common import MESSAGES, BUTTONS


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