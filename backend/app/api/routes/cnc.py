"""Endpoints para CNCs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from calendar import monthrange

from app.database import get_db
from app.models.cnc import CNC, StatusCNC
from app.schemas.cnc import CNCResponse, CNCList

router = APIRouter()


@router.get("/cnc", response_model=CNCList)
def listar_cncs(
    status: Optional[StatusCNC] = Query(None),
    subprefeitura: Optional[str] = Query(None),
    mes_referencia: Optional[str] = Query(
        None, description="Filtra pelo mês de referência no formato YYYY-MM"
    ),
    full: bool = Query(
        False,
        description="Quando verdadeiro, retorna todos os registros do período sem paginação",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista CNCs com filtros."""
    query = db.query(CNC)
    
    if status:
        query = query.filter(CNC.status == status)
    if subprefeitura:
        query = query.filter(CNC.subprefeitura == subprefeitura)
    
    if mes_referencia:
        try:
            mes_dt = datetime.strptime(mes_referencia, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="mes_referencia deve estar no formato YYYY-MM"
            )
        _, last_day = monthrange(mes_dt.year, mes_dt.month)
        inicio_mes = datetime(mes_dt.year, mes_dt.month, 1)
        fim_mes = datetime(mes_dt.year, mes_dt.month, last_day, 23, 59, 59, 999999)
        query = query.filter(
            CNC.data_abertura >= inicio_mes,
            CNC.data_abertura <= fim_mes
        )
    
    total = query.count()
    
    if full:
        cncs = query.order_by(CNC.data_abertura.desc()).all()
        current_page = 1
        current_page_size = total
    else:
        offset = (page - 1) * page_size
        cncs = query.order_by(CNC.data_abertura.desc()).offset(offset).limit(page_size).all()
        current_page = page
        current_page_size = page_size
    
    return CNCList(
        items=[CNCResponse.model_validate(cnc) for cnc in cncs],
        total=total,
        page=current_page,
        page_size=current_page_size
    )


@router.get("/cnc/urgent")
def listar_cncs_urgentes(
    db: Session = Depends(get_db)
):
    """Lista CNCs urgentes (próximas do prazo)."""
    from datetime import datetime, timedelta
    
    agora = datetime.utcnow()
    cncs_urgentes = []
    
    cncs = db.query(CNC).filter(
        CNC.status == StatusCNC.PENDENTE
    ).all()
    
    for cnc in cncs:
        tempo_decorrido = (agora - cnc.data_abertura).total_seconds() / 3600
        percentual_usado = (tempo_decorrido / cnc.prazo_hours) * 100
        
        if percentual_usado >= 50:  # Mais de 50% do prazo usado
            cncs_urgentes.append(cnc)
            # Atualizar status se necessário
            if percentual_usado >= 100:
                cnc.status = StatusCNC.URGENTE
    
    db.commit()
    
    return {
        "urgentes": [CNCResponse.model_validate(cnc) for cnc in cncs_urgentes]
    }


@router.get("/cnc/{cnc_id}", response_model=CNCResponse)
def obter_cnc(
    cnc_id: str,
    db: Session = Depends(get_db)
):
    """Obtém detalhes de uma CNC."""
    cnc = db.query(CNC).filter(CNC.bfs == cnc_id).first()
    if not cnc:
        raise HTTPException(status_code=404, detail="CNC não encontrada")
    
    return CNCResponse.model_validate(cnc)

