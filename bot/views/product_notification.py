from decimal import Decimal
from typing import List

from bot.entities import Product, ProductOption, ProductDifference
from .product_info import product_option_renderer_factory
from bot.utils.common import find_items


def render_notification_message(new: Product, old: Product) -> str:
    """High-level api for rendering notification's message."""
    message = _render_notification_title(new)
    message += _render_options_updates(
        new.product_options, old.product_options
    )
    message += _render_options_changes(
        new.product_options, old.product_options
    )
    return message


def render_unavailable_product(product: Product) -> str:
    """Renders information about unavailable product."""
    message = _render_notification_title(product)
    message += '❗️Product was removed, it is no more available on website.'
    return message


def _render_notification_title(product: Product) -> str:
    return f'📬<a href="{product.url}"><b>{product.title}</b></a>\n\n'


def _render_options_updates(new_options: List[ProductOption],
                            old_options: List[ProductOption]) -> str:
    """
    Renders information about appearing of new options or
    disappearing of old ones.
    """
    if len(new_options) > len(old_options):
        new_opts = _get_options_difference(new_options, old_options)
        return ''.join(map(new_option_renderer, new_opts))
    elif len(new_options) < len(old_options):
        removed_opts = _get_options_difference(old_options, new_options)
        return ''.join(map(removed_option_renderer, removed_opts))
    return ''


def _render_options_changes(new_options: List[ProductOption],
                            old_options: List[ProductOption]) -> str:
    """Renders price and availability changes of product options."""
    result = ''
    for old_option in old_options:
        for new_option in new_options:
            if old_option.title == new_option.title:
                difference = old_option.get_difference(new_option)
                result += difference_renderers[difference](
                    new_option, old_option
                )
    return result


def render_price_change(new_option: ProductOption, old_option: ProductOption) -> str:
    change_text, change_emoji = _price_change_text(
        new_option.price, old_option.price
    )
    return (
        f'<b>Price {change_text} for option '
        f'{new_option.title}</b>\n{change_emoji}'
        f'{price_changed_renderer(new_option.price, old_option.price)}\n'
    )


def render_availability_change(new_option: ProductOption, old_option: ProductOption) -> str:
    availability_text = availability_changed_renderer(
        new_option.availability, old_option.availability
    )
    return (
        f'<b>Availability changed for option {new_option.title}</b>\n'
        f'{availability_text}\n'
    )


def render_availability_and_price_change(new_option: ProductOption,
                                         old_option: ProductOption) -> str:
    change_text, change_emoji = _price_change_text(
        new_option.price, old_option.price
    )
    availability_text = availability_changed_renderer(
        new_option.availability, old_option.availability
    )
    return (
        f'<b>Availability changed and price {change_text} for '
        f'option {new_option.title}</b>\n'
        f'{availability_text}{change_emoji}'
        f'{price_changed_renderer(new_option.price, old_option.price)}\n'
    )


def _get_options_difference(bigger: List[ProductOption],
                            smaller: List[ProductOption]) -> List[ProductOption]:
    title_diff = set([opt.title for opt in bigger]).\
        difference(set([opt.title for opt in smaller]))
    return find_items(lambda opt: opt.title in title_diff, bigger)


def new_option_renderer(option: ProductOption) -> str:
    return product_option_renderer_factory(new_title_renderer)(option)


def removed_option_renderer(option: ProductOption) -> str:
    return product_option_renderer_factory(removed_title_renderer)(option)


def new_title_renderer(title: str) -> str:
    return f'➕<b>New option {title}</b>\n'


def removed_title_renderer(title: str) -> str:
    return f'➖<b>{title} option was removed</b>\n'


def price_changed_renderer(new_price: Decimal, old_price: Decimal) -> str:
    return f'<b>Price:</b> <s>R{old_price:.2f}</s> R{new_price:.2f}\n'


def availability_changed_renderer(new_availability: str, old_availability: str) -> str:
    return (
        f'📦<b>Availability:</b> <s>{old_availability}</s> '
        f'{new_availability}\n'
    )


def _price_change_text(new_price: Decimal, old_price: Decimal) -> tuple[str, str]:
    if new_price > old_price:
        return ('increased', '📈')
    return ('decreased', '📉')


difference_renderers = {
    ProductDifference(False, False): lambda new_option, old_option: '',
    ProductDifference(False, True): render_price_change,
    ProductDifference(True, False): render_availability_change,
    ProductDifference(True, True): render_availability_and_price_change
}
