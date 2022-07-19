import logging

from bot.database import user_gateway
from bot.entities import User
from bot.exceptions import DataAlreadyExistsInDBError


def save(id: int, username: str, first_name: str, last_name: str) -> None:
    try:
        user_gateway.save(User(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name
        ))
        logging.info(f'User with id={id} successfully added')
    except DataAlreadyExistsInDBError as e:
        logging.error(e)