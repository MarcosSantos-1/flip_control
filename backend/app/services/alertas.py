"""Sistema de alertas."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.sac import SAC, TipoServico, StatusSAC
from app.models.cnc import CNC, StatusCNC
import logging

logger = logging.getLogger(__name__)


class AlertasService:
    """Serviço para geração de alertas."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verificar_alertas(self) -> Dict[str, List[Dict[str, Any]]]:
        """Verifica todos os alertas do sistema."""
        return {
            "sacs_demandantes_urgentes": self._alertas_sacs_demandantes(),
            "sacs_atrasados": self._alertas_sacs_atrasados(),
            "cncs_urgentes": self._alertas_cncs_urgentes(),
            "fotos_ausentes": self._alertas_fotos_ausentes(),
            "erros_regionais": self._alertas_erros_regionais(),
        }
    
    def _alertas_sacs_demandantes(self) -> List[Dict[str, Any]]:
        """SACs demandantes > 24h sem vistoria."""
        agora = datetime.utcnow()
        limite = agora - timedelta(hours=24)
        
        sacs = self.db.query(SAC).filter(
            and_(
                SAC.tipo_servico.in_([TipoServico.ENTULHO, TipoServico.ANIMAL_MORTO]),
                SAC.status == StatusSAC.AGUARDANDO_ANALISE,
                SAC.data_criacao < limite
            )
        ).all()
        
        return [
            {
                "sac_id": str(sac.id),
                "protocolo": sac.protocolo,
                "tipo": "demandante_urgente",
                "mensagem": f"SAC {sac.protocolo} aguardando vistoria há mais de 24h",
                "horas_aguardando": int((agora - sac.data_criacao).total_seconds() / 3600),
            }
            for sac in sacs
        ]
    
    def _alertas_sacs_atrasados(self) -> List[Dict[str, Any]]:
        """SACs agendados > 72h sem execução."""
        agora = datetime.utcnow()
        limite = agora - timedelta(hours=72)
        
        sacs = self.db.query(SAC).filter(
            and_(
                SAC.data_agendamento.isnot(None),
                SAC.status == StatusSAC.EM_EXECUCAO,
                SAC.data_agendamento < limite
            )
        ).all()
        
        return [
            {
                "sac_id": str(sac.id),
                "protocolo": sac.protocolo,
                "tipo": "atrasado",
                "mensagem": f"SAC {sac.protocolo} agendado há mais de 72h sem execução",
                "horas_atrasado": int((agora - sac.data_agendamento).total_seconds() / 3600),
            }
            for sac in sacs
        ]
    
    def _alertas_cncs_urgentes(self) -> List[Dict[str, Any]]:
        """CNCs próximas do prazo (50% ou mais)."""
        agora = datetime.utcnow()
        cncs_urgentes = []
        
        cncs = self.db.query(CNC).filter(
            CNC.status == StatusCNC.PENDENTE
        ).all()
        
        for cnc in cncs:
            tempo_decorrido = (agora - cnc.data_abertura).total_seconds() / 3600
            percentual_usado = (tempo_decorrido / cnc.prazo_hours) * 100 if cnc.prazo_hours > 0 else 0
            
            if percentual_usado >= 50:
                cncs_urgentes.append({
                    "cnc_id": str(cnc.id),
                    "bfs": cnc.bfs,
                    "tipo": "cnc_urgente",
                    "mensagem": f"CNC {cnc.bfs} com {percentual_usado:.1f}% do prazo usado",
                    "percentual_usado": round(percentual_usado, 1),
                    "horas_restantes": max(0, cnc.prazo_hours - tempo_decorrido),
                })
        
        return cncs_urgentes
    
    def _alertas_fotos_ausentes(self) -> List[Dict[str, Any]]:
        """SACs executados sem fotos."""
        sacs = self.db.query(SAC).filter(
            SAC.status.in_([
                StatusSAC.EXECUTADO,
                StatusSAC.CONFIRMADA_EXECUCAO,
            ])
        ).all()
        
        alertas = []
        for sac in sacs:
            if not sac.fotos_before or not sac.fotos_after:
                alertas.append({
                    "sac_id": str(sac.id),
                    "protocolo": sac.protocolo,
                    "tipo": "fotos_ausentes",
                    "mensagem": f"SAC {sac.protocolo} executado sem fotos antes/depois",
                    "fotos_before": bool(sac.fotos_before),
                    "fotos_after": bool(sac.fotos_after),
                })
        
        return alertas
    
    def _alertas_erros_regionais(self) -> List[Dict[str, Any]]:
        """SACs com flag de erro regional."""
        sacs = self.db.query(SAC).filter(
            SAC.flag_erro_regional == True
        ).all()
        
        return [
            {
                "sac_id": str(sac.id),
                "protocolo": sac.protocolo,
                "tipo": "erro_regional",
                "mensagem": f"SAC {sac.protocolo} com possível erro de regional",
                "subprefeitura": sac.subprefeitura.value,
            }
            for sac in sacs
        ]

