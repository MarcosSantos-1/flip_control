"""Models do banco de dados."""
from app.models.sac import SAC
from app.models.cnc import CNC
from app.models.acic import ACIC
from app.models.ouvidoria import Ouvidoria
from app.models.fiscal import Fiscal
from app.models.indicador import Indicador
from app.models.log_status import LogStatus

__all__ = [
    "SAC",
    "CNC",
    "ACIC",
    "Ouvidoria",
    "Fiscal",
    "Indicador",
    "LogStatus",
]

