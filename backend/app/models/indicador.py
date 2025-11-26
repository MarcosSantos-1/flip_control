"""Model para Indicadores."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Enum, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.sac import Subprefeitura
import enum


class TipoIndicador(str, enum.Enum):
    """Tipos de indicadores."""
    IRD = "IRD"  # Índice de Reclamações Domiciliares
    IA = "IA"    # Índice de Atendimento
    IF = "IF"    # Índice de Fiscalização
    IPT = "IPT"  # Índice de Execução dos Planos de Trabalho
    ADC = "ADC"  # Avaliação de Desempenho da Contratada


class Indicador(Base):
    """Model para Indicadores (snapshots por período)."""
    __tablename__ = "indicadores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoIndicador), nullable=False, index=True)
    valor = Column(Numeric(10, 4), nullable=False)  # Valor do indicador
    pontuacao = Column(Numeric(5, 2), nullable=True)  # Pontuação obtida (ex: 20 pontos)
    
    # Período
    periodo_inicial = Column(DateTime, nullable=False, index=True)
    periodo_final = Column(DateTime, nullable=False)
    
    # Subprefeitura (nullable para indicadores gerais)
    subprefeitura = Column(Enum(Subprefeitura), nullable=True, index=True)
    
    # Metadados
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    detalhes = Column(String, nullable=True)  # JSON string com detalhes do cálculo
    
    # Índices
    __table_args__ = (
        Index("idx_indicador_tipo_periodo", "tipo", "periodo_inicial", "periodo_final"),
        Index("idx_indicador_subpref_periodo", "subprefeitura", "periodo_inicial"),
    )
    
    def __repr__(self):
        return f"<Indicador {self.tipo} - {self.valor} ({self.periodo_inicial})>"

