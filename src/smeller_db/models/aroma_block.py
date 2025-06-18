# models/aroma_block.py
from sqlalchemy import Column, Integer, String, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class AromaBlockModel(Base):
    """
    SQLAlchemy model for the 'sl_aromablocks' database table, storing AromaBlock information.
    """
    __tablename__ = 'sl_aromablocks'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    data_type = Column(String)
    content_link = Column(String)
    channel_configurations = Column(JSON) # Храним как JSON
    start_time = Column(Float)
    stop_time = Column(Float)
    aroma_track_id = Column(Integer, ForeignKey('aroma_tracks.id', ondelete='SET NULL'), nullable=True) # nullable=True если не всегда нужен трек
    aroma_track = relationship("AromaTrackModel", back_populates="aromablocks")

    def __repr__(self) -> str:
        return (f"<AromaBlockModel(id={self.id}, name='{self.name}', "
                f"start_time={self.start_time}, stop_time={self.stop_time}, "
                f"track_id={self.aroma_track_id})>")