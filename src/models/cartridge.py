# smeller/models/cartridge.py
from sqlalchemy import Column, Integer, String
from .base import Base
import logging

logger = logging.getLogger(__name__)

class CartridgeModel(Base):

    __tablename__ = 'sl_catalog'
    ID = Column(Integer, primary_key=True, name='id') #  Изменили на 'id'
    NAME = Column(String, name='name') #  Изменили на 'name'
    CODE = Column(String, name='sl_category') #  Изменили на 'code'
    CLASS = Column(String, name='sl_class') #  Возможно, колонка называется 'sl_class'? Уточните реальное имя.

    def __repr__(self):
        return f"<Cartridge(ID={self.ID}, NAME='{self.NAME}', CODE='{self.CODE}', CLASS='{self.CLASS}')>" #  <--- ИСПРАВЛЕНО на self.ID, self.NAME, self.CODE, self.CLASS
