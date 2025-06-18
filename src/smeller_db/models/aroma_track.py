# smeller/models/aroma_track.py

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .base import Base
        
class AromaTrackModel(Base):
    """
    SQLAlchemy model for the 'aroma_tracks' database table, storing AromaTrack information.
    """
    __tablename__ = 'aroma_tracks'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text) #  Используем Text вместо String для длинных описаний

    aromablocks = relationship("AromaBlockModel", back_populates="aroma_track") #  One-to-many relationship

    def __repr__(self):
        return f"<AromaTrackModel(id={self.id}, name='{self.name}')>"
