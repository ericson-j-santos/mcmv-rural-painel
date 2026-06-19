from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import EtapaHistorico, Proposta

router = APIRouter(prefix="/api/historico", tags=["historico"])


@router.get("")
def recente(limite: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    rows = (
        db.query(EtapaHistorico, Proposta)
        .join(Proposta, Proposta.num_proposta == EtapaHistorico.num_proposta)
        .order_by(EtapaHistorico.alterado_em.desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "id":           h.id,
            "num_proposta": h.num_proposta,
            "municipio":    p.municipio,
            "uf":           p.uf,
            "entidade":     p.entidade,
            "etapa_de":     h.etapa_de,
            "etapa_para":   h.etapa_para,
            "observacao":   h.observacao,
            "alterado_em":  h.alterado_em.isoformat(),
        }
        for h, p in rows
    ]


@router.get("/relatorio")
def relatorio(dias: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=dias)
    rows = db.query(EtapaHistorico).filter(EtapaHistorico.alterado_em >= cutoff).all()

    por_dia: dict[str, int] = {}
    por_etapa: dict[str, int] = {}
    for h in rows:
        d = h.alterado_em.strftime("%Y-%m-%d")
        por_dia[d] = por_dia.get(d, 0) + 1
        e = h.etapa_para or "?"
        por_etapa[e] = por_etapa.get(e, 0) + 1

    return {
        "total_avancadas": len(rows),
        "periodo_dias":    dias,
        "por_dia": [{"data": k, "avancadas": v} for k, v in sorted(por_dia.items())],
        "por_etapa": [{"etapa": k, "avancadas": v} for k, v in por_etapa.items()],
    }
