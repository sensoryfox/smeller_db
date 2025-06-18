# smeller/schemas/channel_control_config.py       
from pydantic import BaseModel, Field
from typing import Dict, Tuple, List

class Color(BaseModel):
    """
    Pydantic модель для представления цвета RGB.
    """
    r: int = Field(..., ge=0, le=255, description="Красный компонент (0-255)")
    g: int = Field(..., ge=0, le=255, description="Зеленый компонент (0-255)")
    b: int = Field(..., ge=0, le=255, description="Синий компонент (0-255)")

    model_config = { # Pydantic v2
        "json_schema_extra": {
            "example": {"r": 255, "g": 100, "b": 0}
        }
    }


class ChannelControlConfig(BaseModel):
    """
    Pydantic модель для конфигурации управления каналом ароматов на устройстве.
    """
    channel_id: int = Field(..., description="Номер канала на устройстве (например, 1-4)")
    cycle_time: int = Field(..., ge=1, description="Время одного полного цикла работы канала в секундах")
    waypoints: List[Tuple[float, float]] = Field(
        ...,
        description="Список 'путевых точек' для интенсивности аромата. Каждая точка - (процент_времени, интенсивность_аромата)."
                    "Процент времени (0.0-1.0) от общего времени блока, интенсивность (0.0-1.0)."
                    "Пример: [(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)] - нарастание, затем спад."
    )
    interpolation_type: str = Field(
        "linear",
        description="Тип интерполяции между вейпоинтами (например, 'linear', 'exponential', 'sinusoidal', 'step', 'function')."
    )
    cartridge_id: str = Field("", description="Идентификатор картриджа аромата из базы данных (например, UUID).")
    cartridge_name: str = Field("", description="Читаемое имя картриджа аромата.")
    color: Color = Field(..., description="Цвет, ассоциированный с каналом")

    model_config = {
        "json_schema_extra": {
            "example": {
                "channel_id": 1,
                "cycle_time": 60,
                "waypoints": [[0.0, 0.0], [0.2, 0.8], [0.8, 0.8], [1.0, 0.0]],
                "interpolation_type": "linear",
                "cartridge_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "cartridge_name": "Fresh Orange",
                "color": {"r": 255, "g": 165, "b": 0, "a": 255}
            }
        }
    }