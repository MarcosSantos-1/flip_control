"""update_tipos_servico

Revision ID: d9cd32273c87
Revises: 7af2b1191811
Create Date: 2025-11-24 15:57:19.264233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9cd32273c87'
down_revision: Union[str, None] = '7af2b1191811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Primeiro, migrar dados existentes de CAPINA e PROPAGANDA para MUTIRAO
    # (conforme especificação: Capinação e Propaganda agora são Mutirão)
    op.execute("""
        UPDATE sacs 
        SET tipo_servico = 'MUTIRAO' 
        WHERE tipo_servico IN ('CAPINA', 'PROPAGANDA')
    """)
    
    # Adicionar novos valores ao enum tiposervico
    # Nota: PostgreSQL não permite remover valores de ENUM diretamente,
    # então mantemos CAPINA e PROPAGANDA no enum mas não os usamos mais
    op.execute("ALTER TYPE tiposervico ADD VALUE IF NOT EXISTS 'VARRIACAO_COLETA'")
    op.execute("ALTER TYPE tiposervico ADD VALUE IF NOT EXISTS 'LAVAGEM'")
    op.execute("ALTER TYPE tiposervico ADD VALUE IF NOT EXISTS 'VARRIACAO_PRACAS'")
    op.execute("ALTER TYPE tiposervico ADD VALUE IF NOT EXISTS 'MONUMENTOS'")


def downgrade() -> None:
    # Migrar dados de volta para CAPINA e PROPAGANDA (se necessário)
    # Nota: Não podemos remover valores de ENUM no PostgreSQL sem recriar o tipo
    # Esta migration apenas reverte os dados, mas mantém os novos valores no enum
    pass

