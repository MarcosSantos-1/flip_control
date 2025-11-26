"""Endpoints para SACs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models.sac import SAC, StatusSAC, TipoServico, Subprefeitura
from app.schemas.sac import SACResponse, SACList, SACUpdate
from app.schemas import SACCreate

router = APIRouter()


def _annotate_sac(sac: SAC) -> SAC:
    """
    Enriquece o SAC com informações de prazo.
    
    IMPORTANTE: Apenas Demandantes são marcados como fora do prazo.
    Escalonados não importam o prazo (são agendados para até 1 mês).
    """
    horas = None
    fora = False
    
    # Tipos demandantes (com responsividade)
    tipos_demandantes = [TipoServico.ENTULHO, TipoServico.ANIMAL_MORTO, TipoServico.PAPELEIRAS]
    
    if sac.data_execucao and sac.data_criacao:
        total_seconds = (sac.data_execucao - sac.data_criacao).total_seconds()
        horas = round(total_seconds / 3600, 2)
        # Apenas Demandantes podem estar fora do prazo
        if sac.prazo_max_hours and sac.tipo_servico in tipos_demandantes:
            fora = horas > sac.prazo_max_hours
    
    setattr(sac, "horas_ate_execucao", horas)
    setattr(sac, "fora_do_prazo", fora)
    return sac


@router.get("/sacs", response_model=SACList)
def listar_sacs(
    status: Optional[StatusSAC] = Query(None),
    tipo_servico: Optional[TipoServico] = Query(None),
    subprefeitura: Optional[Subprefeitura] = Query(None),
    data_inicio: Optional[datetime] = Query(None),
    data_fim: Optional[datetime] = Query(None),
    fora_do_prazo: Optional[bool] = Query(
        None,
        description="Se True, retorna apenas SACs Demandantes (entulho, animal_morto, papeleiras) executados após o prazo máximo. Escalonados não são considerados."
    ),
    full: bool = Query(
        False,
        description="Quando verdadeiro, retorna todos os registros sem paginação"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista SACs com filtros."""
    query = db.query(SAC)
    
    # Aplicar filtros
    if status:
        query = query.filter(SAC.status == status)
    if tipo_servico:
        query = query.filter(SAC.tipo_servico == tipo_servico)
    if subprefeitura:
        query = query.filter(SAC.subprefeitura == subprefeitura)
    if data_inicio:
        query = query.filter(SAC.data_criacao >= data_inicio)
    if data_fim:
        query = query.filter(SAC.data_criacao <= data_fim)
    if fora_do_prazo is True:
        # Apenas Demandantes podem estar fora do prazo (Escalonados não importam o prazo)
        tipos_demandantes = [TipoServico.ENTULHO, TipoServico.ANIMAL_MORTO, TipoServico.PAPELEIRAS]
        query = query.filter(
            SAC.tipo_servico.in_(tipos_demandantes),
            SAC.data_execucao.isnot(None),
            func.extract("epoch", SAC.data_execucao - SAC.data_criacao) / 3600 > SAC.prazo_max_hours
        )
    
    # Contar total
    total = query.count()
    
    # Paginação
    if full:
        sacs = query.order_by(SAC.data_criacao.desc()).all()
        current_page = 1
        current_page_size = total
    else:
        offset = (page - 1) * page_size
        sacs = query.order_by(SAC.data_criacao.desc()).offset(offset).limit(page_size).all()
        current_page = page
        current_page_size = page_size
    
    return SACList(
        items=[SACResponse.model_validate(_annotate_sac(sac)) for sac in sacs],
        total=total,
        page=current_page,
        page_size=current_page_size
    )


@router.get("/sacs/{sac_id}", response_model=SACResponse)
def obter_sac(
    sac_id: UUID,
    db: Session = Depends(get_db)
):
    """Obtém detalhes de um SAC."""
    sac = db.query(SAC).filter(SAC.id == sac_id).first()
    if not sac:
        raise HTTPException(status_code=404, detail="SAC não encontrado")
    
    return SACResponse.model_validate(_annotate_sac(sac))


@router.post("/sacs/{sac_id}/agendar")
def agendar_sac(
    sac_id: UUID,
    data_agendamento: datetime,
    db: Session = Depends(get_db)
):
    """Agenda um SAC."""
    sac = db.query(SAC).filter(SAC.id == sac_id).first()
    if not sac:
        raise HTTPException(status_code=404, detail="SAC não encontrado")
    
    sac.data_agendamento = data_agendamento
    sac.status = StatusSAC.EM_EXECUCAO
    
    db.commit()
    db.refresh(sac)
    
    return {"success": True, "message": "SAC agendado com sucesso", "sac": SACResponse.model_validate(_annotate_sac(sac))}


@router.patch("/sacs/{sac_id}", response_model=SACResponse)
def atualizar_sac(
    sac_id: UUID,
    update_data: SACUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um SAC."""
    sac = db.query(SAC).filter(SAC.id == sac_id).first()
    if not sac:
        raise HTTPException(status_code=404, detail="SAC não encontrado")
    
    # Atualizar campos
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(sac, key, value)
    
    db.commit()
    db.refresh(sac)
    
    return SACResponse.model_validate(_annotate_sac(sac))


@router.get("/sacs/urgentes")
def listar_sacs_urgentes(
    db: Session = Depends(get_db)
):
    """Lista SACs urgentes (próximos do prazo ou vencidos)."""
    from datetime import datetime, timedelta
    
    agora = datetime.utcnow()
    
    # SACs demandantes > 24h sem vistoria
    sacs_demandantes = db.query(SAC).filter(
        and_(
            SAC.tipo_servico.in_([TipoServico.ENTULHO, TipoServico.ANIMAL_MORTO]),
            SAC.status == StatusSAC.AGUARDANDO_ANALISE,
            SAC.data_criacao < agora - timedelta(hours=24)
        )
    ).all()
    
    # SACs agendados > 72h sem execução
    sacs_atrasados = db.query(SAC).filter(
        and_(
            SAC.data_agendamento.isnot(None),
            SAC.status == StatusSAC.EM_EXECUCAO,
            SAC.data_agendamento < agora - timedelta(hours=72)
        )
    ).all()
    
    return {
        "demandantes_urgentes": [SACResponse.model_validate(sac) for sac in sacs_demandantes],
        "atrasados": [SACResponse.model_validate(sac) for sac in sacs_atrasados],
    }

