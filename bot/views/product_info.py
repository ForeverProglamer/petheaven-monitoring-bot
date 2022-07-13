from typing import Callable, List
from decimal import Decimal

from bot.entities import Product, ProductOption


def render_product_list(products: List[Product]) -> str:
    """Renders name and url of each product in list."""
    return ''.join([
        f'<b>{i}.</b> <a href="{p.url}">{p.title}</a>\n'
        for i, p in enumerate(products, 1)
    ])


def render_product(product: Product) -> str:
    """High-level api for rendering product."""
    return (
        f'{render_descriptive_info(product)}'
        f'{render_product_options(product.product_options)}'
    )


def render_descriptive_info(product: Product) -> str:
    """Renders all product fields except of product options."""
    return (
        f'<a href="{product.url}"><b>{product.title}</b></a>\n'
        f'<b>Brand:</b> {product.brand}\n'
        f'<b>Product type:</b> {product.product_type}\n'
        f'<b>Rating:</b> {product.rating} / 5.0\n'
        f'<b>Reviews:</b> {product.reviews}\n'
        f'<b>Description:</b> {product.description}\n\n'
    )


def render_product_options(product_options: ProductOption) -> str:
    """Renders product options with standard renderer."""
    render_product_option = product_option_renderer_factory(
        standard_title_renderer
    )
    return "".join(map(render_product_option, product_options))


def product_option_renderer_factory(title_renderer: Callable[[str], str]) -> str:
    """Produces renderers for product option."""
    def render(option: ProductOption) -> str:
        """Renders single product options."""
        return (
            f'{title_renderer(option.title)}'
            f'{standard_price_renderer(option.price)}'
            f'{standard_availability_renderer(option.availability)}'
            '\n'
        )
    return render


def standard_title_renderer(title: str) -> str:
    """Standard renderer for title."""
    return f'<b>Option:</b> {title}\n'


def standard_price_renderer(price: Decimal) -> str:
    """Standard renderer for price."""
    return f'💰<b>Price:</b> R{price:.2f}\n'


def standard_availability_renderer(availability: str) -> str:
    """Standard renderer for availability."""
    return f'📦<b>Availability:</b> {availability}\n'
