import logging

from mysql.connector import connect, Error, errorcode

from bot.entities import User
from bot.exceptions import DataAlreadyExistsInDBError, CantSaveToDBError
from .config import db_config


ADD_USER_QUERY = """
    INSERT INTO users
    (id, username, first_name, last_name)
    VALUES (%s, %s, %s, %s)
"""


def save(user: User) -> bool:
    """Save user to database"""
    try:
        with connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(ADD_USER_QUERY, (*user,))
                connection.commit()
        return True
    except Error as e:
        error = f'Failed to add user: {e}'
        logging.exception(error)
        if e.errno == errorcode.ER_DUP_ENTRY:
            raise DataAlreadyExistsInDBError(error)
        raise CantSaveToDBError(error)
