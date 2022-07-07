from unittest.mock import patch
import subprocess
import unittest
import os

from mysql.connector import connect, Error
from dotenv import load_dotenv


ENV_FILE = '.env'
SQL_FOLDER = 'sql'
CREATEDB_FILE = 'createdb.sql'

path = os.path.join(os.getcwd(), ENV_FILE)
if not os.path.exists(path):
    raise FileNotFoundError(f'Failed to find {ENV_FILE} file with path: {path}')

load_dotenv(path)
from bot.database.config import db_config

TEST_DB_NAME = os.getenv('TEST_DB_NAME')


class MockDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._config = db_config.copy()
        del cls._config['database']

        cls._create_db()
        cls._create_db_structure()

        new_config = db_config.copy()
        new_config['database'] = TEST_DB_NAME
        cls.mock_db_config = patch.dict(db_config, new_config)

    # def test_method(self):
    #     self.assertEqual(1, 1)

    @classmethod
    def _create_db(cls):
        try:
            with connect(**cls._config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f'CREATE DATABASE {os.getenv("TEST_DB_NAME")}'
                    )
        except Error as e:
            print(f'Failed to create DB: {e}')
        else:
            print('DB have been successfully created')

    @classmethod
    def _create_db_structure(cls):
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        data = cls._get_data_from_file()
        try:
            subprocess.run(
                [
                    'mysql', f'--user={user}',
                    f'--password={password}', TEST_DB_NAME
                ],
                input=data
            )
        except Exception as e:
            print(f'Failed to create DB structure: {e}')
        else:
            print(f'DB structure have been successfully created')

    @staticmethod
    def _get_data_from_file() -> str:
        filepath = os.path.join(os.getcwd(), SQL_FOLDER, CREATEDB_FILE)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f'Failed to find {CREATEDB_FILE} with path: {filepath}'
            )

        with open(filepath, 'rb') as f:
            data = f.read()
        return data

    @classmethod
    def _drop_db(cls):
        try:
            with connect(**cls._config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f'DROP DATABASE {os.getenv("TEST_DB_NAME")}'
                    )
        except Error as e:
            print(f'Failed to drop DB: {e}')
        else:
            print(f'DB droped successfully')

    @classmethod
    def tearDownClass(cls) -> None:
        cls._drop_db()
