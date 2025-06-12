from __future__ import annotations
import logging
from contextlib import AbstractAsyncContextManager
from typing import Optional, Iterable, Any, Type, Union, Dict, List

from sqlalchemy import select, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)

from src.config.database import DatabaseConfig
from src.models.base import Base

logger = logging.getLogger(__name__)


class AsyncORMClient(AbstractAsyncContextManager):
    """
    Async-версия ORMClient; API максимально похоже на синхронную.
    Используется «async with»!
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self.engine = create_async_engine(self.config.async_url, future=True)
        self._SessionFactory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        self.session: Optional[AsyncSession] = None
        logger.debug("AsyncORMClient initialised.")

    # ------------------------------------------------------------------ schema
    async def create_all_tables(self):
        await self.engine.run_sync(Base.metadata.create_all)

    async def drop_all_tables(self):
        await self.engine.run_sync(Base.metadata.drop_all)

    # --------------------------------------------------------- context-manager
    async def __aenter__(self):
        self.session = self._SessionFactory()
        logger.debug("Async session opened.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.session.rollback()
                logger.error("Rollback by exception.", exc_info=exc_tb)
            else:
                await self.session.commit()
                logger.debug("Commit OK.")
        finally:
            await self.session.close()
            self.session = None
            logger.debug("Async session closed.")
        return False      # не подавляем исключения

    # ----------------------------------------------------------------- helpers
    async def add(self, instance: Base):
        self._ensure_session()
        self.session.add(instance)
        return instance

    async def add_all(self, instances: Iterable[Base]):
        self._ensure_session()
        self.session.add_all(instances)

    async def get(self, model: Type[Base], pk: Any):
        self._ensure_session()
        return await self.session.get(model, pk)

    async def all(self, model: Type[Base]) -> list[Base]:
        self._ensure_session()
        result = await self.session.execute(select(model))
        return result.scalars().all()

    async def delete(self,
                     instance_or_model: Union[Base, Type[Base]],
                     pk: Any = None) -> bool:
        self._ensure_session()
        obj = instance_or_model
        if pk is not None and not isinstance(instance_or_model, Base):
            obj = await self.get(instance_or_model, pk)
        if obj:
            await self.session.delete(obj)
            return True
        return False

    async def flush(self):
        self._ensure_session()
        await self.session.flush()

    async def rollback(self):
        self._ensure_session()
        await self.session.rollback()

    # ------------------------------------------------------------ reflection
    async def get_table_names_raw(self) -> List[str]:
        async with self.engine.begin() as conn:
            return await conn.run_sync(lambda c: inspect(c).get_table_names())

    async def get_columns_info_raw(self, table: str) -> List[Dict[str, Any]]:
        async with self.engine.begin() as conn:
            return await conn.run_sync(lambda c: inspect(c).get_columns(table))

    async def get_raw_table_data(self, table: str, limit: int = 10):
        from sqlalchemy import Table, MetaData
        meta = MetaData()
        async with self.session.begin():          # внутри текущей сессии
            def _run(sync_conn):
                tbl = Table(table, meta, autoload_with=sync_conn)
                res = sync_conn.execute(select(*tbl.columns).limit(limit))
                return [list(r) for r in res.fetchall()]
            return await self.session.run_sync(_run)
    
    async def execute_raw_sql(self, sql_query: str, **params) -> Any: # <--- НОВЫЙ МЕТОД
        """
        Выполняет произвольный сырой SQL-запрос асинхронно.
        Используйте с осторожностью! Параметры передаются безопасно.
        """
        self._ensure_session()
        try:
            result = await self.session.execute(text(sql_query), params)
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error executing raw SQL: {sql_query} with params {params}. Error: {e}", exc_info=True)
            raise
    # ---------------------------------------------------------------- private
    def _ensure_session(self):
        if not self.session:
            raise RuntimeError("Use 'async with AsyncORMClient() as db:'")