"""Validações de dados."""
from datetime import datetime
from typing import Optional
import re


def validar_cpf(cpf: str) -> bool:
    """Valida CPF (formato básico)."""
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf_limpo = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf_limpo) != 11:
        return False
    
    # Verifica se não é sequência repetida
    if cpf_limpo == cpf_limpo[0] * 11:
        return False
    
    return True


def validar_telefone(telefone: str) -> bool:
    """Valida telefone (formato básico)."""
    if not telefone:
        return False
    
    # Remove caracteres não numéricos
    telefone_limpo = re.sub(r'\D', '', telefone)
    
    # Verifica se tem entre 10 e 11 dígitos
    return 10 <= len(telefone_limpo) <= 11


def parse_data_brasil(data_str: str) -> Optional[datetime]:
    """
    Parse de data no formato brasileiro DD/MM/YYYY HH:MM:SS.
    
    Args:
        data_str: String no formato "01/11/2025 04:52:48"
        
    Returns:
        datetime ou None se inválido
    """
    if not data_str or not data_str.strip():
        return None
    
    try:
        # Remove espaços extras
        data_str = data_str.strip()
        
        # Formato com hora
        if len(data_str) > 10:
            return datetime.strptime(data_str, "%d/%m/%Y %H:%M:%S")
        else:
            # Apenas data
            return datetime.strptime(data_str, "%d/%m/%Y")
    except (ValueError, AttributeError):
        return None


def normalizar_subprefeitura(subpref: str) -> Optional[str]:
    """
    Normaliza nome de subprefeitura para código.
    
    Args:
        subpref: Nome da subprefeitura
        
    Returns:
        Código (CV, JT, ST, MG) ou None
    """
    if not subpref:
        return None
    
    subpref_upper = subpref.upper()
    
    if "CASA VERDE" in subpref_upper or "CACHOEIRINHA" in subpref_upper:
        return "CV"
    elif "JAÇANÃ" in subpref_upper or "TREMEMBÉ" in subpref_upper:
        return "JT"
    elif "SANTANA" in subpref_upper or "TUCURUVI" in subpref_upper:
        return "ST"
    elif "VILA MARIA" in subpref_upper or "VILA GUILHERME" in subpref_upper:
        return "MG"
    
    return None


def calcular_prazo_max_hours(tipo_servico: str, responsividade: Optional[int] = None) -> int:
    """
    Calcula prazo máximo em horas baseado no tipo de serviço.
    
    Args:
        tipo_servico: Tipo do serviço
        responsividade: Responsividade do CSV (se disponível)
        
    Returns:
        Prazo em horas
    """
    if responsividade:
        return responsividade
    
    tipo_lower = tipo_servico.lower()
    
    # IMPORTANTE: Verificar Escalonados ANTES dos Demandantes
    # Cata-Bagulho (Escalonado) - prazo de 720h (30 dias), não importa o prazo de vistoria
    if "cata-bagulho" in tipo_lower or "cata bagulho" in tipo_lower:
        return 720  # 30 dias - Escalonado, não importa prazo
    elif "coleta programada" in tipo_lower:
        return 720  # 30 dias - Cata-Bagulho (Escalonado)
    
    # Demandantes (com responsividade específica)
    # Coleta e transporte de entulho (NÃO programada = Demandante)
    elif ("coleta e transporte" in tipo_lower or "coleta de entulho" in tipo_lower) and \
         ("entulho" in tipo_lower or "grandes objetos" in tipo_lower) and \
         "programada" not in tipo_lower:
        return 72  # 72h - Demandante
    elif ("entulho" in tipo_lower or "grandes objetos" in tipo_lower) and \
         "programada" not in tipo_lower:
        return 72  # 72h - Demandante
    elif "animal" in tipo_lower and "morto" in tipo_lower:
        return 12  # 12h - Demandante
    elif "papeleira" in tipo_lower or "lixeira" in tipo_lower or "equipamentos de recepção" in tipo_lower:
        return 72  # 72h conforme especificação - Demandante
    
    # Escalonados (agendados para até 1 mês = 720h)
    elif ("varrição" in tipo_lower or 
          "bueiro" in tipo_lower or 
          "capinação" in tipo_lower or 
          "mutirão" in tipo_lower or
          "lavagem" in tipo_lower or
          "monumento" in tipo_lower):
        return 720  # 30 dias para escalonados
    else:
        return 720  # 30 dias padrão para escalonados/outros

