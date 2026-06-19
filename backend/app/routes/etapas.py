from fastapi import APIRouter
from ..models import ETAPAS

router = APIRouter(prefix="/api/etapas", tags=["etapas"])

COR_ETAPA = {
    "Selecionado":             "#3b82f6",
    "Habilitação da Entidade": "#8b5cf6",
    "Contratação":             "#f59e0b",
    "Início das Obras":        "#f97316",
    "Em Execução":             "#06b6d4",
    "Entrega das Chaves":      "#16a34a",
}


@router.get("")
def listar_etapas():
    return [{"nome": e, "cor": COR_ETAPA.get(e, "#94a3b8")} for e in ETAPAS]
