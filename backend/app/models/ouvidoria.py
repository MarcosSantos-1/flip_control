"""Model para Ouvidorias."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class StatusOuvidoria(str, enum.Enum):
    """Status das Ouvidorias."""
    EM_EXECUCAO = "Em Execução"
    OUVIDORIA_ENCERRADA = "Ouvidoria Encerrada"
    FINALIZADO = "Finalizado"
    EXECUTADO = "Executado"
    CONFIRMAR_EXECUCAO = "Confirmar Execução"


class Ouvidoria(Base):
    """Model para Ouvidorias."""
    __tablename__ = "ouvidorias"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_chamado = Column(String, unique=True, nullable=False, index=True)
    numero_sei = Column(String, nullable=True)
    
    # Relacionamento com SAC
    sac_id = Column(UUID(as_uuid=True), ForeignKey("sacs.id"), nullable=True)
    
    # Status
    status = Column(Enum(StatusOuvidoria), nullable=True)
    situacao = Column(String, nullable=True)
    
    # Informações
    contratada = Column(String, nullable=True)
    origem = Column(String, nullable=True)
    procedente = Column(String, nullable=True)
    procedente_por_status = Column(String, nullable=True)
    finalizado_como_fora_de_escopo = Column(String, nullable=True)
    
    # Localização
    regional = Column(String, nullable=True)
    area = Column(String, nullable=True)
    servico = Column(String, nullable=True)
    assunto = Column(String, nullable=True)
    endereco = Column(String, nullable=True)
    coordenadas = Column(String, nullable=True)
    
    # Datas
    data_extracao_pdf = Column(DateTime, nullable=True)
    data_alteracao_sac = Column(DateTime, nullable=True)
    data_sincronizacao = Column(DateTime, nullable=True)
    data_registro = Column(DateTime, nullable=True)
    data_acao_de_agendar = Column(DateTime, nullable=True)
    data_acionamento_agendamento = Column(DateTime, nullable=True)
    data_acionamento_revistoria = Column(DateTime, nullable=True)
    data_realizacao_vistoria = Column(DateTime, nullable=True)
    data_acionamento_confirmacao_execucao = Column(DateTime, nullable=True)
    data_realizacao_confirmacao_execucao = Column(DateTime, nullable=True)
    data_execucao = Column(DateTime, nullable=True)
    data_ultima_atualizacao = Column(DateTime, nullable=True)
    
    # Responsividade
    responsividade = Column(String, nullable=True)
    responsividade_resposta = Column(String, nullable=True)
    responsividade_execucao = Column(String, nullable=True)
    sac_publicacao_no_prazo = Column(String, nullable=True)
    
    # Classificação
    classificacao_do_servico = Column(String, nullable=True)
    
    # Reprovação
    data_reprova = Column(DateTime, nullable=True)
    usuario_reprova = Column(String, nullable=True)
    observacao_reprova = Column(Text, nullable=True)
    
    # Usuários
    usuario_execucao = Column(String, nullable=True)
    usuario_vistoria_nao_procede = Column(String, nullable=True)
    usuario_primeira_vistoria = Column(String, nullable=True)
    usuario_agendamento = Column(String, nullable=True)
    usuario_publicacao = Column(String, nullable=True)
    
    # Evidências
    fotos = Column(JSON, nullable=True, default=list)
    
    # Relacionamentos
    sac = relationship("SAC", back_populates="ouvidorias")
    
    # Índices
    __table_args__ = (
        Index("idx_ouvidoria_status", "status"),
        Index("idx_ouvidoria_data_registro", "data_registro"),
    )
    
    def __repr__(self):
        return f"<Ouvidoria {self.numero_chamado} - {self.status}>"

