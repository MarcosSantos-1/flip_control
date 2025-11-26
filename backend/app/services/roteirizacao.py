"""Serviço de roteirização."""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
import math

from app.models.sac import SAC
from app.models.fiscal import Fiscal

try:
    from sklearn.cluster import DBSCAN
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class RoteirizacaoService:
    """Serviço para geração de rotas otimizadas."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def gerar_roteiro(
        self,
        sac_ids: List[UUID],
        fiscal_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Gera roteiro otimizado para uma lista de SACs.
        
        Args:
            sac_ids: Lista de IDs dos SACs
            fiscal_id: ID do fiscal (opcional)
            
        Returns:
            Dict com roteiro otimizado
        """
        # Buscar SACs
        sacs = self.db.query(SAC).filter(SAC.id.in_(sac_ids)).all()
        
        if not sacs:
            return {"roteiro": [], "total": 0, "distancia_total": 0}
        
        # Filtrar SACs com coordenadas
        sacs_com_coords = [s for s in sacs if s.lat and s.lng]
        
        if not sacs_com_coords:
            return {"roteiro": [], "total": 0, "distancia_total": 0, "erro": "Nenhum SAC com coordenadas"}
        
        # Clusterização por subprefeitura
        clusters = self._clusterizar_por_subprefeitura(sacs_com_coords)
        
        # Ordenar por prioridade
        sacs_ordenados = self._ordenar_por_prioridade(sacs_com_coords)
        
        # Gerar rota usando nearest neighbor
        rota = self._nearest_neighbor(sacs_ordenados, fiscal_id)
        
        # Otimizar com 2-opt
        rota_otimizada = self._otimizar_2opt(rota)
        
        # Calcular distâncias
        distancia_total = self._calcular_distancia_total(rota_otimizada)
        
        return {
            "roteiro": [
                {
                    "ordem": i + 1,
                    "sac_id": str(sac.id),
                    "protocolo": sac.protocolo,
                    "endereco": sac.endereco_text,
                    "lat": sac.lat,
                    "lng": sac.lng,
                    "tipo_servico": sac.tipo_servico.value,
                    "prazo_horas": sac.prazo_max_hours,
                }
                for i, sac in enumerate(rota_otimizada)
            ],
            "total": len(rota_otimizada),
            "distancia_total_km": round(distancia_total, 2),
            "tempo_estimado_horas": round(len(rota_otimizada) * 0.5, 1),  # 30 min por SAC
        }
    
    def _clusterizar_por_subprefeitura(self, sacs: List[SAC]) -> Dict[str, List[SAC]]:
        """Agrupa SACs por subprefeitura."""
        clusters = {}
        for sac in sacs:
            subpref = sac.subprefeitura.value
            if subpref not in clusters:
                clusters[subpref] = []
            clusters[subpref].append(sac)
        return clusters
    
    def _ordenar_por_prioridade(self, sacs: List[SAC]) -> List[SAC]:
        """Ordena SACs por prioridade."""
        from app.models.sac import TipoServico
        
        def prioridade(sac: SAC) -> int:
            # Urgente: animal morto ou entulho próximo do prazo
            if sac.tipo_servico == TipoServico.ANIMAL_MORTO:
                return 1
            elif sac.tipo_servico == TipoServico.ENTULHO:
                return 2
            elif sac.tipo_servico in [TipoServico.VARRIACAO, TipoServico.BUEIRO]:
                return 3
            else:
                return 4
        
        return sorted(sacs, key=prioridade)
    
    def _nearest_neighbor(
        self,
        sacs: List[SAC],
        fiscal_id: Optional[UUID] = None
    ) -> List[SAC]:
        """Algoritmo nearest neighbor para gerar rota."""
        if not sacs:
            return []
        
        # Ponto inicial (última localização do fiscal ou primeiro SAC)
        if fiscal_id:
            fiscal = self.db.query(Fiscal).filter(Fiscal.id == fiscal_id).first()
            if fiscal and fiscal.last_location_lat and fiscal.last_location_lng:
                inicio = (fiscal.last_location_lat, fiscal.last_location_lng)
            else:
                inicio = (sacs[0].lat, sacs[0].lng)
        else:
            inicio = (sacs[0].lat, sacs[0].lng)
        
        rota = []
        nao_visitados = sacs.copy()
        atual = inicio
        
        while nao_visitados:
            # Encontrar SAC mais próximo
            mais_proximo = None
            menor_distancia = float('inf')
            
            for sac in nao_visitados:
                if sac.lat and sac.lng:
                    distancia = self._haversine(
                        atual[0], atual[1],
                        sac.lat, sac.lng
                    )
                    if distancia < menor_distancia:
                        menor_distancia = distancia
                        mais_proximo = sac
            
            if mais_proximo:
                rota.append(mais_proximo)
                nao_visitados.remove(mais_proximo)
                atual = (mais_proximo.lat, mais_proximo.lng)
            else:
                break
        
        return rota
    
    def _otimizar_2opt(self, rota: List[SAC]) -> List[SAC]:
        """Otimização 2-opt para melhorar a rota."""
        if len(rota) < 4:
            return rota
        
        melhor_rota = rota.copy()
        melhor_distancia = self._calcular_distancia_total(rota)
        melhorou = True
        
        while melhorou:
            melhorou = False
            for i in range(1, len(melhor_rota) - 2):
                for j in range(i + 1, len(melhor_rota)):
                    if j - i == 1:
                        continue
                    
                    # Tentar swap
                    nova_rota = melhor_rota[:i] + melhor_rota[i:j+1][::-1] + melhor_rota[j+1:]
                    nova_distancia = self._calcular_distancia_total(nova_rota)
                    
                    if nova_distancia < melhor_distancia:
                        melhor_rota = nova_rota
                        melhor_distancia = nova_distancia
                        melhorou = True
        
        return melhor_rota
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos usando fórmula de Haversine."""
        R = 6371  # Raio da Terra em km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        
        c = 2 * math.asin(math.sqrt(a))
        distancia = R * c
        
        return distancia
    
    def _calcular_distancia_total(self, rota: List[SAC]) -> float:
        """Calcula distância total da rota em km."""
        if len(rota) < 2:
            return 0.0
        
        distancia_total = 0.0
        for i in range(len(rota) - 1):
            sac1 = rota[i]
            sac2 = rota[i + 1]
            if sac1.lat and sac1.lng and sac2.lat and sac2.lng:
                distancia_total += self._haversine(
                    sac1.lat, sac1.lng,
                    sac2.lat, sac2.lng
                )
        
        return distancia_total

