from bot.tests.mock_db import MockDb # must be imported before tested functions
from bot.database.user_gateway import save
from bot.entities import User


class TestDbUsers(MockDb):

    def test_add_user(self):
        """Tests add_user function"""
        user = User(123, 'johndoe', 'John', 'Doe')
        with self.mock_db_config:
            self.assertTrue(save(user))
