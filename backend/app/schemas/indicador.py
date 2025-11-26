"""Schemas para Indicadores."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from app.models.indicador import TipoIndicador
from app.models.sac import Subprefeitura


class IndicadorCreate(BaseModel):
    """Schema para criação de indicador."""
    tipo: TipoIndicador
    valor: Decimal
    pontuacao: Optional[Decimal] = None
    periodo_inicial: datetime
    periodo_final: datetime
    subprefeitura: Optional[Subprefeitura] = None
    detalhes: Optional[str] = None


class IndicadorResponse(IndicadorCreate):
    """Schema de resposta para indicador."""
    id: UUID
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class IndicadorList(BaseModel):
    """Schema para listagem de indicadores."""
    items: List[IndicadorResponse]
    total: int

