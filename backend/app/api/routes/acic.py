"""Endpoints para ACICs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.acic import ACIC, StatusACIC
from app.schemas.acic import ACICResponse, ACICList

router = APIRouter()


@router.get("/acic", response_model=ACICList)
def listar_acics(
    status: Optional[StatusACIC] = Query(None),
    subprefeitura: Optional[str] = Query(None),
    periodo_inicial: Optional[datetime] = Query(None),
    periodo_final: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista ACICs com filtros."""
    query = db.query(ACIC)
    
    if status:
        query = query.filter(ACIC.status == status)
    if subprefeitura:
        query = query.filter(ACIC.area == subprefeitura)
    if periodo_inicial:
        query = query.filter(ACIC.data_acic >= periodo_inicial)
    if periodo_final:
        query = query.filter(ACIC.data_acic <= periodo_final)
    
    total = query.count()
    offset = (page - 1) * page_size
    acics = query.order_by(ACIC.data_acic.desc()).offset(offset).limit(page_size).all()
    
    return ACICList(
        items=[ACICResponse.model_validate(acic) for acic in acics],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/acic/{acic_id}", response_model=ACICResponse)
def obter_acic(
    acic_id: str,
    db: Session = Depends(get_db)
):
    """Obtém detalhes de uma ACIC."""
    acic = db.query(ACIC).filter(ACIC.n_acic == acic_id).first()
    if not acic:
        raise HTTPException(status_code=404, detail="ACIC não encontrada")
    
    return ACICResponse.model_validate(acic)

