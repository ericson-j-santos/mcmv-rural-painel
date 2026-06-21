import json as _json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


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
    tags: list[str] = []
    responsavel: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except Exception:
                return []
        if isinstance(v, list):
            return v
        return []


class PropostaDetalhe(PropostaOut):
    historico: list[EtapaHistoricoOut] = []


class AtualizarEtapa(BaseModel):
    etapa: str
    observacao: Optional[str] = None


class BulkEtapa(BaseModel):
    ids: list[str]
    etapa: str
    observacao: Optional[str] = None


class TagsUpdate(BaseModel):
    tags: list[str]


class ResponsavelUpdate(BaseModel):
    responsavel: Optional[str] = None


class Stats(BaseModel):
    total_propostas: int
    total_unidades: int
    total_ufs: int
    total_municipios: int
    cnpj_validos: int
    cnpj_invalidos: int
    cnpj_unicos: int
    cnpj_unicos_validos: int
    avancos_7d: int = 0
    por_etapa: list[dict]
    por_uf: list[dict]
