from __future__ import annotations
import logging
from contextlib import AbstractContextManager
from typing import Type, Iterable, Any, Optional, Union, List, Dict
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from smeller_db.models.base import Base # Импортируем базовый класс для ORM-моделей
from smeller_db.config.database import DatabaseConfig # Импортируем конфигурацию БД
logger = logging.getLogger(__name__)

class ORMClient(AbstractContextManager):
    """
    ORMClient предоставляет контекстный менеджер для управления сессиями SQLAlchemy.
    Теперь он отвечает только за управление сессиями и основные CRUD-операции.
    Создание и удаление схемы БД перенесено в DatabaseService для контроля.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Инициализирует ORMClient, настраивая движок и фабрику сессий.
        Параметры create_schema и drop_all_on_init удалены из конструктора,
        так как управление схемой теперь внешнее.
        """
        self.config = config or DatabaseConfig.from_env()
        self.engine = create_engine(self.config.url, future=True)

        self._SessionFactory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
        self.session: Optional[Session] = None
        logger.debug("ORMClient initialized.")

    def drop_all_tables(self) -> None:
        """Удаляет все таблицы, определенные в Base.metadata, из базы данных. ДЕСТРУКТИВНО!"""
        try:
            logger.warning("Attempting to drop all database tables. THIS IS DESTRUCTIVE!")
            Base.metadata.drop_all(self.engine)
            logger.info("All existing tables dropped.")
        except SQLAlchemyError as e:
            logger.critical(f"Failed to drop database tables: {e}", exc_info=True)
            raise

    def create_all_tables(self) -> None:
        """Создает все таблицы, определенные в Base.metadata, в базе данных."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database schema checked/created successfully.")
        except SQLAlchemyError as e:
            logger.critical(f"Failed to create database schema: {e}", exc_info=True)
            raise

    def __enter__(self) -> "ORMClient":
        """
        Инициализирует новую сессию SQLAlchemy при входе в 'with' блок.
        Эта сессия будет использоваться для всех операций внутри блока.
        """
        self.session = self._SessionFactory()
        logger.debug("SQLAlchemy session opened.")
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[Any]) -> bool:
        """
        Управляет коммитом или откатом транзакции и закрытием сессии при выходе из 'with' блока.

        Если произошло исключение (exc_type не None), транзакция откатывается.
        Иначе, транзакция коммитится. Сессия всегда закрывается.

        Args:
            exc_type (Optional[Type[BaseException]]): Тип исключения, если оно произошло.
            exc_val (Optional[BaseException]): Значение исключения.
            exc_tb (Optional[Any]): Трейсбек исключения.

        Returns:
            bool: False, чтобы исключение (если оно было) было повторно вызвано после обработки.
                  True подавило бы исключение.
        """
        try:
            if exc_type:
                logger.error(f"Transaction rolled back due to an exception: {exc_val}", exc_info=exc_tb)
                self.session.rollback()
            else:
                self.session.commit()
                logger.debug("Transaction committed successfully.")
        except SQLAlchemyError as e:
            logger.critical(f"Error during commit/rollback or session close: {e}", exc_info=True)
            # Позволяем ошибке распространиться выше
            raise
        finally:
            self.session.close()
            self.session = None # Обнуляем сессию, чтобы предотвратить её повторное использование
            logger.debug("SQLAlchemy session closed.")
        return False # Важно: False позволяет исключению проброситься дальше

    def add(self, instance: Base) -> Base:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        self.session.add(instance)
        return instance

    def add_all(self, instances: Iterable[Base]) -> None:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        self.session.add_all(instances)

    def get(self, model: Type[Base], pk: Any) -> Optional[Base]:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        return self.session.get(model, pk)

    def all(self, model: Type[Base]) -> list[Base]:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        return self.session.query(model).all()

    def query(self, model: Type[Base]) -> Any:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        return self.session.query(model)

    def delete(self, instance_or_model: Union[Base, Type[Base]], pk: Any = None) -> bool:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")

        instance_to_delete: Optional[Base] = None
        if isinstance(instance_or_model, Base):
            instance_to_delete = instance_or_model
        elif pk is not None:
            instance_to_delete = self.get(instance_or_model, pk)
        else:
            logger.warning("Attempted to delete without instance or (model, pk).")
            return False

        if instance_to_delete:
            self.session.delete(instance_to_delete)
            return True
        else:
            logger.debug(f"Object not found for deletion: {instance_or_model}, pk={pk}")
            return False

    def flush(self) -> None:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        self.session.flush()

    def commit(self) -> None:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        self.session.commit()
        logger.debug("Manual commit performed.")

    def rollback(self) -> None:
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        self.session.rollback()
        logger.warning("Manual rollback performed.")

    def inspect(self, engine_or_connection: Any):
        """
        Возвращает объект Inspector для исследования базы данных.
        """
        return inspect(engine_or_connection)

    def get_table_names_raw(self) -> List[str]:
        """
        Возвращает список имен всех таблиц в базе данных, используя Inspector.
        """
        inspector = self.inspect(self.engine)
        return inspector.get_table_names()

    def get_columns_info_raw(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о колонках заданной таблицы (имя, тип, nullable, primary_key).
        """
        inspector = self.inspect(self.engine)
        return inspector.get_columns(table_name)

    def get_raw_table_data(self, table_name: str, limit: int = 10) -> List[List[Any]]:
        """
        Возвращает сырые данные из таблицы по имени таблицы, без ORM-модели.
        Это универсальный способ получить данные из любой таблицы.
        """
        with self._SessionFactory() as session: # Используем новую сессию
            try:
                # Получаем метаданные таблицы
                from sqlalchemy import Table, MetaData
                metadata = MetaData()
                table = Table(table_name, metadata, autoload_with=self.engine)

                # Выбираем все колонки из таблицы и выполняем запрос
                stmt = select(*table.columns).limit(limit)
                result = session.execute(stmt).fetchall()

                # Преобразуем RowProxy объекты в списки
                data_rows = [list(row) for row in result]
                return data_rows
            except Exception as e:
                logger.error(f"Failed to fetch raw data from table '{table_name}': {e}", exc_info=True)
                return []
            
    def execute_raw_sql(self, sql_query: str, **params) -> Any: # <--- НОВЫЙ МЕТОД
        """
        Выполняет произвольный сырой SQL-запрос.
        Используйте с осторожностью! Параметры передаются безопасно.
        """
        if not self.session:
            raise RuntimeError("ORMClient session is not active. Use 'with ORMClient() as db:'")
        try:
            result = self.session.execute(text(sql_query), params)
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error executing raw SQL: {sql_query} with params {params}. Error: {e}", exc_info=True)
            raise