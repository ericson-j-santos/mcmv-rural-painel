import csv, io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Proposta, EtapaHistorico, ETAPAS
from ..schemas import PropostaOut, PropostaDetalhe, AtualizarEtapa, Stats

router = APIRouter(prefix="/api/propostas", tags=["propostas"])

COR_ETAPA = {
    "Selecionado":             "#3b82f6",
    "Habilitação da Entidade": "#8b5cf6",
    "Contratação":             "#f59e0b",
    "Início das Obras":        "#f97316",
    "Em Execução":             "#06b6d4",
    "Entrega das Chaves":      "#16a34a",
}


@router.get("/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    total_p  = db.query(func.count(Proposta.num_proposta)).scalar()
    total_u  = db.query(func.sum(Proposta.unidades)).scalar() or 0
    total_uf = db.query(func.count(func.distinct(Proposta.uf))).scalar()
    total_m  = db.query(func.count(func.distinct(Proposta.municipio))).scalar()

    por_etapa = []
    for etapa in ETAPAS:
        qtd = db.query(func.count(Proposta.num_proposta)).filter(Proposta.etapa_atual == etapa).scalar()
        un  = db.query(func.sum(Proposta.unidades)).filter(Proposta.etapa_atual == etapa).scalar() or 0
        por_etapa.append({"etapa": etapa, "cor": COR_ETAPA.get(etapa, "#94a3b8"), "propostas": qtd, "unidades": un})

    por_uf_rows = (
        db.query(Proposta.uf, func.count(Proposta.num_proposta), func.sum(Proposta.unidades))
        .group_by(Proposta.uf)
        .order_by(func.count(Proposta.num_proposta).desc())
        .all()
    )
    por_uf = [{"uf": r[0], "propostas": r[1], "unidades": r[2] or 0} for r in por_uf_rows]

    return Stats(
        total_propostas=total_p,
        total_unidades=total_u,
        total_ufs=total_uf,
        total_municipios=total_m,
        por_etapa=por_etapa,
        por_uf=por_uf,
    )


@router.get("", response_model=dict)
def listar(
    uf: Optional[str]    = Query(None),
    etapa: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    pagina: int          = Query(1, ge=1),
    por_pagina: int      = Query(20, ge=1, le=200),
    db: Session          = Depends(get_db),
):
    q = db.query(Proposta)
    if uf:    q = q.filter(Proposta.uf == uf)
    if etapa: q = q.filter(Proposta.etapa_atual == etapa)
    if busca:
        termo = f"%{busca}%"
        q = q.filter(
            Proposta.municipio.ilike(termo) | Proposta.entidade.ilike(termo)
        )
    total = q.count()
    items = q.order_by(Proposta.uf, Proposta.municipio).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": max(1, -(-total // por_pagina)),
        "items": [PropostaOut.model_validate(i) for i in items],
    }


@router.get("/export")
def exportar_csv(
    uf: Optional[str]    = Query(None),
    etapa: Optional[str] = Query(None),
    db: Session          = Depends(get_db),
):
    q = db.query(Proposta)
    if uf:    q = q.filter(Proposta.uf == uf)
    if etapa: q = q.filter(Proposta.etapa_atual == etapa)
    rows = q.order_by(Proposta.uf, Proposta.municipio).all()

    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["UF", "Município", "Entidade", "CNPJ", "Nº Proposta", "Unidades", "Etapa Atual", "Atualizado Em"])
    for r in rows:
        w.writerow([r.uf, r.municipio, r.entidade, r.cnpj, r.num_proposta, r.unidades, r.etapa_atual, r.atualizado_em])

    output.seek(0)
    return StreamingResponse(
        iter(["﻿" + output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mcmv_rural.csv"},
    )


@router.get("/{num_proposta}", response_model=PropostaDetalhe)
def detalhe(num_proposta: str, db: Session = Depends(get_db)):
    p = db.query(Proposta).filter(Proposta.num_proposta == num_proposta).first()
    if not p:
        raise HTTPException(404, "Proposta não encontrada")
    return p


@router.put("/{num_proposta}/etapa", response_model=PropostaOut)
def atualizar_etapa(num_proposta: str, body: AtualizarEtapa, db: Session = Depends(get_db)):
    if body.etapa not in ETAPAS:
        raise HTTPException(400, f"Etapa inválida. Opções: {ETAPAS}")
    p = db.query(Proposta).filter(Proposta.num_proposta == num_proposta).first()
    if not p:
        raise HTTPException(404, "Proposta não encontrada")

    hist = EtapaHistorico(
        num_proposta=p.num_proposta,
        etapa_de=p.etapa_atual,
        etapa_para=body.etapa,
        observacao=body.observacao,
    )
    db.add(hist)
    p.etapa_atual = body.etapa
    db.commit()
    db.refresh(p)
    return p
