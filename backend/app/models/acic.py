"""Model para ACICs (Autos de Constatação de Irregularidade da Contratada)."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class StatusACIC(str, enum.Enum):
    """Status dos ACICs."""
    SOLICITACAO = "Solicitacao"
    CONFIRMADO = "Confirmado"
    CANCELADO = "Cancelado"


class ACIC(Base):
    """Model para ACICs."""
    __tablename__ = "acic"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    n_acic = Column(String, nullable=True, index=True)
    n_bfs = Column(String, nullable=True)
    n_cnc = Column(String, nullable=True)
    
    # Relacionamento com CNC
    cnc_id = Column(UUID(as_uuid=True), ForeignKey("cnc.id"), nullable=True)
    
    # Status
    status = Column(Enum(StatusACIC), nullable=True)
    
    # Datas
    data_fiscalizacao = Column(DateTime, nullable=True)
    data_sincronizacao = Column(DateTime, nullable=True)
    data_execucao = Column(DateTime, nullable=True)
    data_acic = Column(DateTime, nullable=True, index=True)
    data_confirmacao = Column(DateTime, nullable=True)
    data_alteracao_status = Column(DateTime, nullable=True)
    
    # Informações do serviço
    servico = Column(String, nullable=True)
    responsavel = Column(String, nullable=True)
    agente_fiscalizador = Column(String, nullable=True)
    contratada = Column(String, nullable=True)
    regional = Column(String, nullable=True)
    area = Column(String, nullable=True)
    setor = Column(String, nullable=True)
    turno = Column(String, nullable=True)
    
    # Descrição
    descricao = Column(Text, nullable=True)
    
    # Multa
    valor_multa = Column(Numeric(10, 2), nullable=True)
    clausula_contratual = Column(String, nullable=True)
    observacao = Column(Text, nullable=True)
    
    # Localização
    endereco = Column(String, nullable=True)
    coordenada_aceite = Column(String, nullable=True)
    coordenada_resposta = Column(String, nullable=True)
    coordenada_vistoria = Column(String, nullable=True)
    
    # Relacionamentos
    cnc = relationship("CNC", back_populates="acics")
    
    # Índices
    __table_args__ = (
        Index("idx_acic_data_acic", "data_acic"),
        Index("idx_acic_status", "status"),
    )
    
    def __repr__(self):
        return f"<ACIC {self.n_acic} - {self.status}>"

