"""fix_catabagulho_misclassified_as_entulho

Revision ID: d374546b1978
Revises: d9cd32273c87
Create Date: 2025-11-24 16:09:11.986684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd374546b1978'
down_revision: Union[str, None] = 'd9cd32273c87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Correção: SACs de Cata-Bagulho que foram classificados incorretamente como 'entulho'.
    
    PROBLEMA IDENTIFICADO:
    - SACs com tipo "Coleta programada e transporte de objetos volumosos e de entulho (Cata-Bagulho)"
      estavam sendo classificados como ENTULHO (Demandante) quando deveriam ser CATABAGULHO (Escalonado)
    - Isso causava marcação incorreta de "fora do prazo" para serviços escalonados
    
    SOLUÇÃO IMPLEMENTADA:
    - A lógica de parse foi corrigida para verificar "cata-bagulho" ANTES de "entulho"
    - Novos SACs processados serão classificados corretamente
    
    NOTA: Para corrigir dados existentes, seria necessário:
    1. Reprocessar os CSVs originais com a nova lógica, OU
    2. Executar uma query manual baseada em heurísticas (ex: prazo_max_hours = 5h pode indicar Cata-Bagulho)
    
    Query SQL de exemplo para correção manual (executar com cuidado após validação):
    
    UPDATE sacs 
    SET tipo_servico = 'CATABAGULHO' 
    WHERE tipo_servico = 'ENTULHO' 
      AND prazo_max_hours = 5
      AND (endereco_text ILIKE '%cata%bagulho%' OR endereco_text ILIKE '%programada%');
    
    IMPORTANTE: Esta query é apenas um exemplo. Valide os resultados antes de executar em produção.
    """
    # Migration vazia - a correção foi feita na lógica de parse
    # Novos dados serão classificados corretamente automaticamente
    pass


def downgrade() -> None:
    # Não há downgrade necessário - apenas a lógica de parse foi alterada
    pass

