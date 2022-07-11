from typing import Dict, List, Tuple, Union
import logging

from mysql.connector import connect, Error, errorcode

from bot.exceptions import DataAlreadyExistsInDBError, DataNotFoundError
from bot.entities import Product, ProductOption
from bot.utils.util import to_products, group_product_options_by_ids
from .config import db_config


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s  %(module)s  %(name)s  %(message)s'
)

ADD_PRODUCT_QUERY = """
    INSERT INTO products 
    (brand, description_, img, title, product_type, rating, reviews, url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

ADD_PRODUCT_OPTION_QUERY = """
    INSERT INTO product_options
    (availability, title, price, product_id)
    VALUES (%s, %s, %s, %s)
"""

LINK_PRODUCT_WITH_USER_QUERY = """
    INSERT INTO monitoring_list (user_id , product_id)
    VALUES (%s, %s)
"""

FIND_PRODUCT_BY_URL_QUERY = """
    SELECT * FROM products WHERE url = %s
"""

FIND_PRODUCT_OPTIONS_BY_ID_QUERY = """
    SELECT id, availability, title, price 
    FROM product_options 
    WHERE product_id = %s
"""

FIND_PRODUCT_OPTIONS_BY_IDS_QUERY = """
    SELECT id, availability, title, price, product_id
    FROM product_options
    WHERE product_id IN ({})
    ORDER BY product_id
"""

FIND_FAVOURITE_PRODUCTS_QUERY = """
    SELECT p.* FROM monitoring_list m
    JOIN products p ON m.product_id = p.id
    WHERE m.user_id = %s
"""

REMOVE_PRODUCT_BY_ID_QUERY = """
    DELETE FROM products
    WHERE id = %s
"""

REMOVE_PRODUCTS_BY_IDS_QUERY = """
    DELETE FROM monitoring_list
    WHERE user_id = %s
    AND product_id = %s
"""

GET_ALL_PRODUCTS_QUERY = """
    SELECT * FROM products
    ORDER BY id
"""

GET_ALL_PRODUCTS_WITH_OPTIONS_QUERY = """
    SELECT p.*, po.id, po.availability, po.title, po.price
    FROM products AS p
    JOIN product_options AS po ON p.id = po.product_id
    ORDER BY p.id, po.id
"""

GET_ALL_FROM_MONITORING_LIST_QUERY = """
    SELECT * FROM monitoring_list
"""

UPDATE_PRODUCTS_QUERY = """
    INSERT INTO products
        (id, brand, description_, img, title, product_type, rating, reviews, url)
    VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        brand = VALUES(brand),
        description_ = VALUES(description_),
        img = VALUES(img),
        title = VALUES(title),
        product_type = VALUES(product_type),
        rating = VALUES(rating),
        reviews = VALUES(reviews),
        url = VALUES(url)
"""

UPDATE_PRODUCT_OPTIONS_QUERY = """
    INSERT INTO product_options
        (id, availability, title, price, product_id)
    VALUES
        (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        availability = VALUES(availability),
        title = VALUES(title),
        price = VALUES(price)
"""

REMOVE_PRODUCT_OPTIONS_QUERY = """
    DELETE FROM product_options
    WHERE id = %s
"""


def add(user_id: int, product: Product) -> int:
    """
    Insert product and product options to appropriate tables
    and add product to user's monitoring list.
    """
    def prepare_data(product_id: int, product_options: List[ProductOption]) -> Tuple[Tuple]:
        return tuple(map(
            lambda p: (*(*p,)[1:], product_id),
            product_options
        ))

    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(ADD_PRODUCT_QUERY, (*product,)[1:-1])
                product_id = cursor.lastrowid
                cursor.executemany(
                    ADD_PRODUCT_OPTION_QUERY,
                    prepare_data(product_id, product.product_options)
                )
                connection.commit()
        add_to_monitoring_list(user_id, product_id)
        return True
    except Error as e:
        logging.exception(f'Failed to add product: {e}')
        return False


def add_to_monitoring_list(user_id: int, product_id: int) -> bool:
    """
    Create connection between user and product in monitoring_list
    by user_id and product_id.
    """
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    LINK_PRODUCT_WITH_USER_QUERY, (user_id, product_id)
                )
                connection.commit()
                return True
    except Error as e:
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise DataAlreadyExistsInDBError(e)
        logging.exception(f'Failed to add product to monitoring list: {e}')
        return False


def find_by_url(url: str, with_product_options: bool = False) -> Union[Product, None]:
    """Find first product by given url"""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(FIND_PRODUCT_BY_URL_QUERY, (url,))
                data = cursor.fetchone()

                if not data:
                    raise DataNotFoundError(f'No product found with url={url}')

                product_options = None
                if with_product_options:
                    product_options = find_options_by_id(data[0])

                return Product._make((*data, product_options))
    except Error as e:
        logging.exception(f'Failed to find product by url={url}: {e}')
        return None


def find_options_by_id(product_id: int) -> Union[List[ProductOption], List]:
    """Find product options by product_id."""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    FIND_PRODUCT_OPTIONS_BY_ID_QUERY, (product_id,)
                )
                data = cursor.fetchall()

                if not data:
                    raise DataNotFoundError(
                        f'No product options found for product with id={product_id}'
                    )

                product_options = [
                    ProductOption._make(item) for item in data
                ]

                return product_options
    except Error as e:
        logging.exception(
            f'Failed to find product options by id={product_id}: {e}')
        return []


def find_options_by_ids(product_ids: List[int]) -> Dict[int, List[ProductOption]]:
    """Finds product options within product_ids list."""
    if not product_ids:
        return {}

    query = FIND_PRODUCT_OPTIONS_BY_IDS_QUERY.format(
        ', '.join(['%s' for _ in range(len(product_ids))])
    )

    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, product_ids)
                data = cursor.fetchall()
                if not data:
                    return {}
                return group_product_options_by_ids(product_ids, data)
    except Error as e:
        logging.exception(
            f'Failed to find product options by ids={product_ids}: {e}'
        )
        return {}


def find_all_from_monitoring_list(user_id: int) -> Tuple[Product]:
    """Find products from user's monitoring list."""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(FIND_FAVOURITE_PRODUCTS_QUERY, (user_id,))
                data = cursor.fetchall()

                if not data:
                    raise DataNotFoundError(
                        f'No products found in monitoring list of user with id={user_id}'
                    )

                return tuple(Product._make((*item, None)) for item in data)
    except Error as e:
        logging.exception(f'Failed to find favourite products: {e}')


def remove_by_ids(product_ids: List[int]) -> bool:
    """Removes products with given ids."""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    REMOVE_PRODUCT_BY_ID_QUERY, [(id,) for id in product_ids]
                )
                connection.commit()
                return True
    except Error as e:
        logging.exception(
            f'Failed to remove products by ids={product_ids}: {e}'
        )
        return False


def remove_from_monitoring_list_by_ids(user_id: int, product_ids: List[int]) -> bool:
    """Removes products from user's monitoring list."""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    REMOVE_PRODUCTS_BY_IDS_QUERY,
                    [(user_id, id) for id in product_ids]
                )
                connection.commit()
                return True
    except Error as e:
        logging.exception((
            f'Failed to remove products of user {user_id} '
            f'with ids {product_ids}: {e}'
        ))
        return False


def get_all_products(with_options: bool = True) -> List[Product]:
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                if with_options:
                    cursor.execute(GET_ALL_PRODUCTS_WITH_OPTIONS_QUERY)
                    data = cursor.fetchall()
                    return to_products(data)
                else:
                    cursor.execute(GET_ALL_PRODUCTS_QUERY)
                    data = cursor.fetchall()
                    return [Product._make(*item, None) for item in data]
    except Error as e:
        logging.exception(f'Failed to get all products: {e}')
        return []


def get_all_from_monitoring_list() -> List[List]:
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(GET_ALL_FROM_MONITORING_LIST_QUERY)
                return cursor.fetchall()
    except Error as e:
        logging.exception(f'Failed to get all from monitoring list: {e}')
        return []


def update_products(products: List[Product]) -> bool:
    products_data = [(*p,)[:-1] for p in products]
    product_options_data = [
        (*opt, p.id) for p in products for opt in p.product_options
    ]
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    UPDATE_PRODUCTS_QUERY, products_data
                )
                cursor.executemany(
                    UPDATE_PRODUCT_OPTIONS_QUERY, product_options_data
                )
                connection.commit()
                return True
    except Error as e:
        logging.exception(f'Failed to update products: {e}')
        return False


def remove_product_options_by_id(ids: List[int]) -> bool:
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    REMOVE_PRODUCT_OPTIONS_QUERY,
                    [(id_,) for id_ in ids]
                )
                connection.commit()
                return True
    except Error as e:
        logging.exception(
            f'Failed to remove product options by ids={ids}: {e}')
        return False
