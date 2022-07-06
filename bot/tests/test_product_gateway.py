from bot.tests.mock_db import MockDb # must be imported before tested functions
from bot.database.product_gateway import add, find_by_url, update_products, remove_product_options_by_id
from bot.database.user_gateway import save # need to add user before connecting him with product
from bot.entities import Product, ProductOption, User
from copy import deepcopy


class TestDbProducts(MockDb):

    def setUp(self) -> None:
        self.options = [
            ProductOption(None, 'In stock', '300g', 100),
            ProductOption(None, 'In stock', '500g', 180),
            ProductOption(None, 'Out of stock', '800g', 260)
        ]

        self.options2 = [
            ProductOption(None, 'Out of stock', '100g', 100),
            ProductOption(None, 'In stock', '200g', 200),
            ProductOption(None, 'Low stock', '300g', 300),
            ProductOption(None, 'Out of stock', '400g', 400),
        ]

        self.product = Product(
            None, 'Adaptil', 'Description', 'cat.png', 'Title',
            'Cat Food', 3.43, 7, 'https://www.cat.com', self.options
        )

        self.product2 = Product(
            None, 'Some brand', 'Some descr', 'https://www.dummy.com/img.jpeg', 'Some title',
            'Dog food', 4.2, 2, 'https://www.dummy.com', self.options2
        )

        self.product_id = 1
        self.product2_id = 2
        self.product_options_ids = [1, 2, 3]
        self.product_options2_ids = [4, 5, 6, 7]

        self.user = User(1, 'jackdoe', 'Jack', 'Doe')
        

    def test_add_product(self):
        """Tests add_product function"""
        with self.mock_db_config:
            # first test add_user in test_db_users than assume that add_user works correctly
            save(self.user)
            self.product_id = add(self.user.id, self.product)
            self.product2_id = add(self.user.id, self.product2)
            self.assertTrue(self.product_id)
            self.assertTrue(self.product2_id)

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

    def test_update_products(self):
        """Tests update_products function"""
        opt1 = deepcopy(self.options)
        opt1[0] = opt1[0]._replace(id=self.product_options_ids[0], price=50)
        opt1[1] = opt1[1]._replace(id=self.product_options_ids[1], title='Bruhhh', price=123)
        opt1[2] = opt1[2]._replace(id=self.product_options_ids[2], price=456)
        opt1.append(ProductOption(None, 'In stock', '1100g', 320))

        opt2 = deepcopy(self.options2)
        opt2[0] = opt2[0]._replace(id=self.product_options2_ids[0], price=40)
        opt2[1] = opt2[1]._replace(id=self.product_options2_ids[1], title='Gang bang', price=80)
        opt2[2] = opt2[2]._replace(id=self.product_options2_ids[2], title='Jabroni', price=120)
        opt2[3] = opt2[3]._replace(id=self.product_options2_ids[3], price=160)

        p1 = self.product._replace(id=self.product_id, title='New Title', rating=3.01, product_options=opt1)

        p2 = self.product2._replace(id=self.product2_id, title='Some NEW title', rating=4.5, reviews=4, product_options=opt2)
        
        new_products = [p1, p2]
        
        with self.mock_db_config:
            self.assertTrue(update_products(new_products))

    def test_remove_product_options_by_id(self):
        """Tests remove_product_options_by_id function"""
        with self.mock_db_config:
            self.assertTrue(remove_product_options_by_id([1]))
