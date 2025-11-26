"""Endpoints para indicadores."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime
from decimal import Decimal
import logging

from app.database import get_db
from app.models.indicador import Indicador, TipoIndicador
from app.models.sac import Subprefeitura
from app.models.cnc import CNC, StatusCNC
from app.models.sac import SAC
from app.services.indicadores import IndicadoresService
from app.schemas.indicador import IndicadorResponse, IndicadorList

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/indicadores", response_model=IndicadorList)
def listar_indicadores(
    tipo: Optional[TipoIndicador] = Query(None),
    subprefeitura: Optional[Subprefeitura] = Query(None),
    periodo_inicial: Optional[datetime] = Query(None),
    periodo_final: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Lista indicadores calculados."""
    query = db.query(Indicador)
    
    if tipo:
        query = query.filter(Indicador.tipo == tipo)
    if subprefeitura:
        query = query.filter(Indicador.subprefeitura == subprefeitura)
    if periodo_inicial:
        query = query.filter(Indicador.periodo_inicial >= periodo_inicial)
    if periodo_final:
        query = query.filter(Indicador.periodo_final <= periodo_final)
    
    indicadores = query.order_by(Indicador.calculated_at.desc()).all()
    
    return IndicadorList(
        items=[IndicadorResponse.model_validate(ind) for ind in indicadores],
        total=len(indicadores)
    )


@router.get("/indicadores/detalhes")
def detalhar_indicadores(
    periodo_inicial: Optional[datetime] = Query(
        None, description="Data inicial; se vazio, usa o primeiro dia do mês atual"
    ),
    periodo_final: Optional[datetime] = Query(
        None, description="Data final; se vazio, usa a data e hora atuais"
    ),
    subprefeitura: Optional[Subprefeitura] = Query(None),
    db: Session = Depends(get_db)
):
    """Retorna os cálculos completos de IRD, IA e IF para o período informado."""
    from datetime import datetime as dt

    agora = dt.utcnow()
    if not periodo_final:
        periodo_final = agora
    if not periodo_inicial:
        periodo_inicial = periodo_final.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    service = IndicadoresService(db)
    ird = service.calcular_ird(periodo_inicial, periodo_final, subprefeitura)
    ia = service.calcular_ia(periodo_inicial, periodo_final, subprefeitura)
    if_result = service.calcular_if(periodo_inicial, periodo_final, subprefeitura)
    
    # Buscar IPT do banco de dados
    # Estratégia: buscar IPT que intersecta com o período OU que está dentro do mesmo mês/ano do período solicitado
    from datetime import datetime as dt
    
    # Extrair mês/ano do período solicitado
    mes_periodo = periodo_inicial.month
    ano_periodo = periodo_inicial.year
    
    # Primeiro tentar buscar IPT que intersecta com o período solicitado
    ipt_indicador = db.query(Indicador).filter(
        and_(
            Indicador.tipo == TipoIndicador.IPT,
            Indicador.periodo_inicial <= periodo_final,
            Indicador.periodo_final >= periodo_inicial,
            Indicador.subprefeitura.is_(None)
        )
    ).order_by(Indicador.calculated_at.desc()).first()
    
    # Se não encontrou, buscar IPT do mesmo mês/ano do período solicitado
    if not ipt_indicador:
        inicio_mes_periodo = dt(ano_periodo, mes_periodo, 1, 0, 0, 0)
        # Calcular fim do mês
        if mes_periodo == 12:
            fim_mes_periodo = dt(ano_periodo + 1, 1, 1, 0, 0, 0)
        else:
            fim_mes_periodo = dt(ano_periodo, mes_periodo + 1, 1, 0, 0, 0)
        
        ipt_indicador = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.periodo_inicial >= inicio_mes_periodo,
                Indicador.periodo_inicial < fim_mes_periodo,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
    
    # Se ainda não encontrou, buscar o IPT mais recente
    if not ipt_indicador:
        ipt_indicador = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
    
    ipt_result = None
    if ipt_indicador:
        ipt_result = {
            "valor": float(ipt_indicador.valor),
            "pontuacao": float(ipt_indicador.pontuacao),
            "periodo_inicial": ipt_indicador.periodo_inicial.isoformat(),
            "periodo_final": ipt_indicador.periodo_final.isoformat(),
        }
        logger.info(f"IPT encontrado para período {periodo_inicial} - {periodo_final}: valor={ipt_result['valor']}, pontuacao={ipt_result['pontuacao']}")
    else:
        logger.warning(f"IPT não encontrado para período {periodo_inicial} - {periodo_final}, mês/ano: {mes_periodo}/{ano_periodo}")

    return {
        "periodo": {
            "inicial": periodo_inicial.isoformat(),
            "final": periodo_final.isoformat(),
        },
        "subprefeitura": subprefeitura.value if subprefeitura else None,
        "ird": ird,
        "ia": ia,
        "if": if_result,
        "ipt": ipt_result,
    }


@router.post("/indicadores/calcular/ird")
def calcular_ird(
    periodo_inicial: datetime,
    periodo_final: datetime,
    subprefeitura: Optional[Subprefeitura] = Query(None),
    salvar: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Calcula IRD para um período."""
    service = IndicadoresService(db)
    resultado = service.calcular_ird(periodo_inicial, periodo_final, subprefeitura)
    
    if salvar:
        service.salvar_indicador(resultado)
    
    return resultado


@router.post("/indicadores/calcular/ia")
def calcular_ia(
    periodo_inicial: datetime,
    periodo_final: datetime,
    subprefeitura: Optional[Subprefeitura] = Query(None),
    salvar: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Calcula IA para um período."""
    service = IndicadoresService(db)
    resultado = service.calcular_ia(periodo_inicial, periodo_final, subprefeitura)
    
    if salvar:
        service.salvar_indicador(resultado)
    
    return resultado


@router.post("/indicadores/calcular/if")
def calcular_if(
    periodo_inicial: datetime,
    periodo_final: datetime,
    subprefeitura: Optional[Subprefeitura] = Query(None),
    salvar: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Calcula IF para um período."""
    service = IndicadoresService(db)
    resultado = service.calcular_if(periodo_inicial, periodo_final, subprefeitura)
    
    if salvar:
        service.salvar_indicador(resultado)
    
    return resultado


@router.post("/indicadores/calcular/ipt")
def calcular_ipt(
    periodo_inicial: datetime,
    periodo_final: datetime,
    valor_mao_obra: Decimal,
    valor_equipamentos: Decimal,
    salvar: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Calcula IPT para um período."""
    service = IndicadoresService(db)
    resultado = service.calcular_ipt(periodo_inicial, periodo_final, valor_mao_obra, valor_equipamentos)
    
    if salvar:
        service.salvar_indicador(resultado)
    
    return resultado


@router.post("/indicadores/salvar/ipt")
def salvar_ipt(
    periodo_inicial: datetime,
    periodo_final: datetime,
    percentual_total: Decimal = Query(..., description="Percentual total do IPT (0-100)"),
    db: Session = Depends(get_db)
):
    """
    Salva ou atualiza IPT com percentual total.
    Calcula a pontuação automaticamente baseado no percentual.
    Se já existir IPT para o período, atualiza ao invés de criar duplicado.
    """
    service = IndicadoresService(db)
    
    # Verificar se já existe IPT para este período
    ipt_existente = db.query(Indicador).filter(
        and_(
            Indicador.tipo == TipoIndicador.IPT,
            Indicador.periodo_inicial == periodo_inicial,
            Indicador.periodo_final == periodo_final,
            Indicador.subprefeitura.is_(None)
        )
    ).first()
    
    # Calcular pontuação baseado no percentual
    pontuacao = service._calcular_pontuacao_ipt(percentual_total)
    
    if ipt_existente:
        # Atualizar existente
        ipt_existente.valor = percentual_total
        ipt_existente.pontuacao = pontuacao
        db.commit()
        db.refresh(ipt_existente)
        indicador_salvo = ipt_existente
        mensagem = "IPT atualizado com sucesso"
    else:
        # Criar novo
        resultado = {
            "tipo": TipoIndicador.IPT,
            "valor": float(percentual_total),
            "pontuacao": float(pontuacao),
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
        }
        indicador_salvo = service.salvar_indicador(resultado)
        mensagem = "IPT salvo com sucesso"
    
    return {
        "success": True,
        "message": mensagem,
        "indicador": {
            "valor": float(percentual_total),
            "pontuacao": float(pontuacao),
            "periodo_inicial": periodo_inicial.isoformat(),
            "periodo_final": periodo_final.isoformat(),
        }
    }


@router.post("/indicadores/calcular/adc")
def calcular_adc(
    periodo_inicial: datetime,
    periodo_final: datetime,
    valor_ipt: Optional[Decimal] = Query(None),
    valor_mao_obra: Optional[Decimal] = Query(None),
    valor_equipamentos: Optional[Decimal] = Query(None),
    subprefeitura: Optional[Subprefeitura] = Query(None),
    db: Session = Depends(get_db)
):
    """Calcula ADC completo para um período."""
    from datetime import datetime as dt
    
    service = IndicadoresService(db)
    
    # Se não forneceu IPT, buscar do banco de dados
    if valor_ipt is None:
        # Extrair mês/ano do período solicitado
        mes_periodo = periodo_inicial.month
        ano_periodo = periodo_inicial.year
        
        # Primeiro tentar buscar IPT que intersecta com o período solicitado
        ipt_indicador = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.periodo_inicial <= periodo_final,
                Indicador.periodo_final >= periodo_inicial,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
        
        # Se não encontrou, buscar IPT do mesmo mês/ano do período solicitado
        if not ipt_indicador:
            inicio_mes_periodo = dt(ano_periodo, mes_periodo, 1, 0, 0, 0)
            # Calcular fim do mês
            if mes_periodo == 12:
                fim_mes_periodo = dt(ano_periodo + 1, 1, 1, 0, 0, 0)
            else:
                fim_mes_periodo = dt(ano_periodo, mes_periodo + 1, 1, 0, 0, 0)
            
            ipt_indicador = db.query(Indicador).filter(
                and_(
                    Indicador.tipo == TipoIndicador.IPT,
                    Indicador.periodo_inicial >= inicio_mes_periodo,
                    Indicador.periodo_inicial < fim_mes_periodo,
                    Indicador.subprefeitura.is_(None)
                )
            ).order_by(Indicador.calculated_at.desc()).first()
        
        # Se ainda não encontrou, buscar o IPT mais recente
        if not ipt_indicador:
            ipt_indicador = db.query(Indicador).filter(
                and_(
                    Indicador.tipo == TipoIndicador.IPT,
                    Indicador.subprefeitura.is_(None)
                )
            ).order_by(Indicador.calculated_at.desc()).first()
        
        if ipt_indicador:
            valor_ipt = ipt_indicador.valor
    
    resultado = service.calcular_adc(
        periodo_inicial,
        periodo_final,
        valor_ipt,
        valor_mao_obra,
        valor_equipamentos,
        subprefeitura
    )
    
    # Se não tinha IPT no resultado mas encontramos no banco, adicionar
    if "ipt" not in resultado or resultado.get("ipt") is None:
        # Extrair mês/ano do período solicitado
        mes_periodo = periodo_inicial.month
        ano_periodo = periodo_inicial.year
        
        # Primeiro tentar buscar IPT que intersecta com o período
        ipt_indicador_db = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.periodo_inicial <= periodo_final,
                Indicador.periodo_final >= periodo_inicial,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
        
        # Se não encontrou, buscar IPT do mesmo mês/ano do período solicitado
        if not ipt_indicador_db:
            inicio_mes_periodo = dt(ano_periodo, mes_periodo, 1, 0, 0, 0)
            # Calcular fim do mês
            if mes_periodo == 12:
                fim_mes_periodo = dt(ano_periodo + 1, 1, 1, 0, 0, 0)
            else:
                fim_mes_periodo = dt(ano_periodo, mes_periodo + 1, 1, 0, 0, 0)
            
            ipt_indicador_db = db.query(Indicador).filter(
                and_(
                    Indicador.tipo == TipoIndicador.IPT,
                    Indicador.periodo_inicial >= inicio_mes_periodo,
                    Indicador.periodo_inicial < fim_mes_periodo,
                    Indicador.subprefeitura.is_(None)
                )
            ).order_by(Indicador.calculated_at.desc()).first()
        
        # Se ainda não encontrou, buscar o IPT mais recente
        if not ipt_indicador_db:
            ipt_indicador_db = db.query(Indicador).filter(
                and_(
                    Indicador.tipo == TipoIndicador.IPT,
                    Indicador.subprefeitura.is_(None)
                )
            ).order_by(Indicador.calculated_at.desc()).first()
        
        if ipt_indicador_db:
            resultado["ipt"] = {
                "valor": float(ipt_indicador_db.valor),
                "pontuacao": float(ipt_indicador_db.pontuacao),
            }
    
    return resultado


@router.post("/indicadores/recalcular")
def recalcular_indicadores(
    periodo_inicial: datetime,
    periodo_final: datetime,
    db: Session = Depends(get_db)
):
    """Recalcula todos os indicadores para um período."""
    service = IndicadoresService(db)
    
    resultados = {
        "ird": service.calcular_ird(periodo_inicial, periodo_final),
        "ia": service.calcular_ia(periodo_inicial, periodo_final),
        "if": service.calcular_if(periodo_inicial, periodo_final),
    }
    
    # Salvar indicadores
    for resultado in resultados.values():
        service.salvar_indicador(resultado)
    
    return {
        "success": True,
        "message": "Indicadores recalculados e salvos",
        "resultados": resultados
    }


@router.get("/dashboard/indicadores/historico")
def obter_historico_indicadores(
    periodo_inicial: Optional[datetime] = Query(None),
    periodo_final: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtém histórico de indicadores para o gráfico de evolução."""
    from datetime import datetime, timedelta
    
    # Se não especificado, usar último mês
    if not periodo_final:
        periodo_final = datetime.utcnow()
    if not periodo_inicial:
        periodo_inicial = periodo_final - timedelta(days=30)
    
    # Buscar indicadores salvos no período
    indicadores = db.query(Indicador).filter(
        and_(
            Indicador.periodo_inicial >= periodo_inicial,
            Indicador.periodo_final <= periodo_final,
            Indicador.subprefeitura.is_(None)  # Apenas indicadores gerais
        )
    ).order_by(Indicador.calculated_at.asc()).all()
    
    # Agrupar por data e tipo
    historico_por_data = {}
    for ind in indicadores:
        # Usar data de cálculo como chave
        data_key = ind.calculated_at.date().isoformat()
        if data_key not in historico_por_data:
            historico_por_data[data_key] = {
                "data": data_key,
                "ia": None,
                "ird": None,
                "if": None,
                "ipt": None,
            }
        
        if ind.tipo == TipoIndicador.IA:
            historico_por_data[data_key]["ia"] = {"valor": float(ind.valor), "pontuacao": float(ind.pontuacao)}
        elif ind.tipo == TipoIndicador.IRD:
            historico_por_data[data_key]["ird"] = {"valor": float(ind.valor), "pontuacao": float(ind.pontuacao)}
        elif ind.tipo == TipoIndicador.IF:
            historico_por_data[data_key]["if"] = {"valor": float(ind.valor), "pontuacao": float(ind.pontuacao)}
        elif ind.tipo == TipoIndicador.IPT:
            historico_por_data[data_key]["ipt"] = {"valor": float(ind.valor), "pontuacao": float(ind.pontuacao)}
    
    # Converter para lista ordenada
    historico_lista = list(historico_por_data.values())
    historico_lista.sort(key=lambda x: x["data"])
    
    return {"data": historico_lista}


@router.get("/dashboard/kpis")
def obter_kpis_dashboard(
    periodo_inicial: Optional[datetime] = Query(None),
    periodo_final: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Obtém KPIs para o dashboard."""
    from datetime import datetime, timedelta
    
    # Se não especificado, usar último mês
    if not periodo_final:
        periodo_final = datetime.utcnow()
    if not periodo_inicial:
        periodo_inicial = periodo_final - timedelta(days=30)
    
    service = IndicadoresService(db)
    
    # Calcular indicadores
    ird = service.calcular_ird(periodo_inicial, periodo_final)
    ia = service.calcular_ia(periodo_inicial, periodo_final)
    if_valor = service.calcular_if(periodo_inicial, periodo_final)
    
    # Buscar IPT do banco de dados
    # Extrair mês/ano do período solicitado (ou do período final se for mais recente)
    periodo_ref = periodo_final if periodo_final else datetime.utcnow()
    mes_periodo = periodo_ref.month
    ano_periodo = periodo_ref.year
    
    # Primeiro tentar buscar IPT que intersecta com o período solicitado
    ipt_indicador = db.query(Indicador).filter(
        and_(
            Indicador.tipo == TipoIndicador.IPT,
            Indicador.periodo_inicial <= periodo_final,
            Indicador.periodo_final >= periodo_inicial,
            Indicador.subprefeitura.is_(None)
        )
    ).order_by(Indicador.calculated_at.desc()).first()
    
    # Se não encontrou, buscar IPT do mesmo mês/ano do período de referência
    if not ipt_indicador:
        inicio_mes_periodo = datetime(ano_periodo, mes_periodo, 1, 0, 0, 0)
        # Calcular fim do mês
        if mes_periodo == 12:
            fim_mes_periodo = datetime(ano_periodo + 1, 1, 1, 0, 0, 0)
        else:
            fim_mes_periodo = datetime(ano_periodo, mes_periodo + 1, 1, 0, 0, 0)
        
        ipt_indicador = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.periodo_inicial >= inicio_mes_periodo,
                Indicador.periodo_inicial < fim_mes_periodo,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
    
    # Se ainda não encontrou, buscar o IPT mais recente
    if not ipt_indicador:
        ipt_indicador = db.query(Indicador).filter(
            and_(
                Indicador.tipo == TipoIndicador.IPT,
                Indicador.subprefeitura.is_(None)
            )
        ).order_by(Indicador.calculated_at.desc()).first()
    
    ipt_valor = None
    ipt_pontuacao = None
    if ipt_indicador:
        ipt_valor = float(ipt_indicador.valor)
        ipt_pontuacao = float(ipt_indicador.pontuacao)
    
    # Contar SACs do dia
    from sqlalchemy import func
    hoje = datetime.utcnow().date()
    sacs_hoje = db.query(SAC).filter(
        func.date(SAC.data_criacao) == hoje
    ).count()
    
    # CNCs urgentes - usar a mesma lógica do endpoint /cnc/urgent
    agora = datetime.utcnow()
    cncs_pendentes = db.query(CNC).filter(CNC.status == StatusCNC.PENDENTE).all()
    cncs_urgentes_set = set()
    
    # Contar CNCs pendentes que estão urgentes (>= 50% do prazo usado)
    for cnc in cncs_pendentes:
        tempo_decorrido = (agora - cnc.data_abertura).total_seconds() / 3600
        percentual_usado = (tempo_decorrido / cnc.prazo_hours) * 100 if cnc.prazo_hours > 0 else 0
        
        if percentual_usado >= 50:  # Mais de 50% do prazo usado
            cncs_urgentes_set.add(cnc.id)
            # Atualizar status se necessário
            if percentual_usado >= 100:
                cnc.status = StatusCNC.URGENTE
    
    # Adicionar CNCs já marcados como urgentes
    cncs_ja_urgentes = db.query(CNC).filter(CNC.status == StatusCNC.URGENTE).all()
    for cnc in cncs_ja_urgentes:
        cncs_urgentes_set.add(cnc.id)
    
    cncs_urgentes_count = len(cncs_urgentes_set)
    
    db.commit()
    
    return {
        "indicadores": {
            "ird": ird,
            "ia": ia,
            "if": if_valor,
            "ipt": {
                "valor": ipt_valor,
                "pontuacao": ipt_pontuacao,
            } if ipt_valor is not None else None,
        },
        "sacs_hoje": sacs_hoje,
        "cncs_urgentes": cncs_urgentes_count,
        "periodo": {
            "inicial": periodo_inicial.isoformat() if isinstance(periodo_inicial, datetime) else periodo_inicial,
            "final": periodo_final.isoformat() if isinstance(periodo_final, datetime) else periodo_final,
        }
    }

