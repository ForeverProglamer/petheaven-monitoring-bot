from datetime import datetime, timedelta
from random import uniform
from typing import List
import logging
import asyncio

from aiohttp import ClientSession
from aiogram import Bot

from bot.views.product_notification import render_notification_message
from bot.utils.common import find_items
from bot.utils.util import choose_notifications
from bot.exceptions import ProductNotFoundError
from bot.entities import Product, Notification
from bot.database import product_gateway
from bot.scraper import Scraper, HEADERS


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s  %(module)s  %(name)s  %(message)s'
)

MAX_SECONDS_DELAY = 5
MIN_SECONDS_DELAY = 2
DELTA = timedelta(hours=12)


async def monitor_products(bot: Bot) -> None:
    """Task for monitoring products and updating their info."""
    while True:
        start_time = datetime.now()
        logging.info('Start monitoring products...')

        products = product_gateway.get_all_products()
        monitoring_list = product_gateway.get_all_from_monitoring_list()
        scraped_products = await _scrape_products([p.url for p in products])
        scraped_products = list(filter(lambda p: p, scraped_products))

        notifications = _create_notifications(
            bot, products, scraped_products, monitoring_list
        )

        await _send_notifications(notifications)
        _update_products(products, scraped_products)

        logging.info(f'{len(products) = }')
        logging.info(f'{len(scraped_products) = }')
        logging.info(f'{len(notifications) = }')

        logging.info(
            f'Time elapsed: {(datetime.now()-start_time).total_seconds()} sec'
        )

        logging.info(f'Monitoring task scheduled to {datetime.now() + DELTA}')
        await asyncio.sleep(DELTA.total_seconds())


async def _scrape_products(urls: List[str]) -> List[Product]:
    async def scrape_product(url: str, session: ClientSession) -> Product:
        scraper = Scraper(url, session)
        try:
            return await scraper.scrape_product()
        except ProductNotFoundError as e:
            # todo delete such products from storage and notify users
            logging.exception(e)

    async with ClientSession(headers=HEADERS) as session:
        return await asyncio.gather(
            *(scrape_product(url, session) for url in urls)
        )


def _create_notifications(bot: Bot, old_products: List[Product], scraped_products: List[Product],
                          monitoring_list: List[List]) -> List[Notification]:
    notifications = []
    for old in old_products:
        for scraped in scraped_products:
            if old == scraped and old.are_product_options_changed(scraped):
                message = render_notification_message(
                    scraped, old
                )
                user_ids = _find_user_ids(old.id, monitoring_list)
                notifications.extend(
                    [Notification(id_, bot, message) for id_ in user_ids]
                )
    return notifications


def _find_user_ids(product_id: int, monitoring_list: List[List]) -> List[int]:
    return [
        el[0]
        for el in find_items(
            lambda item: item[1] == product_id,
            monitoring_list
        )
    ]


async def _send_notifications(notifications: List[Notification]) -> None:
    notifications_set = set(notifications)
    while notifications_set:
        notifications_to_send = choose_notifications(notifications_set)
        await asyncio.gather(*(n.send() for n in notifications_to_send))

        notifications_set = notifications_set.difference(
            notifications_to_send
        )

        await asyncio.sleep(uniform(MIN_SECONDS_DELAY, MAX_SECONDS_DELAY))


def _update_products(old_products: List[Product], scraped_products: List[Product]) -> None:
    new_products = []
    outdated_product_options_ids = []
    for old in old_products:
        for scraped in scraped_products:
            if old == scraped and old.are_product_options_changed(scraped):
                new_products.append(old.update_with(scraped))

                outdated_product_options_ids.extend(
                    old.get_outdated_product_options_ids(scraped)
                )

    product_gateway.update_products(new_products)
    product_gateway.remove_product_options_by_id(outdated_product_options_ids)
