"""Endpoints para roteirização."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.sac import SAC
from app.services.roteirizacao import RoteirizacaoService

router = APIRouter()


@router.post("/roteiros/gerar")
def gerar_roteiro(
    sac_ids: List[UUID],
    fiscal_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Gera roteiro otimizado para uma lista de SACs."""
    service = RoteirizacaoService(db)
    roteiro = service.gerar_roteiro(sac_ids, fiscal_id)
    
    return roteiro

