"""Model para CNCs (BFS)."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Float, ForeignKey, Enum, JSON, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class StatusCNC(str, enum.Enum):
    """Status das CNCs."""
    PENDENTE = "pendente"
    URGENTE = "urgente"
    REGULARIZADO = "regularizado"
    AGUARDANDO_VISTORIA = "Aguardando Vistoria"


class CNC(Base):
    """Model para CNCs (BFS - Boletim de Fiscalização de Serviço)."""
    __tablename__ = "cnc"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bfs = Column(String, unique=True, nullable=False, index=True)  # N_BFS
    n_cnc = Column(String, nullable=True)
    subprefeitura = Column(String, nullable=False, index=True)
    area = Column(String, nullable=True)
    setor = Column(String, nullable=True)
    turno = Column(String, nullable=True)
    servico = Column(String, nullable=True)
    
    # Datas
    data_abertura = Column(DateTime, nullable=False, index=True)
    data_sincronizacao = Column(DateTime, nullable=True)
    data_fiscalizacao = Column(DateTime, nullable=True)
    data_execucao = Column(DateTime, nullable=True)
    
    # Prazos
    prazo_hours = Column(Integer, nullable=False)
    responsividade = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum(StatusCNC), nullable=False, default=StatusCNC.PENDENTE, index=True)
    situacao_cnc = Column(String, nullable=True)
    
    # Localização
    endereco = Column(String, nullable=True)
    coordenada = Column(String, nullable=True)  # Formato: "lat,lng"
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Descrição e evidências
    descricao = Column(Text, nullable=True)
    fotos = Column(JSON, nullable=True, default=list)
    
    # Fiscal
    fiscal_contratada = Column(String, nullable=True)
    agente_fiscalizador = Column(String, nullable=True)
    
    # Flags
    aplicou_multa = Column(Boolean, default=False, index=True)
    
    # Relacionamentos
    acics = relationship("ACIC", back_populates="cnc", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index("idx_cnc_status_prazo", "status", "prazo_hours"),
        Index("idx_cnc_data_abertura", "data_abertura"),
    )
    
    def __repr__(self):
        return f"<CNC {self.bfs} - {self.status}>"

