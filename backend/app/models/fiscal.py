"""Model para Fiscais."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Float, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.sac import Subprefeitura
import enum


class Turno(str, enum.Enum):
    """Turnos de trabalho."""
    MANHA = "Manhã"
    TARDE = "Tarde"
    NOITE = "Noite"


class Fiscal(Base):
    """Model para Fiscais."""
    __tablename__ = "fiscais"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, nullable=False, index=True)
    subprefeitura = Column(Enum(Subprefeitura), nullable=True, index=True)
    turno = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    ativo = Column(Boolean, default=True, index=True)
    
    # Última localização
    last_location = Column(JSON, nullable=True)  # {lat, lng, timestamp}
    last_location_lat = Column(Float, nullable=True)
    last_location_lng = Column(Float, nullable=True)
    last_location_time = Column(DateTime, nullable=True)
    
    # Relacionamentos
    sacs = relationship("SAC", back_populates="fiscal")
    
    # Índices
    __table_args__ = (
        Index("idx_fiscal_subpref_ativo", "subprefeitura", "ativo"),
    )
    
    def __repr__(self):
        return f"<Fiscal {self.nome} - {self.subprefeitura}>"

