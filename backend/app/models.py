from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

ETAPAS = [
    "Selecionado",
    "Habilitação da Entidade",
    "Contratação",
    "Início das Obras",
    "Em Execução",
    "Entrega das Chaves",
]


class Proposta(Base):
    __tablename__ = "propostas"

    num_proposta = Column(String(64), primary_key=True, index=True)
    uf           = Column(String(2), index=True, nullable=False)
    municipio    = Column(String(120), index=True, nullable=False)
    entidade     = Column(String(255), nullable=False)
    cnpj         = Column(String(20))
    unidades     = Column(Integer, default=0)
    etapa_atual  = Column(String(60), default="Selecionado", index=True)
    criado_em    = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    historico = relationship("EtapaHistorico", back_populates="proposta", cascade="all, delete-orphan")


class EtapaHistorico(Base):
    __tablename__ = "etapa_historico"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    num_proposta = Column(String(64), ForeignKey("propostas.num_proposta"), nullable=False)
    etapa_de     = Column(String(60))
    etapa_para   = Column(String(60), nullable=False)
    observacao   = Column(Text)
    alterado_em  = Column(DateTime, default=datetime.utcnow)

    proposta = relationship("Proposta", back_populates="historico")
