import asyncio
import logging
import os
from typing import Dict

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import (
    CallbackQuery,
    ContentType,
    Message,
    ParseMode,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from dotenv import load_dotenv
load_dotenv()

from bot.exceptions import (
    ServiceOperationFailedError,
    DataAlreadyExistsInDBError,
    CantSaveToDBError,
    DataNotFoundError
)
from bot.services import user_service, product_service
from bot.states import MonitorProducts
from bot.tasks.monitoring import monitor_products
from bot.utils.common import MESSAGES, BUTTONS
from bot.utils.handlers import (
    monitor_menu_handlers,
    get_pages,
    send_products_info,
    get_ui_for_monitor_command
)
from bot.utils.keyboard import (
    get_keyboard_for_page,
    select_cb,
    navigation_cb,
    confirm_cb
)


logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('TOKEN')

bot = Bot(token=TOKEN)
storage = RedisStorage2()
dp = Dispatcher(bot, storage=storage)

monitor_menu_buttons = (*BUTTONS.values(),)


@dp.message_handler(commands='start', state='*')
async def cmd_start(message: Message):
    user = message.from_user
    try:
        user_service.save(
            user.id, user.username, user.first_name, user.last_name
        )
    except CantSaveToDBError as e:
        logging.error(e)
        await message.answer(MESSAGES['start_error'])
    else:
        bot_info = await bot.get_me()
        await message.answer(MESSAGES['start'].format(bot_info.first_name))


@dp.message_handler(commands='monitor', state='*')
async def cmd_monitor(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    products = product_service.find_all_from_monitoring_list(
        message.from_user.id
    )

    answer_text, buttons = get_ui_for_monitor_command(products)
    if products:
        await state.update_data(products=[p._asdict() for p in products])

    markup.add(*buttons)
    await message.answer(
        answer_text, reply_markup=markup,
        parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )
    await MonitorProducts.on_monitor_cmd.set()


@dp.message_handler(lambda m: m.text in monitor_menu_buttons, state=MonitorProducts.on_monitor_cmd)
async def monitor_menu_handler(message: Message, state: FSMContext):
    text = message.text
    handler = monitor_menu_handlers[text]
    await handler(message, state)


@dp.callback_query_handler(select_cb.filter(), state='*')
async def callback_select(call: CallbackQuery, callback_data: Dict, state: FSMContext):
    product_id = int(callback_data['product_id'])
    await product_service.add_to_checked_ids(product_id, state)

    async with state.proxy() as data:
        current_page = data['current_page']
        checked_ids = data['checked_products']

    pages = await get_pages(state)
    await call.message.edit_reply_markup(
        get_keyboard_for_page(pages, current_page, checked_ids)
    )
    await call.answer()


@dp.callback_query_handler(confirm_cb.filter(), state=MonitorProducts.on_getting_product_info)
async def info_callback_confirm(call: CallbackQuery, callback_data: Dict, state: FSMContext):
    try:
        products = await product_service.get_info(state)
    except DataNotFoundError as e:
        logging.exception(e)
        await call.message.answer(MESSAGES['info_error'])
    else:
        await call.message.edit_reply_markup()
        await send_products_info(call, products)
    finally:
        await state.update_data(checked_products=[])
        await state.reset_state(with_data=False)
        await call.answer()


@dp.callback_query_handler(navigation_cb.filter(), state='*')
async def callback_navigation(call: CallbackQuery, callback_data: Dict, state: FSMContext):
    # Handles both forward and back buttons
    page_num = int(callback_data['page_num'])
    pages = await get_pages(state)

    async with state.proxy() as data:
        data['current_page'] = page_num
        checked_ids = data['checked_products']

    await call.message.edit_reply_markup(
        get_keyboard_for_page(pages, page_num, checked_ids)
    )
    await call.answer()


@dp.message_handler(content_types=[ContentType.TEXT], state=MonitorProducts.on_adding_product)
async def add_product(message: Message, state: FSMContext):
    await message.answer(MESSAGES['add_wait'])
    url = message.text
    user_id = message.from_user.id

    try:
        await product_service.add(url, user_id)
    except DataAlreadyExistsInDBError:
        return await message.answer(MESSAGES['add_same_product'])
    except Exception as e:
        logging.exception(e)
        return await message.answer(MESSAGES['add_error'])

    await message.answer(
        MESSAGES['add_success'], reply_markup=ReplyKeyboardRemove()
    )
    await state.reset_state(with_data=False)


@dp.callback_query_handler(confirm_cb.filter(), state=MonitorProducts.on_removing_product)
async def remove_callback_confirm(call: CallbackQuery, callback_data: Dict, state: FSMContext):
    try:
        await product_service.remove_from_monitoring_list_by_ids(
            call.from_user.id, state
        )
    except ServiceOperationFailedError:
        await call.message.answer(MESSAGES['remove_error'])
    else:
        await call.message.edit_reply_markup()
        await call.message.answer(MESSAGES['remove_success'])
    finally:
        await state.update_data(checked_products=[])
        await state.reset_state(with_data=False)
        await call.answer()


async def startup(dp: Dispatcher):
    asyncio.create_task(monitor_products(dp.bot))


async def shutdown(dp: Dispatcher):
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(
        dp, skip_updates=True, on_startup=startup, on_shutdown=shutdown
    )
