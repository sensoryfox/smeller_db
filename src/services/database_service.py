import logging
import json
from typing import List, Optional, Dict, Any, Type, Union
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.models.aroma_block import AromaBlockModel
from src.models.aroma_track import AromaTrackModel
from src.models.cartridge import CartridgeModel
from src.models.base import Base
from src.schemas.aroma_block import AromaBlock, AromaBlockCreate
from src.schemas.aroma_track import AromaTrack, AromaTrackCreate
from src.schemas.cartridge import Cartridge
from src.schemas.channel_control_config import ChannelControlConfig
from src.orm_client import ORMClient
from src.config.database import DatabaseConfig
from src.utils.console_printer import print_table_data, print_message
logger = logging.getLogger(__name__)

class DatabaseService:

    def __init__(self, db_config: DatabaseConfig, create_schema_on_init: bool = True, drop_all_on_init: bool = False):
        self.db_config = db_config

        # Первоначальная настройка схемы БД при инициализации DatabaseService
        if create_schema_on_init:
            # Используем временный ORMClient для операций со схемой
            # ORMClient теперь не принимает флаги create_schema/drop_all_on_init в конструкторе
            with ORMClient(config=self.db_config) as temp_db:
                if drop_all_on_init:
                    temp_db.drop_all_tables() # Вызываем явный метод
                temp_db.create_all_tables() # Вызываем явный метод
            logger.info("Initial database schema setup complete.")

        logger.info(f"DatabaseService initialized for host: {self.db_config.host}")

    def _convert_channel_configs_to_json_serializable(
        self, channel_configs: Dict[int, ChannelControlConfig]
    ) -> Dict[str, Any]:
        """
        Преобразует словарь Pydantic моделей ChannelControlConfig
        в словарь, пригодный для сохранения в JSON-поле базы данных.
        Ключи словаря должны быть строками для JSON.
        """
        json_serializable_configs = {}
        for channel_id, config_pydantic in channel_configs.items():
            # Pydantic model_dump() автоматически сериализует все поля, включая вложенные
            json_serializable_configs[str(channel_id)] = config_pydantic.model_dump()
        return json_serializable_configs

    def _convert_json_to_channel_configs(
        self, json_configs: Dict[str, Any]
    ) -> Dict[int, ChannelControlConfig]:
        """
        Преобразует JSON-словарь из базы данных обратно
        в словарь Pydantic моделей ChannelControlConfig.
        """
        pydantic_configs = {}
        if not json_configs:
            return pydantic_configs

        for channel_id_str, config_data in json_configs.items():
            try:
                channel_id = int(channel_id_str)
                # ChannelControlConfig(**config_data) автоматически десериализует
                pydantic_configs[channel_id] = ChannelControlConfig(**config_data)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to deserialize channel config for ID {channel_id_str}: {e}")
                continue
        return pydantic_configs

    def create_read_only_db_user(self, username: str, password: str) -> bool:
        """
        Создает нового пользователя (роль) в базе данных и выдает ему права только на чтение.
        Важно: Пользователь, от имени которого работает сервис, должен иметь права CREATEROLE и GRANT.
        """
        db_name = self.db_config.dbname
        if not username.isalnum():
            logger.error(f"Invalid username '{username}'. Only alphanumeric characters are allowed.")
            print_message(f"❌ Неверное имя пользователя '{username}'. Допускаются только буквенно-цифровые символы.", style="bold red")
            return False

        # Пароль будет безопасно связан через SQLAlchemy text() конструкцию
        # Для имени пользователя (роли) используем f-строку. Поскольку мы проверяем username.isalnum(),
        # это обеспечивает безопасность от SQL-инъекций для имени роли.
        # PostgreSQL приводит нецитированные идентификаторы к нижнему регистру.
        sql_create_role = f"CREATE ROLE {username} WITH LOGIN PASSWORD :user_password;"
        sql_grant_connect = f"GRANT CONNECT ON DATABASE {db_name} TO {username};"
        sql_grant_schema_usage = f"GRANT USAGE ON SCHEMA public TO {username};"
        sql_grant_select_tables = f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};"
        # Примечание: GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};
        # относится только к СУЩЕСТВУЮЩИМ таблицам.
        # Для автоматического предоставления прав на БУДУЩИЕ таблицы
        # требуется ALTER DEFAULT PRIVILEGES, который должен быть выполнен
        # пользователем, создающим эти таблицы. Это обычно делается
        # через миграции или при инициализации приложения.

        try:
            with ORMClient(config=self.db_config) as db:
                db.execute_raw_sql(sql_create_role, user_password=password) # <--- ПЕРЕДАЧА ПАРОЛЯ КАК ПАРАМЕТРА
                db.execute_raw_sql(sql_grant_connect)
                db.execute_raw_sql(sql_grant_schema_usage)
                db.execute_raw_sql(sql_grant_select_tables)
                logger.info(f"Read-only user '{username}' created and granted permissions on database '{db_name}'.")
                print_message(f"✅ Read-only user '{username}' успешно создан для базы данных '{db_name}'.", style="bold green")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create read-only user '{username}': {e}", exc_info=True)
            print_message(f"❌ Ошибка при создании read-only пользователя '{username}'. Error: {e}", style="bold red")
            return False

    def get_cartridge_by_id(self, cartridge_id: int) -> Optional[Cartridge]:
        # ORMClient теперь инициализируется без флагов create_schema/drop_all_on_init
        with ORMClient(config=self.db_config) as db:
            orm_cartridge = db.get(CartridgeModel, cartridge_id)
            if orm_cartridge:
                return Cartridge.model_validate(orm_cartridge)
            return None
    def get_all_cartridges(self) -> List[Cartridge]:
        with ORMClient(config=self.db_config) as db:
            orm_cartridges = db.all(CartridgeModel)
            return [Cartridge.model_validate(c) for c in orm_cartridges]
    def create_aroma_track(self, track_create: AromaTrackCreate) -> Optional[AromaTrack]:
        with ORMClient(config=self.db_config) as db:
            try:
                orm_track = AromaTrackModel(
                    name=track_create.name,
                    description=track_create.description
                )
                db.add(orm_track)
                db.flush() # Flush to get the ID for validation if needed, before commit
                logger.info(f"AromaTrack '{orm_track.name}' created with ID {orm_track.id}.")
                return AromaTrack.model_validate(orm_track)
            except Exception as e:
                logger.error(f"Database error creating AromaTrack: {e}", exc_info=True)
                return None
    def update_aroma_track(self, track_id: int, update_data: AromaTrackCreate) -> Optional[AromaTrack]:
        """Обновляет существующий AromaTrack в базе данных."""
        # NOTE: This method is async, but this is DatabaseService (sync).
        # It should be in AsyncDatabaseService or marked as async if it intends to use async ORMClient.
        # Given the context, it seems like a copy-paste error.
        # Keeping it as is but noting it should be in AsyncDatabaseService.
        with ORMClient(config=self.db_config) as db: # Use sync ORMClient here
            orm_track: AromaTrackModel = db.get(AromaTrackModel, track_id) # Use db.get directly
            if not orm_track:
                logger.warning(f"AromaTrack with ID {track_id} not found for update.")
                return None
            try:
                orm_track.name = update_data.name
                orm_track.description = update_data.description
                # Changes will be committed automatically upon exiting the 'with' block
                logger.info(f"AromaTrack '{orm_track.name}' with ID {orm_track.id} updated in DB.")
                # Get and return the updated object to ensure current data
                return self.get_aroma_track_by_id(orm_track.id) # Use sync method
            except Exception as e:
                logger.error(f"Database error updating AromaTrack ID {track_id}: {e}", exc_info=True)
                return None
    def get_aroma_track_by_id(self, track_id: int) -> Optional[AromaTrack]:
        with ORMClient(config=self.db_config) as db:
            orm_track = db.get(AromaTrackModel, track_id)
            if orm_track:
                return AromaTrack.model_validate(orm_track)
            return None
    def get_all_aroma_tracks(self) -> List[AromaTrack]:
        with ORMClient(config=self.db_config) as db:
            orm_tracks = db.all(AromaTrackModel)
            return [AromaTrack.model_validate(t) for t in orm_tracks]
    def delete_aroma_track(self, track_id: int) -> bool:
        with ORMClient(config=self.db_config) as db:
            return db.delete(AromaTrackModel, track_id)
    def create_aromablock(self, aromablock_create: AromaBlockCreate) -> Optional[AromaBlock]:
        with ORMClient(config=self.db_config) as db:
            try:
                channel_configs_json = self._convert_channel_configs_to_json_serializable(
                    aromablock_create.channel_configurations
                )

                orm_aromablock = AromaBlockModel(
                    name=aromablock_create.name,
                    description=aromablock_create.description,
                    data_type=aromablock_create.data_type,
                    content_link=aromablock_create.content_link,
                    channel_configurations=channel_configs_json,
                    start_time=aromablock_create.start_time,
                    stop_time=aromablock_create.stop_time,
                    aroma_track_id=aromablock_create.aroma_track_id
                )
                db.add(orm_aromablock)
                db.flush() # Flush to get the ID for validation if needed, before commit
                logger.info(f"AromaBlock '{orm_aromablock.name}' created with ID {orm_aromablock.id}.")

                channel_configs_pydantic = self._convert_json_to_channel_configs(orm_aromablock.channel_configurations or {})
                return AromaBlock(
                    id=orm_aromablock.id,
                    name=orm_aromablock.name,
                    description=orm_aromablock.description,
                    data_type=orm_aromablock.data_type,
                    content_link=orm_aromablock.content_link,
                    channel_configurations=channel_configs_pydantic,
                    start_time=orm_aromablock.start_time,
                    stop_time=orm_aromablock.stop_time,
                    aroma_track_id=orm_aromablock.aroma_track_id
                )
            except Exception as e:
                logger.error(f"Database error creating AromaBlock: {e}", exc_info=True)
                return None
    def get_aromablock_by_id(self, aromablock_id: int) -> Optional[AromaBlock]:
        with ORMClient(config=self.db_config) as db:
            orm_aromablock: AromaBlockModel = db.get(AromaBlockModel, aromablock_id)
            if orm_aromablock:
                channel_configs = self._convert_json_to_channel_configs(
                    orm_aromablock.channel_configurations or {}
                )
                return AromaBlock(
                    id=orm_aromablock.id,
                    name=orm_aromablock.name,
                    description=orm_aromablock.description,
                    data_type=orm_aromablock.data_type,
                    content_link=orm_aromablock.content_link,
                    channel_configurations=channel_configs,
                    start_time=orm_aromablock.start_time,
                    stop_time=orm_aromablock.stop_time,
                    aroma_track_id=orm_aromablock.aroma_track_id
                )
            return None
    def get_all_aromablocks(self) -> List[AromaBlock]:
        with ORMClient(config=self.db_config) as db:
            orm_aromablocks: List[AromaBlockModel] = db.all(AromaBlockModel)
            aromablocks = []
            for orm_block in orm_aromablocks:
                channel_configs = self._convert_json_to_channel_configs(
                    orm_block.channel_configurations or {}
                )
                aromablocks.append(
                    AromaBlock(
                        id=orm_block.id,
                        name=orm_block.name,
                        description=orm_block.description,
                        data_type=orm_block.data_type,
                        content_link=orm_block.content_link,
                        channel_configurations=channel_configs,
                        start_time=orm_block.start_time,
                        stop_time=orm_block.stop_time,
                        aroma_track_id=orm_block.aroma_track_id
                    )
                )
            return aromablocks
    def update_aromablock(self, aromablock_id: int, update_data: AromaBlockCreate) -> Optional[AromaBlock]:
        with ORMClient(config=self.db_config) as db:
            orm_aromablock: AromaBlockModel = db.get(AromaBlockModel, aromablock_id)
            if not orm_aromablock:
                logger.warning(f"AromaBlock with ID {aromablock_id} not found for update.")
                return None

            try:
                orm_aromablock.name = update_data.name
                orm_aromablock.description = update_data.description
                orm_aromablock.data_type = update_data.data_type
                orm_aromablock.content_link = update_data.content_link
                orm_aromablock.start_time = update_data.start_time
                orm_aromablock.stop_time = update_data.stop_time
                orm_aromablock.aroma_track_id = update_data.aroma_track_id
                orm_aromablock.channel_configurations = self._convert_channel_configs_to_json_serializable(
                    update_data.channel_configurations
                )
                logger.info(f"AromaBlock '{orm_aromablock.name}' with ID {orm_aromablock.id} updated in DB.")
                return self.get_aromablock_by_id(orm_aromablock.id)
            except Exception as e:
                logger.error(f"Database error updating AromaBlock ID {aromablock_id}: {e}", exc_info=True)
                return None
    def delete_aromablock(self, aromablock_id: int) -> bool:
        with ORMClient(config=self.db_config) as db:
            return db.delete(AromaBlockModel, aromablock_id)
    def get_table_names(self) -> List[str]:
        with ORMClient(config=self.db_config) as db:
            return db.get_table_names_raw()
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        with ORMClient(config=self.db_config) as db:
            return db.get_columns_info_raw(table_name)
    def get_table_data_preview(self, model_or_table_name: Union[Type[Base], str], limit: int = 5) -> Dict[str, Any]:
        with ORMClient(config=self.db_config) as db:
            headers: List[str] = []
            rows: List[List[Any]] = []

            if isinstance(model_or_table_name, type) and issubclass(model_or_table_name, Base):
                orm_model = model_or_table_name
                from sqlalchemy import inspect
                mapper = inspect(orm_model)
                headers = [c.key for c in mapper.columns]

                stmt = select(orm_model).limit(limit)
                result = db.session.execute(stmt).scalars().all()

                for row_obj in result:
                    row_data = []
                    for col_name in headers:
                        item = getattr(row_obj, col_name)
                        if isinstance(item, (dict, list)):
                            row_data.append(json.dumps(item, indent=2, ensure_ascii=False))
                        else:
                            row_data.append(item)
                    rows.append(row_data)
                logger.debug(f"Fetched {len(rows)} rows from ORM model {orm_model.__tablename__}.")
            elif isinstance(model_or_table_name, str):
                table_name = model_or_table_name
                columns_info = db.get_columns_info_raw(table_name)
                headers = [col['name'] for col in columns_info]
                rows = db.get_raw_table_data(table_name, limit=limit)
                logger.debug(f"Fetched {len(rows)} raw rows from table {table_name}.")
            else:
                raise ValueError("model_or_table_name must be an ORM model class or a string table name.")

            return {"headers": headers, "rows": rows}
    def print_database_overview(
        self,
        preview_rows: int = 3,
        headers_only: bool = False,
    ) -> None:
        """
        Красиво выводит в консоль информацию обо всех таблицах.
        Если headers_only=True, выводятся только названия колонок.
        """
        table_names = self.get_table_names()
        if not table_names:
            print_message("В базе пока нет таблиц.", style="bold yellow")
            return

        print_message("📊  Состояние базы данных", style="bold green")

        for table_name in table_names:
            preview = self.get_table_data_preview(table_name, limit=preview_rows)
            rows = [] if headers_only else preview["rows"]
            title = f"🗄️  {table_name}  ({len(rows)} / {preview_rows if not headers_only else 0})"
            print_table_data(
                title=title,
                headers=preview["headers"],
                rows=rows,
                row_limit=None if headers_only else preview_rows
            )