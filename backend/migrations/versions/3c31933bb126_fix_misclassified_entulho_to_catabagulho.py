"""fix_misclassified_entulho_to_catabagulho

Revision ID: 3c31933bb126
Revises: d374546b1978
Create Date: 2025-11-24 16:37:31.987920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c31933bb126'
down_revision: Union[str, None] = 'd374546b1978'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Correção: SACs de Cata-Bagulho classificados incorretamente como ENTULHO.
    
    PROBLEMA:
    - SACs com tipo "Coleta programada e transporte de objetos volumosos e de entulho (Cata-Bagulho)"
      estavam sendo classificados como ENTULHO (Demandante) quando deveriam ser CATABAGULHO (Escalonado)
    - Isso causava marcação incorreta de "fora do prazo" e afetava o ADC
    
    HEURÍSTICA DE CORREÇÃO:
    - SACs classificados como ENTULHO com prazo_max_hours = 5 são provavelmente Cata-Bagulho
      (Cata-Bagulho tem responsividade de 5h para vistoria, mas prazo total é 30 dias)
    - Coleta (Demandante) tem prazo de 72h
    
    IMPORTANTE: Esta é uma correção baseada em heurística. Para correção completa e precisa,
    recomenda-se reprocessar os CSVs originais com a nova lógica de parse.
    """
    # Corrigir SACs classificados como ENTULHO mas que são Cata-Bagulho
    # Heurística: ENTULHO com prazo de 5h = provavelmente Cata-Bagulho
    op.execute("""
        UPDATE sacs 
        SET tipo_servico = 'CATABAGULHO',
            prazo_max_hours = 720
        WHERE tipo_servico = 'ENTULHO' 
          AND prazo_max_hours = 5
    """)


def downgrade() -> None:
    # Não há downgrade seguro - seria necessário o texto original do serviço
    pass

