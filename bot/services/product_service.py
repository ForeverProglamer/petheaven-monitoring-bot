from cgitb import reset
from typing import Tuple
import logging

from aiogram.dispatcher import FSMContext

from bot.exceptions import ServiceOperationFailedError, DataNotFoundError
from bot.database import product_gateway
from bot.utils.common import find_item
from bot.entities import Product
from bot.scraper import Scraper


def find_all_from_monitoring_list(user_id: int) -> Tuple[Product]:
    return product_gateway.find_all_from_monitoring_list(user_id)


async def get_info(product_id: int, state: FSMContext) -> Product:
    async with state.proxy() as data:
        products = data['products']

    product_dict = find_item(lambda p: p['id'] == product_id, products)
    if not product_dict:
        raise DataNotFoundError(
            f'Cannot find product with id={product_id} in cache'
        )
    product_options = product_gateway.find_options_by_id(product_id)
    product_dict['product_options'] = product_options
    return Product._make(product_dict.values())


async def add(product_url: str, user_id: int) -> None:
    try:
        # Check if someone already add product to his list
        product = product_gateway.find_by_url(product_url)
    except DataNotFoundError:
        # Scraping product from website and then adding
        scraper = Scraper(product_url)
        product = await scraper.scrape_product()
        product_gateway.add(user_id, product)
    else:
        # Trying to add link to existing product
        product_gateway.add_to_monitoring_list(user_id, product.id)


def remove_by_id(product_id: int) -> None:
    result = product_gateway.remove_by_id(product_id)
    if not result:
        raise ServiceOperationFailedError

    logging.info(f'Product with id={product_id} removed successfully')
