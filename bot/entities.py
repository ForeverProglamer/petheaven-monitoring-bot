from typing import NamedTuple, List


class User(NamedTuple):
    id: int
    username: str
    first_name: str
    last_name: str


class ProductOption(NamedTuple):
    id: int
    availability: str
    title: str
    price: int


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
