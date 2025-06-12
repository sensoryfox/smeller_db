# schemas/cartridge.py
from pydantic import BaseModel, Field
from typing import Optional

class Cartridge(BaseModel):
    """
    Pydantic модель для представления картриджа.
    Использует alias для соответствия именам колонок в CartridgeModel (SQLAlchemy).
    """
    id: Optional[int] = Field(None, alias="ID", description="Уникальный идентификатор картриджа")
    name: Optional[str] = Field(None, alias="NAME", description="Название картриджа")
    code: Optional[str] = Field(None, alias="CODE", description="Код картриджа/категория")
    class_: Optional[str] = Field(None, alias="CLASS", description="Класс картриджа") # Используем _class чтобы избежать конфликта с зарезервированным словом

    model_config = {
        "from_attributes": True, # Разрешает Pydantic читать атрибуты из ORM объектов
        "populate_by_name": True, # Разрешает инициализацию по именам полей (id, name, code, _class)
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Vanilla Bean",
                "code": "SWEET",
                "class": "ESSENTIAL" # В JSON будет "class"
            }
        }
    }