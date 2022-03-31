from aiogram.dispatcher.filters.state import State, StatesGroup


class MonitorProducts(StatesGroup):
    on_monitor_cmd = State()
    on_getting_product_info = State()
    on_adding_product = State()
    on_removing_product = State()