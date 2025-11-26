"""Model para SACs."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Float, ForeignKey, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TipoServico(str, enum.Enum):
    """
    Tipos de serviço.
    
    IMPORTANTE: Os valores devem corresponder aos nomes do enum PostgreSQL (MAIÚSCULAS).
    """
    ENTULHO = "ENTULHO"  # Coleta e transporte de entulho e grandes objetos (Demandante - 72h)
    ANIMAL_MORTO = "ANIMAL_MORTO"  # Remoção de animais mortos (Demandante - 12h)
    PAPELEIRAS = "PAPELEIRAS"  # Papeleiras e equipamentos de recepção de resíduos (Demandante - 72h)
    CATABAGULHO = "CATABAGULHO"  # Coleta programada de objetos volumosos (Escalonado)
    VARRIACAO_COLETA = "VARRIACAO_COLETA"  # Coleta manual de resíduos de varrição e feiras (Escalonado)
    MUTIRAO = "MUTIRAO"  # Mutirão de Zeladoria (inclui Capinação, Propaganda, Raspagem, Pintura) (Escalonado)
    LAVAGEM = "LAVAGEM"  # Lavagem especial de equipamentos públicos (Escalonado)
    BUEIRO = "BUEIRO"  # Limpeza e desobstrução de bueiros (Escalonado)
    VARRIACAO = "VARRIACAO"  # Varrição manual de vias e logradouros (Escalonado)
    VARRIACAO_PRACAS = "VARRIACAO_PRACAS"  # Varrição de Praças (Escalonado)
    MONUMENTOS = "MONUMENTOS"  # Limpeza e conservação de monumentos públicos (Escalonado)
    OUTROS = "OUTROS"  # Outros serviços (Escalonado)


class StatusSAC(str, enum.Enum):
    """Status dos SACs."""
    AGUARDANDO_ANALISE = "Aguardando Análise"
    AGUARDANDO_AGENDAMENTO = "Aguardando Agendamento"
    AGUARDANDO_REVISTORIA = "Aguardando Revistoria"
    NAO_PROCEDE = "Não Procede"
    EM_EXECUCAO = "Em Execução"
    EXECUTADO = "Executado"
    CONFIRMAR_EXECUCAO = "Confirmar Execução"
    CONFIRMADA_EXECUCAO = "Confirmada Execução"
    NAO_CONFIRMADA_EXECUCAO = "Não Confirmada Execução"
    CONFIRMAR_FORA_ESCOPO = "Confirmar Fora de Escopo"
    AGUARDANDO_CONFIRMACAO_EXECUCAO_PARCIAL = "Aguardando Confirmação de Execução Parcial"
    FINALIZADO = "Finalizado"


class Subprefeitura(str, enum.Enum):
    """Subprefeituras."""
    CV = "CV"  # Casa Verde/Cachoeirinha
    JT = "JT"  # Jaçanã/Tremembé
    ST = "ST"  # Santana/Tucuruvi
    MG = "MG"  # Vila Maria/Vila Guilherme


class SAC(Base):
    """Model para SACs."""
    __tablename__ = "sacs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocolo = Column(String, unique=True, nullable=False, index=True)
    tipo_servico = Column(Enum(TipoServico), nullable=False, index=True)
    status = Column(Enum(StatusSAC), nullable=False, index=True)
    subprefeitura = Column(Enum(Subprefeitura), nullable=False, index=True)
    endereco_text = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    bairro = Column(String, nullable=True)
    domicilio_id = Column(String, nullable=True)
    protocolo_origem = Column(String, nullable=True)
    
    # Datas
    data_criacao = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    data_vistoria = Column(DateTime, nullable=True)
    data_agendamento = Column(DateTime, nullable=True, index=True)
    data_execucao = Column(DateTime, nullable=True, index=True)
    data_encerramento = Column(DateTime, nullable=True)
    
    # Prazos e fiscal
    prazo_max_hours = Column(Integer, nullable=False)
    fiscal_id = Column(UUID(as_uuid=True), ForeignKey("fiscais.id"), nullable=True)
    
    # Evidências
    fotos_before = Column(JSON, nullable=True, default=list)
    fotos_after = Column(JSON, nullable=True, default=list)
    evidencias = Column(JSON, nullable=True)
    
    # Flags
    flag_erro_regional = Column(Boolean, default=False, index=True)
    inserted_from_csv = Column(Boolean, default=False)
    
    # Relacionamentos
    fiscal = relationship("Fiscal", back_populates="sacs")
    ouvidorias = relationship("Ouvidoria", back_populates="sac")
    logs_status = relationship("LogStatus", back_populates="sac")
    
    # Índices compostos
    __table_args__ = (
        Index("idx_sac_status_subpref", "status", "subprefeitura"),
        Index("idx_sac_data_criacao", "data_criacao"),
    )
    
    def __repr__(self):
        return f"<SAC {self.protocolo} - {self.status}>"

