from typing import List
import logging

from aiogram.dispatcher import FSMContext

from bot.exceptions import ServiceOperationFailedError, DataNotFoundError
from bot.database import product_gateway
from bot.utils.common import find_items
from bot.entities import Product
from bot.scraper import Scraper


def find_all_from_monitoring_list(user_id: int) -> List[Product]:
    return product_gateway.find_all_from_monitoring_list(user_id)


async def get_info(state: FSMContext) -> List[Product]:
    async with state.proxy() as data:
        products = data['products']
        checked_products = data['checked_products']

    product_dicts = find_items(
        lambda product: product['id'] in checked_products, products
    )

    product_options = product_gateway.find_options_by_ids(checked_products)

    if not product_options:
        raise DataNotFoundError(
            f'Cannot find products options with ids={checked_products}'
        )

    products = []
    for product_dict in product_dicts:
        id = product_dict['id']
        product_dict['product_options'] = product_options[id]
        products.append(Product._make(product_dict.values()))

    return products


async def add(product_url: str, user_id: int) -> None:
    # Check if someone already add product to his list
    product = product_gateway.find_by_url(product_url)

    if not product:
        # Scraping product from website and then adding
        scraper = Scraper(product_url)
        product = await scraper.scrape_product()
        product_gateway.add(user_id, product)
        return

    # Trying to add link to existing product
    product_gateway.add_to_monitoring_list(user_id, product.id)


async def remove_from_monitoring_list_by_ids(user_id: int, state: FSMContext) -> None:
    async with state.proxy() as data:
        product_ids = data.get('checked_products')
        if not product_ids:
            logging.info('No products selected to remove')
            return

    result = product_gateway.remove_from_monitoring_list_by_ids(
        user_id, product_ids
    )
    if not result:
        raise ServiceOperationFailedError

    logging.info((
        f'Products of user {user_id} '
        f'with ids {product_ids} removed successfully'
    ))


async def add_to_checked_ids(id: int, state: FSMContext) -> None:
    """Add id to checked_ids or remove if already exist."""
    async with state.proxy() as data:
        checked_ids = data.get('checked_products')
        if not checked_ids:
            data['checked_products'] = [id]
            return

        if id in checked_ids:
            checked_ids.remove(id)
        else:
            checked_ids.append(id)
    