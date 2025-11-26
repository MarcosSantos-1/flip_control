"""Cálculos de indicadores ADC."""
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models.sac import SAC, TipoServico, StatusSAC, Subprefeitura
from app.models.cnc import CNC, StatusCNC
from app.models.indicador import Indicador, TipoIndicador
from app.models.acic import ACIC
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class IndicadoresService:
    """Serviço para cálculos de indicadores."""
    
    def __init__(self, db: Session):
        self.db = db
        self.TOTAL_DOMICILIOS = settings.TOTAL_DOMICILIOS
    
    def calcular_ird(
        self,
        periodo_inicial: datetime,
        periodo_final: datetime,
        subprefeitura: Optional[Subprefeitura] = None
    ) -> Dict[str, any]:
        """
        Calcula IRD (Índice de Reclamações Domiciliares).
        
        Fórmula: (reclamações escalonadas procedentes no mês / nº domicílios) × 1000
        
        Args:
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            subprefeitura: Subprefeitura (opcional, se None calcula geral)
            
        Returns:
            Dict com valor do IRD, pontuação e detalhes
        """
        # Tipos escalonados
        tipos_escalonados = [
            TipoServico.CATABAGULHO,
            TipoServico.VARRIACAO_COLETA,
            TipoServico.MUTIRAO,
            TipoServico.LAVAGEM,
            TipoServico.BUEIRO,
            TipoServico.VARRIACAO,
            TipoServico.VARRIACAO_PRACAS,
            TipoServico.MONUMENTOS,
            TipoServico.OUTROS,
        ]
        
        # Query base
        query = self.db.query(SAC).filter(
            and_(
                SAC.data_criacao >= periodo_inicial,
                SAC.data_criacao <= periodo_final,
                SAC.tipo_servico.in_(tipos_escalonados),
                SAC.status.in_([
                    StatusSAC.EXECUTADO,
                    StatusSAC.FINALIZADO,
                    StatusSAC.CONFIRMADA_EXECUCAO,
                ])
            )
        )
        
        # Filtrar por subprefeitura se especificado
        if subprefeitura:
            query = query.filter(SAC.subprefeitura == subprefeitura)
            domicilios = settings.DOMICILIOS_POR_SUBPREFEITURA.get(subprefeitura.value, self.TOTAL_DOMICILIOS)
        else:
            domicilios = self.TOTAL_DOMICILIOS
        
        # Contar reclamações procedentes
        total_reclamacoes = query.count()
        
        # Calcular IRD
        if domicilios > 0:
            ird = Decimal(total_reclamacoes) / Decimal(domicilios) * Decimal(1000)
            ird = ird.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        else:
            ird = Decimal(0)
        
        # Calcular pontuação conforme faixas
        pontuacao = self._calcular_pontuacao_ird(ird)
        
        return {
            "tipo": TipoIndicador.IRD,
            "valor": float(ird),
            "pontuacao": float(pontuacao),
            "total_reclamacoes": total_reclamacoes,
            "domicilios": domicilios,
             "tipos_considerados": [tipo.value for tipo in tipos_escalonados],
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
            "subprefeitura": subprefeitura.value if subprefeitura else None,
        }
    
    def calcular_ia(
        self,
        periodo_inicial: datetime,
        periodo_final: datetime,
        subprefeitura: Optional[Subprefeitura] = None
    ) -> Dict[str, any]:
        """
        Calcula IA (Índice de Atendimento).
        
        Fórmula: (solicitações demandantes atendidas no prazo / total demandantes procedentes) × 100
        
        Args:
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            subprefeitura: Subprefeitura (opcional)
            
        Returns:
            Dict com valor do IA, pontuação e detalhes
        """
        # Tipos demandantes
        tipos_demandantes = [
            TipoServico.ENTULHO,
            TipoServico.ANIMAL_MORTO,
            TipoServico.PAPELEIRAS,
        ]
        
        # Query para demandantes procedentes
        # IMPORTANTE: Considerar apenas registros com data_execucao para o cálculo de IA
        query_procedentes = self.db.query(SAC).filter(
            and_(
                SAC.data_criacao >= periodo_inicial,
                SAC.data_criacao <= periodo_final,
                SAC.tipo_servico.in_(tipos_demandantes),
                SAC.status.in_([
                    StatusSAC.EXECUTADO,
                    StatusSAC.FINALIZADO,
                    StatusSAC.CONFIRMADA_EXECUCAO,
                ]),
                # Apenas SACs com data_execucao podem ser considerados no cálculo de IA
                SAC.data_execucao.isnot(None),
            )
        )
        
        if subprefeitura:
            query_procedentes = query_procedentes.filter(SAC.subprefeitura == subprefeitura)
        
        total_procedentes = query_procedentes.count()
        
        # Query para atendidos no prazo
        # Considera apenas os que têm data_execucao e estão dentro do prazo
        query_no_prazo = query_procedentes.filter(
            func.extract('epoch', SAC.data_execucao - SAC.data_criacao) / 3600 <= SAC.prazo_max_hours
        )
        
        total_no_prazo = query_no_prazo.count()
        total_fora_prazo = max(total_procedentes - total_no_prazo, 0)
        
        # Calcular IA
        if total_procedentes > 0:
            ia = Decimal(total_no_prazo) / Decimal(total_procedentes) * Decimal(100)
            ia = ia.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            ia = Decimal(0)
        
        # Calcular pontuação
        pontuacao = self._calcular_pontuacao_ia(ia)
        
        return {
            "tipo": TipoIndicador.IA,
            "valor": float(ia),
            "pontuacao": float(pontuacao),
            "total_procedentes": total_procedentes,
            "total_no_prazo": total_no_prazo,
            "total_fora_prazo": total_fora_prazo,
            "tipos_considerados": [tipo.value for tipo in tipos_demandantes],
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
            "subprefeitura": subprefeitura.value if subprefeitura else None,
        }
    
    def calcular_if(
        self,
        periodo_inicial: datetime,
        periodo_final: datetime,
        subprefeitura: Optional[Subprefeitura] = None
    ) -> Dict[str, any]:
        """
        Calcula IF (Índice de Fiscalização).
        
        Fórmula: (nº de fiscalizações sem irregularidade / total fiscalizações) × 100
        
        Args:
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            subprefeitura: Subprefeitura (opcional)
            
        Returns:
            Dict com valor do IF, pontuação e detalhes
        """
        # Query base para CNCs no período
        query = self.db.query(CNC).filter(
            and_(
                CNC.data_abertura >= periodo_inicial,
                CNC.data_abertura <= periodo_final,
            )
        )
        
        if subprefeitura:
            # Converter subprefeitura para string para comparar
            subpref_map = {
                Subprefeitura.CV: "Casa Verde/Cachoeirinha",
                Subprefeitura.JT: "Jaçanã/Tremembé",
                Subprefeitura.ST: "Santana/Tucuruvi",
                Subprefeitura.MG: "Vila Maria/Vila Guilherme",
            }
            query = query.filter(CNC.subprefeitura == subpref_map.get(subprefeitura))
        
        total_fiscalizacoes = query.count()
        
        # Fiscalizações sem irregularidade (status Regularizado)
        query_sem_irregularidade = query.filter(CNC.status == StatusCNC.REGULARIZADO)
        total_sem_irregularidade = query_sem_irregularidade.count()
        
        # Calcular IF
        if total_fiscalizacoes > 0:
            if_valor = Decimal(total_sem_irregularidade) / Decimal(total_fiscalizacoes) * Decimal(100)
            if_valor = if_valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            if_valor = Decimal(0)
        
        # Calcular pontuação
        pontuacao = self._calcular_pontuacao_if(if_valor)
        
        return {
            "tipo": TipoIndicador.IF,
            "valor": float(if_valor),
            "pontuacao": float(pontuacao),
            "total_fiscalizacoes": total_fiscalizacoes,
            "total_sem_irregularidade": total_sem_irregularidade,
            "status_referencia": StatusCNC.REGULARIZADO.value,
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
            "subprefeitura": subprefeitura.value if subprefeitura else None,
        }
    
    def calcular_ipt(
        self,
        periodo_inicial: datetime,
        periodo_final: datetime,
        valor_mao_obra: Decimal,
        valor_equipamentos: Decimal
    ) -> Dict[str, any]:
        """
        Calcula IPT (Índice de Execução dos Planos de Trabalho).
        
        Fórmula: média ponderada (mão de obra 50% + equipamentos 50%)
        
        Args:
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            valor_mao_obra: Valor de execução de mão de obra (0-100)
            valor_equipamentos: Valor de execução de equipamentos (0-100)
            
        Returns:
            Dict com valor do IPT, pontuação e detalhes
        """
        # Calcular IPT
        ipt = (valor_mao_obra * Decimal(0.5)) + (valor_equipamentos * Decimal(0.5))
        ipt = ipt.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calcular pontuação
        pontuacao = self._calcular_pontuacao_ipt(ipt)
        
        return {
            "tipo": TipoIndicador.IPT,
            "valor": float(ipt),
            "pontuacao": float(pontuacao),
            "valor_mao_obra": float(valor_mao_obra),
            "valor_equipamentos": float(valor_equipamentos),
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
        }
    
    def calcular_adc(
        self,
        periodo_inicial: datetime,
        periodo_final: datetime,
        valor_ipt: Optional[Decimal] = None,
        valor_mao_obra: Optional[Decimal] = None,
        valor_equipamentos: Optional[Decimal] = None,
        subprefeitura: Optional[Subprefeitura] = None
    ) -> Dict[str, any]:
        """
        Calcula ADC (Avaliação de Desempenho da Contratada).
        
        ADC = IRD + IA + IF + IPT
        
        Args:
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            valor_ipt: Valor do IPT (se já calculado)
            valor_mao_obra: Valor de mão de obra para calcular IPT
            valor_equipamentos: Valor de equipamentos para calcular IPT
            subprefeitura: Subprefeitura (opcional)
            
        Returns:
            Dict com valor do ADC, pontuação total e detalhes
        """
        # Calcular indicadores
        ird_result = self.calcular_ird(periodo_inicial, periodo_final, subprefeitura)
        ia_result = self.calcular_ia(periodo_inicial, periodo_final, subprefeitura)
        if_result = self.calcular_if(periodo_inicial, periodo_final, subprefeitura)
        
        # Calcular IPT
        ipt_valor_info = None
        if valor_ipt is not None:
            ipt_pontuacao = float(self._calcular_pontuacao_ipt(Decimal(str(valor_ipt))))
            ipt_valor_info = float(valor_ipt)
        elif valor_mao_obra is not None and valor_equipamentos is not None:
            ipt_result = self.calcular_ipt(periodo_inicial, periodo_final, valor_mao_obra, valor_equipamentos)
            ipt_pontuacao = ipt_result["pontuacao"]
            ipt_valor_info = ipt_result["valor"]
        else:
            ipt_pontuacao = 0
            ipt_valor_info = None
        
        # Soma das pontuações
        pontuacao_total = (
            ird_result["pontuacao"] +
            ia_result["pontuacao"] +
            if_result["pontuacao"] +
            ipt_pontuacao
        )
        
        # Calcular percentual do contrato e desconto
        percentual_contrato, desconto = self._calcular_desconto_contrato(pontuacao_total)
        
        resultado = {
            "tipo": TipoIndicador.ADC,
            "pontuacao_total": pontuacao_total,
            "ird": ird_result,
            "ia": ia_result,
            "if": if_result,
            "ipt_pontuacao": ipt_pontuacao,
            "percentual_contrato": percentual_contrato,
            "desconto": desconto,
            "periodo_inicial": periodo_inicial,
            "periodo_final": periodo_final,
            "subprefeitura": subprefeitura.value if subprefeitura else None,
        }
        
        # Adicionar informações do IPT se disponível
        if ipt_valor_info is not None:
            resultado["ipt"] = {
                "valor": ipt_valor_info,
                "pontuacao": ipt_pontuacao,
            }
        
        return resultado
    
    def _calcular_pontuacao_ird(self, ird: Decimal) -> Decimal:
        """Calcula pontuação do IRD conforme faixas."""
        if ird <= Decimal("1.0"):
            return Decimal("20")
        elif ird <= Decimal("2.0"):
            return Decimal("15")
        elif ird <= Decimal("5.0"):
            return Decimal("10")
        elif ird <= Decimal("10.0"):
            return Decimal("5")
        else:
            return Decimal("0")
    
    def _calcular_pontuacao_ia(self, ia: Decimal) -> Decimal:
        """Calcula pontuação do IA conforme faixas."""
        if ia >= Decimal("90"):
            return Decimal("20")
        elif ia >= Decimal("80"):
            return Decimal("16")
        elif ia >= Decimal("70"):
            return Decimal("12")
        elif ia >= Decimal("60"):
            return Decimal("8")
        elif ia >= Decimal("50"):
            return Decimal("4")
        else:
            return Decimal("0")
    
    def _calcular_pontuacao_if(self, if_valor: Decimal) -> Decimal:
        """Calcula pontuação do IF conforme faixas."""
        if if_valor >= Decimal("90"):
            return Decimal("20")
        elif if_valor >= Decimal("80"):
            return Decimal("18")
        elif if_valor >= Decimal("70"):
            return Decimal("16")
        elif if_valor >= Decimal("60"):
            return Decimal("14")
        elif if_valor >= Decimal("50"):
            return Decimal("12")
        elif if_valor >= Decimal("40"):
            return Decimal("10")
        elif if_valor >= Decimal("30"):
            return Decimal("8")
        elif if_valor >= Decimal("20"):
            return Decimal("6")
        elif if_valor >= Decimal("10"):
            return Decimal("4")
        else:
            return Decimal("0")
    
    def _calcular_pontuacao_ipt(self, ipt: Decimal) -> Decimal:
        """Calcula pontuação do IPT conforme faixas."""
        if ipt >= Decimal("90"):
            return Decimal("40")
        elif ipt >= Decimal("80"):
            return Decimal("38")
        elif ipt >= Decimal("70"):
            return Decimal("36")
        elif ipt >= Decimal("60"):
            return Decimal("32")
        elif ipt >= Decimal("50"):
            return Decimal("28")
        elif ipt >= Decimal("40"):
            return Decimal("24")
        elif ipt >= Decimal("30"):
            return Decimal("20")
        elif ipt >= Decimal("20"):
            return Decimal("16")
        elif ipt >= Decimal("10"):
            return Decimal("12")
        else:
            return Decimal("0")
    
    def _calcular_desconto_contrato(self, pontuacao_total: float) -> tuple:
        """
        Calcula percentual do contrato e desconto baseado na pontuação.
        
        Returns:
            Tuple (percentual_contrato, desconto)
        """
        if pontuacao_total >= 90:
            return (100.0, 0.0)
        elif pontuacao_total >= 70:
            # Redução de 0,20% por ponto abaixo de 90, até limite de 95%
            pontos_abaixo = 90 - pontuacao_total
            desconto = pontos_abaixo * 0.20
            percentual = max(95.0, 100.0 - desconto)
            return (percentual, desconto)
        elif pontuacao_total >= 50:
            # Redução de 0,25% por ponto abaixo de 70, até limite de 90%
            pontos_abaixo = 70 - pontuacao_total
            desconto_base = (90 - 70) * 0.20  # Desconto da faixa anterior
            desconto = desconto_base + (pontos_abaixo * 0.25)
            percentual = max(90.0, 100.0 - desconto)
            return (percentual, desconto)
        elif pontuacao_total >= 30:
            # Redução de 0,5% por ponto abaixo de 50, até limite de 80%
            pontos_abaixo = 50 - pontuacao_total
            desconto_base = (90 - 50) * 0.20 + (50 - 30) * 0.25  # Descontos anteriores
            desconto = desconto_base + (pontos_abaixo * 0.5)
            percentual = max(80.0, 100.0 - desconto)
            return (percentual, desconto)
        else:
            # Abaixo de 30 pontos: 70% do valor mensal
            return (70.0, 30.0)
    
    def salvar_indicador(self, resultado: Dict[str, any]) -> Indicador:
        """Salva indicador calculado no banco."""
        indicador = Indicador(
            tipo=resultado["tipo"],
            valor=Decimal(str(resultado["valor"])),
            pontuacao=Decimal(str(resultado["pontuacao"])),
            periodo_inicial=resultado["periodo_inicial"],
            periodo_final=resultado["periodo_final"],
            subprefeitura=resultado.get("subprefeitura"),
            detalhes=str(resultado) if resultado.get("detalhes") is None else resultado["detalhes"],
        )
        
        self.db.add(indicador)
        self.db.commit()
        self.db.refresh(indicador)
        
        return indicador

