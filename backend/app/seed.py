"""Carrega mcmv_rural_lista.json no banco na primeira execução."""
import json, os, re
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Proposta

JSON_PATH = Path(__file__).parent.parent / "data" / "mcmv_rural_lista.json"

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _clean_cnpj(value: str) -> str:
    """Normaliza CNPJ para XX.XXX.XXX/XXXX-XX, removendo espaços do PDF."""
    if not value:
        return ""
    nums = re.sub(r"[^\d]", "", value)
    if len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:14]}"
    return re.sub(r"\s+", "", value)


def seed(db: Session):
    if os.getenv("TESTING"):
        return
    if db.query(Proposta).count() > 0:
        return  # já populado

    if not JSON_PATH.exists():
        print(f"[seed] Arquivo não encontrado: {JSON_PATH}")
        return

    with open(JSON_PATH, encoding="utf-8") as f:
        dados = json.load(f)

    batch = []
    for d in dados:
        num_proposta = d.get("num_proposta", "")
        if not num_proposta or d.get("uf") == "UF":
            continue
        if not _UUID_RE.match(num_proposta):
            continue  # fragmento de extração PDF — descarta linha incompleta
        batch.append(Proposta(
            num_proposta=num_proposta,
            uf=d["uf"],
            municipio=d.get("municipio", ""),
            entidade=d.get("entidade", ""),
            cnpj=_clean_cnpj(d.get("cnpj", "")),
            unidades=d.get("unidades", 0),
            etapa_atual="Selecionado",
        ))

    db.bulk_save_objects(batch)
    db.commit()
    print(f"[seed] {len(batch)} propostas carregadas.")
