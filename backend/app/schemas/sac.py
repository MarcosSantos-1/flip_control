"""Schemas para SACs."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from app.models.sac import TipoServico, StatusSAC, Subprefeitura


class SACBase(BaseModel):
    """Schema base para SAC."""
    protocolo: str
    tipo_servico: TipoServico
    status: StatusSAC
    subprefeitura: Subprefeitura
    endereco_text: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    bairro: Optional[str] = None
    prazo_max_hours: int


class SACCreate(SACBase):
    """Schema para criação de SAC."""
    protocolo_origem: Optional[str] = None
    domicilio_id: Optional[str] = None
    data_criacao: Optional[datetime] = None
    fiscal_id: Optional[UUID] = None


class SACUpdate(BaseModel):
    """Schema para atualização de SAC."""
    status: Optional[StatusSAC] = None
    data_vistoria: Optional[datetime] = None
    data_agendamento: Optional[datetime] = None
    data_execucao: Optional[datetime] = None
    data_encerramento: Optional[datetime] = None
    fiscal_id: Optional[UUID] = None
    fotos_before: Optional[List[Dict[str, Any]]] = None
    fotos_after: Optional[List[Dict[str, Any]]] = None
    flag_erro_regional: Optional[bool] = None


class SACResponse(SACBase):
    """Schema de resposta para SAC."""
    id: UUID
    protocolo_origem: Optional[str]
    domicilio_id: Optional[str]
    data_criacao: datetime
    data_vistoria: Optional[datetime]
    data_agendamento: Optional[datetime]
    data_execucao: Optional[datetime]
    data_encerramento: Optional[datetime]
    fiscal_id: Optional[UUID]
    fotos_before: Optional[List[Dict[str, Any]]]
    fotos_after: Optional[List[Dict[str, Any]]]
    evidencias: Optional[Dict[str, Any]]
    flag_erro_regional: bool
    inserted_from_csv: bool
    horas_ate_execucao: Optional[float] = Field(default=None, description="Horas entre a abertura e a execução")
    fora_do_prazo: bool = Field(
        default=False, 
        description="Indica se o SAC foi executado após o prazo máximo. IMPORTANTE: Apenas Demandantes (entulho, animal_morto, papeleiras) são marcados como fora do prazo. Escalonados não importam o prazo."
    )
    
    class Config:
        from_attributes = True


class SACList(BaseModel):
    """Schema para listagem de SACs."""
    items: List[SACResponse]
    total: int
    page: int
    page_size: int

