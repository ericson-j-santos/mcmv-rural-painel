"""Carrega mcmv_rural_lista.json no banco na primeira execução."""
import json, os
from pathlib import Path
from sqlalchemy.orm import Session
from .models import Proposta

JSON_PATH = Path(__file__).parent.parent / "data" / "mcmv_rural_lista.json"


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
        if not d.get("num_proposta") or d.get("uf") == "UF":
            continue
        batch.append(Proposta(
            num_proposta=d["num_proposta"],
            uf=d["uf"],
            municipio=d.get("municipio", ""),
            entidade=d.get("entidade", ""),
            cnpj=d.get("cnpj", ""),
            unidades=d.get("unidades", 0),
            etapa_atual="Selecionado",
        ))

    db.bulk_save_objects(batch)
    db.commit()
    print(f"[seed] {len(batch)} propostas carregadas.")
