import os
from typing import Union

from src.orm_client import ORMClient
from src.async_orm_client import AsyncORMClient
from src.config.database import DatabaseConfig

# Значения «True» в env-переменной
_TRUE = {"1", "true", "yes", "y"}


def get_db_client(*,
                  async_mode: Union[bool, None] = None,
                  config: DatabaseConfig | None = None):
    """
    Возвращает НЕ-открытый (ещё без with/async with) клиент.
    При async_mode=None читаем переменную окружения DB_ASYNC.
    """
    if async_mode is None:
        async_mode = os.getenv("DB_ASYNC", "false").lower() in _TRUE
    cls = AsyncORMClient if async_mode else ORMClient
    return cls(config=config)

