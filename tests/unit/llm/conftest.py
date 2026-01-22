import pytest
from unittest.mock import MagicMock
import sys

# Pre-create fake modules for chroma
mock_chroma_module = MagicMock()
mock_chroma_db_instance = MagicMock()
mock_chroma_module.ChromaVectorDB = MagicMock(return_value=mock_chroma_db_instance)
mock_chroma_module.chroma_db = mock_chroma_db_instance

# before any test runs
sys.modules["chroma_db.chroma_vector_db"] = mock_chroma_module


@pytest.fixture(autouse=True)
def mock_chroma(monkeypatch):
    pass
