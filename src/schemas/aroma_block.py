# schemas/aroma_block.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, Union
from src.schemas.channel_control_config import ChannelControlConfig

class AromaBlockCreate(BaseModel):
    """
    Pydantic модель для создания нового аромаблока.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Название аромаблока")
    description: Optional[str] = Field(None, description="Описание аромаблока")
    data_type: str = Field(..., description="Тип данных (например, 'audio/mp3', 'image/jpeg')")
    content_link: str = Field(..., description="Ссылка на контент")
    # Словарь, где ключ - int (ID канала), значение - ChannelControlConfig Pydantic модель
    channel_configurations: Dict[int, ChannelControlConfig] = Field(
        {}, description="Конфигурации управления каналами"
    )
    start_time: float = Field(0.0, ge=0.0, description="Время начала блока в треке (секунды)")
    stop_time: float = Field(..., ge=0.0, description="Время окончания блока в треке (секунды)")
    aroma_track_id: Optional[int] = Field(None, description="ID родительского трека ароматов")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Morning Coffee",
                "description": "The rich scent of freshly brewed coffee.",
                "data_type": "audio/mp3",
                "content_link": "https://example.com/audio/coffee.mp3",
                "channel_configurations": {
                    "1": {"active": True, "volume": 0.8, "color": {"r": 139, "g": 69, "b": 19}},
                    "2": {"active": False, "volume": 0.0, "color": {"r": 0, "g": 0, "b": 0}}
                },
                "start_time": 0.0,
                "stop_time": 30.0,
                "aroma_track_id": 1
            }
        }
    }

class AromaBlock(AromaBlockCreate):
    """
    Pydantic модель для представления аромаблока (с ID).
    """
    id: int = Field(..., ge=1, description="Уникальный идентификатор аромаблока")

    model_config = {
        "from_attributes": True, # Разрешает Pydantic читать атрибуты из ORM объектов
        "json_schema_extra": {
            "example": {
                "id": 101,
                "name": "Morning Coffee",
                "description": "The rich scent of freshly brewed coffee.",
                "data_type": "audio/mp3",
                "content_link": "https://example.com/audio/coffee.mp3",
                "channel_configurations": {
                    "1": {"active": True, "volume": 0.8, "color": {"r": 139, "g": 69, "b": 19}},
                    "2": {"active": False, "volume": 0.0, "color": {"r": 0, "g": 0, "b": 0}}
                },
                "start_time": 0.0,
                "stop_time": 30.0,
                "aroma_track_id": 1
            }
        }
    }