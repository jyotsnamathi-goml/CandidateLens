import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Ensure all models are registered on Base
from app.db import Base, get_db
from app.main import app

# Test SQLite in-memory DB shared across threads
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    import app.config
    import app.db
    import app.services.evaluation
    import app.services.ingestion
    import app.services.llm_client
    monkeypatch.setattr(app.config.settings, "LLM_MOCK", True)
    monkeypatch.setattr(app.db, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(app.services.ingestion, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(app.services.evaluation, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(app.services.llm_client, "SessionLocal", TestingSessionLocal)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
