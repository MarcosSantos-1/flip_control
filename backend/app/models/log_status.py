"""Model para logs de alteração de status."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.sac import StatusSAC


class LogStatus(Base):
    """Model para histórico de alterações de status dos SACs."""
    __tablename__ = "logs_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sac_id = Column(UUID(as_uuid=True), ForeignKey("sacs.id"), nullable=False, index=True)
    
    # Alteração
    status_anterior = Column(String, nullable=True)
    status_novo = Column(String, nullable=False)
    
    # Usuário e motivo
    usuario = Column(String, nullable=True)
    motivo = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relacionamentos
    sac = relationship("SAC", back_populates="logs_status")
    
    # Índices
    __table_args__ = (
        Index("idx_log_sac_created", "sac_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<LogStatus {self.sac_id} - {self.status_anterior} -> {self.status_novo}>"

