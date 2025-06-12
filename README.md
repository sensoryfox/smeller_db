# Aroma DB Client 📚

> Удобный синхронно-асинхронный клиент (SQLAlchemy 2.0 style) с сервис-слоем и CLI для работы
> с базой данных проекта **Aroma Platform**.  
> Пакет можно поставить одной командой `pip install aroma-db-client`
> и сразу воспользоваться как из Python-кода, так и из терминала.

---

## Содержание

1. [Почему именно этот клиент?](#почему-этот-клиент)
2. [Установка](#установка)
3. [Настройка окружения (.env)](#настройка-окружения)
4. [Быстрый старт (синхронный)](#быстрый-старт-sync)
5. [Быстрый старт (асинхронный)](#быстрый-старт-async)
6. [CLI-утилита `aroma-db`](#cli-утилита)
7. [API-справка](#api-справка)
8. [Разработка / вклад](#разработка--вклад)
9. [Лицензия](#license)

---

## Почему этот клиент?

* **Два режима** — сразу готовы `ORMClient` и `AsyncORMClient`.
* **Pydantic v2** — типобезопасное превращение ORM-объектов в датаклассы и обратно.
* **Rich & Typer** — красивые таблицы и мощный CLI «из коробки».
* **Zero-Boilerplate** — одна строка для получения превью любой таблицы,
  одна команда CLI для инициализации схемы.
* **Пример-шаблон** (см. `tests/test.py`) — копируйте и начинайте.

---

## Установка

```bash
# Из PyPI
pip install aroma-db-client

# Локальная разработка
git clone https://github.com/sensoryfox/aroma-db-client.git
cd aroma-db-client
pip install -e .[dev]   # + dev-зависимости
```
Python ≥ 3.9 обязателен (используются `typing.Annotated`, match-statement и т.д.).

---

## Настройка окружения

`DatabaseConfig` автоматически подтянет значения из переменных окружения
(можно задать в `.env` файле). Минимальный набор:

```
DB_HOST=185.180.230.207
DB_PORT=55432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=SL_aroma
```

Допускается форма URL-строки `postgresql://user:pass@host:port/dbname` — смотрите
`src/config/database.py`.

---
```py
## Быстрый старт (synchronous) <a name="быстрый-старт-sync"></a>
from src.services import DatabaseService
from src.schemas.aroma_track import AromaTrackCreate
from src.schemas.channel_control_config import ChannelControlConfig, Color

service = DatabaseService.from_env()  # использует .env

# 1) Создадим трек
track = service.create_aroma_track(
    AromaTrackCreate(
        name="Demo track",
        description="Just a couple of blocks 🙂"
    )
)

# 2) Добавим аромаблок
block = service.create_aromablock(
    AromaBlockCreate(
        name="Lime intro",
        description="Opening shot of fresh lime",
        data_type="image",
        content_link="s3://bucket/frames/lime.png",
        start_time=0.0,
        stop_time=3.0,
        aroma_track_id=track.id,
        channel_configurations={
            1: ChannelControlConfig(
                color=Color(r=0, g=255, b=0),
                intensity=0.7,
                interpolation="linear" # TODO MORE
            )
        }
    )
)

print(track)
print(block)

# 3) Красиво покажем состояние БД
service.print_database_overview()
```
---
```py
## Быстрый старт (asynchronous) <a name="быстрый-старт-async"></a>
import asyncio
from src.services.database_service_async import AsyncDatabaseService
from src.schemas.aroma_track import AromaTrackCreate

async def main():
    service = AsyncDatabaseService.from_env()

    await service.setup_schema(create_schema=True)  # или миграции alembic

    track = await service.create_aroma_track(
        AromaTrackCreate(name="Async track", description="Created asynchronously")
    )
    print(track)

asyncio.run(main())
```
---

## CLI-утилита <a name="cli-утилита"></a>

После установки пакета появляется (должна) команда `aroma-db`.
# Посмотреть все возможности
aroma-db --help
Часто используемые под-команды:
| Команда | Описание |
| ------------------------------------------- | --------------------------------------------------- |
| `aroma-db show-db` | Красивый вывод всех таблиц (+3 строки превью). |
| `aroma-db show-db --headers` | Только заголовки таблиц. |
| `aroma-db list-tables` | Сухой список таблиц. |
| `aroma-db init-schema` | Создать (если нужно – пересоздать) все таблицы. |
| `aroma-db init-schema --drop-first` | Удалить **всё** и заново создать. ⚠ Будьте осторожны! |
| `aroma-db ... --async` | Любая команда может быть выполнена через async. |

Пример:
# Одной строкой посмотреть первые 5 записей всех таблиц

```bash
aroma-db show-db --rows 5
```

---

## API-справка

src/
├─ async_orm_client.py        – «сырой» AsyncSession-обёртка (low-level)
├─ orm_client.py              – синхронный вариант
├─ services/
│    ├─ database_service.py   – высокоуровневый sync-сервис
│    └─ database_service_async.py – async-сервис
├─ models/                    – ORM-таблицы SQLAlchemy
└─ schemas/                   – Pydantic-схемы (DTO)

Основные публичные классы/функции:

| Класс/функция | Где находится | Назначение |
| ---------------------------------------- | -------------------------------------- | ------------ |
| `ORMClient`, `AsyncORMClient` | `src/orm_client.py`, `src/async_orm_client.py` | Base-клиенты для CRUD, контекстный менеджер |
| `DatabaseService`, `AsyncDatabaseService` | `src/services/…` | CRUD + удобные вспомогательные методы |
| `get_db_client()` | `src/db_client_factory.py` | Фабрика sync/async-клиентов |
| `aroma-db` (CLI) | `src/tools/db_cli.py` | Управление БД из терминала |

Полная автодока генерируется `pdoc`/`mkdocs` (см. раздел «docs»).

---

## Разработка / вклад

1. Склонируйте репозиторий.
2. `pip install -e .[dev]`
3. Запустите тесты: `pytest -q`.
4. Перед PR запустите `black . && isort . && mypy src`.

Будем рады pull-request'ам 🚀

---

## License

`aroma-db-client` распространяется по лицензии **MIT** – делайте с кодом, что хотите,
но не забудьте сохранить копию лицензии.
────────────────────────────────────────

Готово!  
• `pyproject.toml` — вставьте в корень проекта и запустите `python -m build`,  
  затем `twine upload dist/*` — пакет уже готов к публикации.  
• `README.md` — кладётся рядом; PyPI отобразит его как документацию.  
