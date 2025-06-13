import typer
from rich import print as rprint
import asyncio # Импорт для запуска асинхронных функций
from typing import Union
from src.config.database import DatabaseConfig
from src.services.database_service import DatabaseService         # Синхронный сервис
from src.services.database_service_async import AsyncDatabaseService # Асинхронный сервис
from src.utils.console_printer import print_message             # Используется обоими сервисами
app = typer.Typer(add_completion=False, help="📚 Утилиты для работы с базой данных")

def _get_configured_service(async_mode: bool) -> Union[DatabaseService, AsyncDatabaseService]:
    cfg = DatabaseConfig.from_env()
    # Важно: В CLI-утилитах, которые только читают данные,
    # не следует автоматически создавать или удалять схему.
    # Это должно быть явной командой (например, через миграции или отдельный CLI-метод).
    if async_mode:
        # Для AsyncDatabaseService схема управляется через `setup_schema`
        return AsyncDatabaseService(db_config=cfg)
    else:
        # Для DatabaseService, передаем флаги явно, чтобы избежать случайного создания/удаления
        return DatabaseService(db_config=cfg, create_schema_on_init=False, drop_all_on_init=False)

@app.command(name="show-db") # Переименовал для ясности
def show_db(
    rows: int = typer.Option(3, help="Сколько строк превью выводить"),
    headers_only: bool = typer.Option(False, "--headers", help="Только заголовки"),
    async_mode: bool = typer.Option(False, "--async", help="Использовать async-клиент"),
):
    """
    Красиво вывести содержимое всех таблиц (синхронно или асинхронно).
    """
    if async_mode:
        async def _run_async_show():
            service = _get_configured_service(async_mode=True)
            print_message("Async connection OK!", style="bold blue")
            await service.print_database_overview(preview_rows=rows, headers_only=headers_only)
        asyncio.run(_run_async_show())
    else:
        service = _get_configured_service(async_mode=False)
        service.print_database_overview(preview_rows=rows, headers_only=headers_only)

@app.command(name="list-tables") # Переименовал для ясности
def list_tables(async_mode: bool = typer.Option(False, "--async", help="Использовать async-клиент")):
    """
    Показать список таблиц без превью.
    """
    if async_mode:
        async def _run_async_list_tables():
            service = _get_configured_service(async_mode=True)
            table_names = await service.get_table_names()
            for t in table_names:
                rprint(f"• [cyan]{t}[/cyan]")
        asyncio.run(_run_async_list_tables())
    else:
        service = _get_configured_service(async_mode=False)
        for t in service.get_table_names():
            rprint(f"• [cyan]{t}[/cyan]")

@app.command(name="init-schema")
def init_schema(
    drop_first: bool = typer.Option(False, "--drop-first", help="Удалить все таблицы перед созданием"),
    async_mode: bool = typer.Option(False, "--async", help="Использовать async-клиент"),
):
    """
    Инициализировать схему базы данных (создать все таблицы).
    """
    cfg = DatabaseConfig.from_env()
    if async_mode:
        async def _run_async_init_schema():
            service = AsyncDatabaseService(db_config=cfg)
            await service.setup_schema(create_schema=True, drop_all_first=drop_first)
            print_message("Async schema setup complete!", style="bold green")
        asyncio.run(_run_async_init_schema())
    else:
        # Передаем флаги напрямую в конструктор DatabaseService.
        # Он уже содержит логику для вызова create_all_tables/drop_all_tables внутри себя.
        service = DatabaseService(
            db_config=cfg,
            create_schema_on_init=True,   # Всегда пытаемся создать схему
            drop_all_on_init=drop_first   # Передаем значение drop_first
        )
        print_message("Sync schema setup complete!", style="bold green")
@app.command(name="create-user") # <--- НОВАЯ КОМАНДА
def create_db_user(
    username: str = typer.Argument(..., help="Имя нового пользователя (роли) базы данных."),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Пароль для нового пользователя. Будет запрошен безопасно."),
    async_mode: bool = typer.Option(False, "--async", help="Использовать async-клиент для создания пользователя."),
):
    """
    Создать нового пользователя базы данных с правами только на чтение.
    Важно: Пользователь, от имени которого вы запускаете эту команду, должен иметь
    административные привилегии (CREATEROLE, GRANT) в базе данных.
    """
    cfg = DatabaseConfig.from_env()
    if async_mode:
        async def _run_async_create_user():
            service = AsyncDatabaseService(db_config=cfg)
            # setup_schema здесь не требуется, т.к. мы просто создаем пользователя, а не схему.
            await service.create_read_only_db_user(username, password)
        asyncio.run(_run_async_create_user())
    else:
        service = DatabaseService(db_config=cfg, create_schema_on_init=False, drop_all_on_init=False)
        service.create_read_only_db_user(username, password)

if __name__ == "__main__":
    app()