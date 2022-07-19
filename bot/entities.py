from __future__ import annotations
from decimal import Decimal
import logging
from typing import NamedTuple, List, Tuple

from aiogram import Bot, types
from aiogram.utils.exceptions import BotBlocked


class User(NamedTuple):
    id: int
    username: str
    first_name: str
    last_name: str


# todo consider using dataclass decorator instead of extending NamedTuple
class ProductOption(NamedTuple):
    id: int
    availability: str
    title: str
    price: Decimal

    def __eq__(self, other: ProductOption) -> bool:
        return (
            self.availability == other.availability and
            self.title == other.title and
            self.price == other.price
        )

    def __hash__(self) -> int:
        return hash(self.title) + hash(self.availability) + hash(self.price)

    def get_difference(self, other: ProductOption) -> ProductDifference:
        """
        Returns difference of availability and price
        of two versions of product option.
        """
        return ProductDifference(
            availability_changed=self.availability != other.availability,
            price_changed=self.price != other.price
        )

    def to_tuple(self, with_id: bool = False) -> Tuple:
        """Converts an object to tuple of it's values."""
        fields = self._fields
        dict_ = self._asdict()
        if not with_id:
            fields = fields[1:]
        return tuple(dict_[f] for f in fields)


# todo consider using dataclass decorator instead of extending NamedTuple
class Product(NamedTuple):
    id: int
    brand: str
    description: str
    img: str
    title: str
    product_type: str
    rating: float
    reviews: int
    url: str
    product_options: List[ProductOption]

    def __eq__(self, other: Product) -> bool:
        return self.url == other.url

    def update_with(self, other: Product) -> Product:
        """
        Returns new version of product updated with scraped product's data.
        """
        product_options = []
        for old_opt in self.product_options:
            for scraped_opt in other.product_options:
                if old_opt.title == scraped_opt.title:
                    product_options.append(
                        scraped_opt._replace(id=old_opt.id)
                    )

        return other._replace(id=self.id, product_options=product_options)

    def get_outdated_product_options_ids(self, other: Product) -> List[int]:
        """
        Returns ids of product options, which
        no more present in new version of product.
        """
        if len(self.product_options) > len(other.product_options):
            ids = list(map(
                lambda opt: opt.id,
                set(self.product_options).difference(other.product_options)
            ))
            return ids
        return []

    def are_product_options_changed(self, other: Product) -> bool:
        """
        Returns False, if old product options and
        new product options are equal. Otherwise return True.
        """
        diff = set(self.product_options).difference(other.product_options)
        len_is_equal = len(self.product_options) != len(other.product_options)
        return bool(diff) or len_is_equal

    def to_storage_structure(self) -> Tuple:
        """
        Converts product to structure
        that can be saved in storage.
        """
        fields = self._fields
        dict_ = self._asdict()
        return tuple(dict_[f] for f in fields[1:-1])

    def options_to_storage_structure(self, product_id: int) -> List[Tuple]:
        """
        Converts product options to structure
        that can be saved in storage.
        """
        return [(*opt.to_tuple(), product_id) for opt in self.product_options]


class ProductDifference(NamedTuple):
    availability_changed: bool
    price_changed: bool


class Notification(NamedTuple):
    receiver_id: int
    sender: Bot
    message: str

    def __eq__(self, other: Notification) -> bool:
        return (
            self.receiver_id == other.receiver_id and
            self.message == other.message
        )

    def __hash__(self) -> int:
        return hash(self.receiver_id) + hash(self.message)

    async def send(self) -> None:
        """Sends message from bot to user."""
        try:
            await self.sender.send_message(
                self.receiver_id,
                self.message,
                parse_mode=types.ParseMode.HTML,
                disable_web_page_preview=True
            )
        except BotBlocked as e:
            # todo consider doing something with users that blocked the bot
            logging.error(
                f'Bot was blocked by {self.receiver_id}: {e}'
            )
