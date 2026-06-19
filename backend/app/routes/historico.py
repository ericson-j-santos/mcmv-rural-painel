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
