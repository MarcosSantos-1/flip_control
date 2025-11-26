"""Configurações da aplicação."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Database
    DATABASE_URL: str
    
    # Server
    PORT: int = 8000
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Geocoding
    GEOCODING_API_KEY: str = ""
    GEOCODING_PROVIDER: str = "nominatim"  # nominatim ou google
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Constantes do sistema
    TOTAL_DOMICILIOS: int = 511093  # Base IBGE 2024
    DOMICILIOS_POR_SUBPREFEITURA: dict = {
        "CV": 130030,  # Casa Verde/Cachoeirinha
        "JT": 112924,  # Jaçanã/Tremembé
        "ST": 147969,  # Santana/Tucuruvi
        "MG": 120170,  # Vila Maria/Vila Guilherme
    }
    
    # Prazos por tipo de serviço (em horas)
    # IMPORTANTE: Chaves devem corresponder aos valores do enum (MAIÚSCULAS)
    PRAZOS_SERVICO: dict = {
        "ENTULHO": 72,
        "ANIMAL_MORTO": 12,
        "PAPELEIRAS": 72,  # 72h conforme especificação
        "escalonado": 720,  # 30 dias
    }
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

