from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EtapaHistoricoOut(BaseModel):
    etapa_de: Optional[str]
    etapa_para: str
    observacao: Optional[str]
    alterado_em: datetime

    model_config = {"from_attributes": True}


class PropostaOut(BaseModel):
    num_proposta: str
    uf: str
    municipio: str
    entidade: str
    cnpj: Optional[str]
    unidades: int
    etapa_atual: str
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class PropostaDetalhe(PropostaOut):
    historico: list[EtapaHistoricoOut] = []


class AtualizarEtapa(BaseModel):
    etapa: str
    observacao: Optional[str] = None


class Stats(BaseModel):
    total_propostas: int
    total_unidades: int
    total_ufs: int
    total_municipios: int
    por_etapa: list[dict]
    por_uf: list[dict]
