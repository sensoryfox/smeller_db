# schemas/aroma_track.py
from pydantic import BaseModel, Field
from typing import Optional, List

class AromaTrackCreate(BaseModel):
    """
    Pydantic модель для создания нового трека ароматов.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Название трека ароматов")
    description: Optional[str] = Field(None, description="Описание трека ароматов")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Relaxing Forest Walk",
                "description": "A track designed for deep relaxation with forest sounds and scents."
            }
        }
    }

class AromaTrack(AromaTrackCreate):
    """
    Pydantic модель для представления трека ароматов (с ID).
    """
    id: int = Field(..., ge=1, description="Уникальный идентификатор трека ароматов")

    model_config = {
        "from_attributes": True, # Разрешает Pydantic читать атрибуты из ORM объектов
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Relaxing Forest Walk",
                "description": "A track designed for deep relaxation with forest sounds and scents."
            }
        }
    }