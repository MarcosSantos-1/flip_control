"""Utilitários para geocoding."""
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging

logger = logging.getLogger(__name__)


def geocode_endereco(endereco: str, max_retries: int = 3) -> Optional[Tuple[float, float]]:
    """
    Faz geocoding de um endereço usando Nominatim (gratuito).
    
    Args:
        endereco: Endereço completo
        max_retries: Número máximo de tentativas
        
    Returns:
        Tupla (lat, lng) ou None se não conseguir geocodificar
    """
    if not endereco or not endereco.strip():
        return None
    
    geolocator = Nominatim(user_agent="adc_flip_app")
    
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(endereco, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Erro no geocoding (tentativa {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
            else:
                logger.error(f"Falha no geocoding após {max_retries} tentativas")
                return None
        except Exception as e:
            logger.error(f"Erro inesperado no geocoding: {e}")
            return None
    
    return None


def parse_coordenadas(coordenada_str: str) -> Optional[Tuple[float, float]]:
    """
    Parse de string de coordenadas no formato "lat,lng".
    
    Args:
        coordenada_str: String no formato "-23.4726589,-46.6620801"
        
    Returns:
        Tupla (lat, lng) ou None se inválido
    """
    if not coordenada_str or not coordenada_str.strip():
        return None
    
    try:
        parts = coordenada_str.strip().split(",")
        if len(parts) != 2:
            return None
        
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        
        # Validação básica (São Paulo está aproximadamente entre essas coordenadas)
        if -24.0 <= lat <= -23.0 and -47.0 <= lng <= -46.0:
            return (lat, lng)
        
        return None
    except (ValueError, AttributeError):
        return None

