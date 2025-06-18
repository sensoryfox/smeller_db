# smeller/models/cartridge.py
from sqlalchemy import Column, Integer, String
from .base import Base
import logging

logger = logging.getLogger(__name__)

class CartridgeModel(Base):

    __tablename__ = 'sl_catalog'
    ID = Column(Integer, primary_key=True, name='id') 
    NAME = Column(String, name='name') 
    CODE = Column(String, name='sl_category')
    CLASS = Column(String, name='sl_class') 
    ORIGIN = Column(String, name='sl_origin')  
    TYPE = Column(String, name='sl_type')      
    

    def __repr__(self):
        # Обновите repr для отображения новых полей
        return (f"<Cartridge(ID={self.ID}, NAME='{self.NAME}', CODE='{self.CODE}', "
                f"ORIGIN='{self.ORIGIN}', TYPE='{self.TYPE}', CLASS='{self.CLASS}')>")