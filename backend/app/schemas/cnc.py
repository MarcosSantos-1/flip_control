"""Schemas para CNCs."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from app.models.cnc import StatusCNC


class CNCCreate(BaseModel):
    """Schema para criação de CNC."""
    bfs: str
    n_cnc: Optional[str] = None
    subprefeitura: str
    area: Optional[str] = None
    setor: Optional[str] = None
    turno: Optional[str] = None
    servico: Optional[str] = None
    data_abertura: datetime
    data_sincronizacao: Optional[datetime] = None
    data_fiscalizacao: Optional[datetime] = None
    data_execucao: Optional[datetime] = None
    prazo_hours: int
    responsividade: Optional[int] = None
    status: StatusCNC = StatusCNC.PENDENTE
    situacao_cnc: Optional[str] = None
    endereco: Optional[str] = None
    coordenada: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    descricao: Optional[str] = None
    fotos: Optional[List[Dict[str, Any]]] = None
    fiscal_contratada: Optional[str] = None
    agente_fiscalizador: Optional[str] = None
    aplicou_multa: bool = False


class CNCResponse(CNCCreate):
    """Schema de resposta para CNC."""
    id: UUID
    
    class Config:
        from_attributes = True


class CNCList(BaseModel):
    """Schema para listagem de CNCs."""
    items: List[CNCResponse]
    total: int
    page: int
    page_size: int

