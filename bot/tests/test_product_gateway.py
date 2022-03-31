from bot.tests.mock_db import MockDb # must be imported before tested functions
from bot.database.product_gateway import add, find_by_url
from bot.database.user_gateway import save # need to add user before connecting him with product
from bot.entities import Product, ProductOption, User


class TestDbProducts(MockDb):

    def setUp(self) -> None:
        options = [
            ProductOption(None, 'In stock', '300g', 100),
            ProductOption(None, 'In stock', '500g', 180),
            ProductOption(None, 'Out of stock', '800g', 260)
        ]

        self.product = Product(
            None, 'Adaptil', 'Description', 'cat.png', 'Title',
            'Cat Food', 3.43, 7, 'https://www.cat.com', options
        )
        self.user = User(1, 'jackdoe', 'Jack', 'Doe')

    def test_add_product(self):
        """Tests add_product function"""
        with self.mock_db_config:
            # firt test add_user in test_db_users than assume that add_user works correctly
            save(self.user)
            self.assertTrue(add(self.user.id, self.product))

    def test_find_product_by_url(self):
        """Tests find_products_by_url function"""
        def get_options_without_id(options):
            return [[*opt][1:] for opt in options]

        with self.mock_db_config:
            product = find_by_url(self.product.url)
            self.assertIsInstance(product, Product)
            self.assertEqual([*product][1:-1], [*self.product][1:-1])

            product = find_by_url(
                self.product.url, with_product_options=True
            )
            self.assertIsInstance(product, Product)
            test_options = get_options_without_id(self.product.product_options)
            found_options = get_options_without_id(product.product_options)
            self.assertEqual(test_options, found_options)