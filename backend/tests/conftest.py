"""Fixtures compartilhadas por todos os testes."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Impede o lifespan de gravar no SQLite real durante os testes
os.environ.setdefault("TESTING", "1")

from app.database import Base, get_db
from app.main import app
from app.models import Proposta, EtapaHistorico

# ─── Banco em memória exclusivo por sessão de testes ───────────────────────────
# StaticPool: todas as sessões compartilham a mesma conexão in-memory
TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

PROPOSTAS_FIXTURE = [
    {"num_proposta": "aaa-001", "uf": "AC", "municipio": "Acrelândia",    "entidade": "Assoc. Rural AC",   "cnpj": "11.111.111/0001-11", "unidades": 50,  "etapa_atual": "Selecionado"},
    {"num_proposta": "bbb-002", "uf": "BA", "municipio": "Salvador",      "entidade": "Coop. BA Sul",      "cnpj": "22.222.222/0001-22", "unidades": 30,  "etapa_atual": "Selecionado"},
    {"num_proposta": "ccc-003", "uf": "BA", "municipio": "Feira de Santana", "entidade": "Inst. Feirense", "cnpj": "33.333.333/0001-33", "unidades": 20,  "etapa_atual": "Contratação"},
    {"num_proposta": "ddd-004", "uf": "SP", "municipio": "São Paulo",     "entidade": "ONG SP",            "cnpj": "44.444.444/0001-44", "unidades": 100, "etapa_atual": "Em Execução"},
    {"num_proposta": "eee-005", "uf": "MG", "municipio": "Belo Horizonte","entidade": "Assoc. MG",         "cnpj": "55.555.555/0001-55", "unidades": 40,  "etapa_atual": "Entrega das Chaves"},
]


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Cria tabelas e semeia dados de teste uma vez por sessão."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSession()
    for p in PROPOSTAS_FIXTURE:
        db.add(Proposta(**p))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client(setup_db):
    """TestClient com banco de teste injetado."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db(setup_db):
    """Sessão de banco isolada por teste (com rollback ao final)."""
    conn = test_engine.connect()
    tx = conn.begin()
    session = TestingSession(bind=conn)
    yield session
    session.close()
    tx.rollback()
    conn.close()
