# smeller/config/config.py
from __future__ import annotations
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла один раз при импорте модуля.
# Важно: В production-среде переменные окружения должны устанавливаться напрямую
# через менеджер секретов (Kubernetes Secrets, Vault и т.д.), а не через .env.
load_dotenv()

@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """
    Класс для хранения конфигурации подключения к базе данных PostgreSQL.

    Атрибуты:
        dbname (str): Имя базы данных. По умолчанию "postgres", если не найдено в POSTGRES_DB.
        user (str): Имя пользователя базы данных. По умолчанию "postgres", если не найдено в POSTGRES_USER.
        password (str): Пароль пользователя. По умолчанию пустая строка, если не найдено в POSTGRES_PASSWORD.
        host (str): Хост базы данных. По умолчанию "localhost", если не найдено в POSTGRES_HOST.
        port (str): Порт базы данных. По умолчанию "5432", если не найдено в POSTGRES_PORT.
        options (str): Дополнительные параметры подключения SQLAlchemy (например, "sslmode=require").
                       По умолчанию пустая строка, если не найдено в POSTGRES_OPTIONS.

    Использует dataclasses для создания неизменяемого и типизированного объекта конфигурации.
    """
    dbname:   str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "postgres"))
    user:     str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    host:     str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port:     str = field(default_factory=lambda: os.getenv("POSTGRES_PORT", "5432"))
    options:  str = field(default_factory=lambda: os.getenv("POSTGRES_OPTIONS", ""))

    @property
    def url(self) -> str:
        """
        Генерирует полную строку подключения (URL) для SQLAlchemy.

        Пример: "postgresql://user:password@host:port/dbname?options"
        """
        # Добавляем параметры только если они существуют
        opts = f"?{self.options}" if self.options else ""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}{opts}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        Фабричный метод для создания экземпляра DatabaseConfig,
        автоматически подтягивая значения из переменных окружения.
        """
        return cls()
    
    @property
    def async_url(self) -> str:
        """
        Формирует URL для async-движка (postgresql+asyncpg://…).
        Если dialect уже async – ничего не меняем.
        """
        if self.url().startswith("postgresql+asyncpg"):
            return self.url()
        return self.url().replace("postgresql://", "postgresql+asyncpg://", 1)