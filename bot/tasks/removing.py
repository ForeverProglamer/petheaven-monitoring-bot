from typing import List
import asyncio
import logging

from aiogram import Bot

from bot.views.product_notification import render_unavailable_product
from bot.entities import Product, Notification
from bot.database import product_gateway
from bot.utils.common import find_items


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s  %(module)s  %(name)s  %(message)s'
)


async def remove_unavailable_products(bot: Bot,
                                      unavailable_product_urls: List[str],
                                      products: List[Product],
                                      monitoring_list: List[List]) -> None:
    """
    Task for removing unavailable products and
    notifying users that monitor such products.
    """
    unavailable_products = find_items(
        lambda p: p.url in unavailable_product_urls, products
    )
    notifications = _create_notifications(
        bot, unavailable_products, monitoring_list
    )
    await _send_notifications(notifications)

    logging.info(f'{len(notifications) = }')

    product_gateway.remove_by_ids([p.id for p in unavailable_products])
    logging.info('Unavailable products are removed successfully')


async def _send_notifications(notifications: List[Notification]) -> None:
    await asyncio.gather(*(n.send() for n in notifications))


def _create_notifications(bot: Bot, products: List[Product],
                          monitoring_list: List[List]) -> List[Notification]:
    notifications = []
    for product in products:
        receivers_ids = _find_receivers_ids(product.id, monitoring_list)
        message = render_unavailable_product(product)
        notifications.extend(
            [Notification(id, bot, message) for id in receivers_ids]
        )
    return notifications


def _find_receivers_ids(product_id: int, monitoring_list: List[List]) -> List[int]:
    result = find_items(lambda item: item[1] == product_id, monitoring_list)
    return [item[0] for item in result]
