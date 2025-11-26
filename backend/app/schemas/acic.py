"""Schemas para ACICs."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from app.models.acic import StatusACIC
from decimal import Decimal


class ACICResponse(BaseModel):
    """Schema de resposta para ACIC."""
    id: UUID
    n_acic: Optional[str] = None
    n_bfs: Optional[str] = None
    n_cnc: Optional[str] = None
    status: Optional[StatusACIC] = None
    data_fiscalizacao: Optional[datetime] = None
    data_sincronizacao: Optional[datetime] = None
    data_execucao: Optional[datetime] = None
    data_acic: Optional[datetime] = None
    data_confirmacao: Optional[datetime] = None
    servico: Optional[str] = None
    responsavel: Optional[str] = None
    agente_fiscalizador: Optional[str] = None
    contratada: Optional[str] = None
    regional: Optional[str] = None
    area: Optional[str] = None
    setor: Optional[str] = None
    turno: Optional[str] = None
    descricao: Optional[str] = None
    valor_multa: Optional[Decimal] = None
    clausula_contratual: Optional[str] = None
    observacao: Optional[str] = None
    endereco: Optional[str] = None
    coordenada_aceite: Optional[str] = None
    coordenada_resposta: Optional[str] = None
    coordenada_vistoria: Optional[str] = None
    
    class Config:
        from_attributes = True


class ACICList(BaseModel):
    """Schema para listagem de ACICs."""
    items: List[ACICResponse]
    total: int
    page: int
    page_size: int

