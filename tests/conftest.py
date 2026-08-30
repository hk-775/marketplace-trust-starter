from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from marketplace_trust_starter.app import create_app


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def app(database_path: Path):
    return create_app(database_path)


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
