# test.py
import logging
import json
from rich.console import Console
from rich.table import Table
from rich import print as rich_print

from src.config.database import DatabaseConfig
from src.services.database_service import DatabaseService
from src.schemas.aroma_block import AromaBlockCreate, AromaBlock
from src.schemas.aroma_track import AromaTrackCreate, AromaTrack
from src.schemas.channel_control_config import ChannelControlConfig, Color
from src.schemas.interpolation import InterpolationType # Импортируем новый класс
from src.models.aroma_block import AromaBlockModel
from src.models.aroma_track import AromaTrackModel
from src.models.cartridge import CartridgeModel
from src.utils.console_printer import print_table_data, print_message, print_key_value_pairs

console = Console()

# Настройка логирования для лучшей видимости
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Инициализация: Настройка базы данных ---
print_message("--- Демонстрация: Инициализация базы данных ---", style="bold blue")

# Инициализируем DatabaseConfig
db_config = DatabaseConfig.from_env()

# Инициализируем DatabaseService.
# drop_all_on_init=True используется здесь ОДИН РАЗ, чтобы очистить БД в начале выполнения скрипта.
# Все последующие операции будут использовать этот же экземпляр db_service.
db_service = DatabaseService(db_config, create_schema_on_init=True, drop_all_on_init=True)

print_message("Проверка текущих таблиц в БД:", style="bold blue")
table_names = db_service.get_table_names()
print_key_value_pairs("Таблицы в БД", {"Tables": ", ".join(table_names) if table_names else "No tables found"})

# --- Демонстрация: Создание AromaTrack ---
print_message("\n--- Демонстрация: Создание AromaTrack ---", style="bold green")

# Определение данных для AromaTrack
new_track_data = AromaTrackCreate(
    name="Rainy Day Serenity",
    description="A track designed for relaxation with natural rain sounds and calming aromas."
)

created_track = db_service.create_aroma_track(new_track_data)

if created_track:
    print_key_value_pairs(f"Создан новый AromaTrack с ID: {created_track.id}, Name: {created_track.name}", created_track.model_dump())
else:
    print_message("Ошибка при создании AromaTrack.", style="bold red")

# --- Демонстрация: Создание AromaBlock (используя ID созданного AromaTrack) ---
print_message("\n--- Демонстрация: Создание AromaBlock ---", style="bold green")

if created_track:
    # Пример конфигурации канала
    # Обратите внимание на использование класса Color, как было указано в вашем сообщении
    channel_configs = {
        1: ChannelControlConfig(
            channel_id=1,
            cycle_time=30.0,
            waypoints=[(0.0, 0.0), (0.5, 1.0), (1.0, 0.5)],
            interpolation_type=InterpolationType.LINEAR,
            cartridge_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            cartridge_name="Rain Fresh",
            color=Color(r=50, g=150, b=200) # Использование класса Color
        ),
        2: ChannelControlConfig(
            channel_id=2,
            cycle_time=45.0,
            waypoints=[(0.0, 1.0), (0.7, 0.2), (1.0, 0.0)],
            interpolation_type=InterpolationType.EXPONENTIAL,
            cartridge_id="f0e9d8c7-b6a5-4321-fedc-ba9876543210",
            cartridge_name="Morning Fresh",
            color=Color(r=0, g=120, b=0) # Использование класса Color
        )
    }

    new_aromablock_data = AromaBlockCreate(
        name="Soft Rain with Scent",
        description="Gentle rain sound with dynamic aroma release.",
        data_type="audio/wav",
        content_link="http://example.com/rain_scent.wav",
        channel_configurations=channel_configs,
        start_time=0.0,
        stop_time=120.0,
        aroma_track_id=created_track.id # Привязываем к только что созданному AromaTrack
    )

    created_aromablock = db_service.create_aromablock(new_aromablock_data)

    if created_aromablock:
        print_key_value_pairs(f"Создан новый AromaBlock с ID: {created_aromablock.id}, Name: {created_aromablock.name}", created_aromablock.model_dump())
    else:
        print_message("Ошибка при создании AromaBlock. Проверьте логи для деталей.", style="bold red")
else:
    print_message("Невозможно создать AromaBlock, так как AromaTrack не был создан.", style="bold red")

# --- Демонстрация: Получение всех AromaTracks ---
print_message("\n--- Демонстрация: Получение всех AromaTracks ---", style="bold blue")
all_tracks = db_service.get_all_aroma_tracks()
if all_tracks:
    track_headers = ["ID", "Name", "Description"]
    track_rows = [[t.id, t.name, t.description] for t in all_tracks]
    print_table_data("Все AromaTracks", track_headers, track_rows)
else:
    print_message("Нет AromaTracks в базе данных.", style="dim")

# --- Демонстрация: Получение всех AromaBlocks ---
print_message("\n--- Демонстрация: Получение всех AromaBlocks ---", style="bold blue")
all_blocks = db_service.get_all_aromablocks()
if all_blocks:
    block_headers = ["ID", "Name", "Type", "Link", "Start", "Stop", "Track ID", "Channel Configs"]
    block_rows = []
    for b in all_blocks:
        # Для удобства отображения, преобразуем channel_configurations в строку
        channel_configs_summary = json.dumps({k: v.model_dump_json() for k, v in b.channel_configurations.items()}, indent=2, ensure_ascii=False)
        block_rows.append([
            b.id, b.name, b.data_type, b.content_link, b.start_time, b.stop_time, b.aroma_track_id, channel_configs_summary
        ])
    print_table_data("Все AromaBlocks", block_headers, block_rows)
else:
    print_message("Нет AromaBlocks в базе данных.", style="dim")

# --- Демонстрация: Обновление AromaBlock ---
print_message("\n--- Демонстрация: Обновление AromaBlock ---", style="bold yellow")
if created_aromablock:
    updated_channel_configs = {
        1: ChannelControlConfig(
            channel_id=1,
            cycle_time=60.0, # Обновленное время цикла
            waypoints=[(0.0, 0.2), (0.8, 0.8), (1.0, 0.1)],
            interpolation_type=InterpolationType.SINUSOIDAL, # Обновленный тип интерполяции
            cartridge_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            cartridge_name="Rain Fresh - Updated",
            color=Color(r=255, g=0, b=0) # Обновленный цвет
        )
    }
    update_data = AromaBlockCreate(
        name="Soft Rain with Scent - UPDATED",
        description="Gentle rain sound with dynamic aroma release. Now with updated parameters.",
        data_type="audio/wav",
        content_link="http://example.com/rain_scent_updated.wav",
        channel_configurations=updated_channel_configs,
        start_time=5.0, # Обновленное время начала
        stop_time=125.0, # Обновленное время окончания
        aroma_track_id=created_track.id # Все еще привязан к тому же треку
    )
    updated_aromablock = db_service.update_aromablock(created_aromablock.id, update_data)
    if updated_aromablock:
        print_key_value_pairs(f"AromaBlock с ID {updated_aromablock.id} обновлен:", updated_aromablock.model_dump())
    else:
        print_message(f"Ошибка при обновлении AromaBlock с ID {created_aromablock.id}.", style="bold red")

# --- Демонстрация: Проверка обновленного AromaBlock ---
print_message("\n--- Демонстрация: Проверка обновленного AromaBlock ---", style="bold blue")
if created_aromablock:
    verified_aromablock = db_service.get_aromablock_by_id(created_aromablock.id)
    if verified_aromablock:
        print_key_value_pairs(f"Проверенный AromaBlock с ID {verified_aromablock.id}:", verified_aromablock.model_dump())
    else:
        print_message(f"Не удалось найти AromaBlock с ID {created_aromablock.id} после обновления.", style="bold red")

# --- Демонстрация: Удаление AromaBlock ---
print_message("\n--- Демонстрация: Удаление AromaBlock ---", style="bold red")
if created_aromablock:
    deleted_block_success = db_service.delete_aromablock(created_aromablock.id)
    print_message(f"AromaBlock с ID {created_aromablock.id} удален: {deleted_block_success}", 
                  style="green" if deleted_block_success else "red")
else:
    print_message("Нет AromaBlock для удаления.", style="dim")

# --- Демонстрация: Удаление AromaTrack ---
print_message("\n--- Демонстрация: Удаление AromaTrack ---", style="bold red")
if created_track:
    deleted_track_success = db_service.delete_aroma_track(created_track.id)
    print_message(f"AromaTrack с ID {created_track.id} удален: {deleted_track_success}",
                  style="green" if deleted_track_success else "red")
else:
    print_message("Нет AromaTrack для удаления.", style="dim")

print_message("\n--- Завершение демонстрации ---", style="bold blue")