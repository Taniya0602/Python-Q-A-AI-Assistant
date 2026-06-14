"""
Unit tests for the FastAPI endpoints.

The RAG pipeline is mocked so tests run without a GPU/API key.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.models import Source


MOCK_ANSWER = (
    "To reverse a list in Python, use slicing: `my_list[::-1]` (returns a new list) "
    "or `my_list.reverse()` (in-place)."
)
MOCK_SOURCES = [
    Source(title="How do I reverse a list in Python?", score=150, snippet="Q: How do I reverse a list...")
]


@pytest.fixture(autouse=True)
def mock_pipeline():
    with patch("app.main.rag_pipeline") as mock:
        mock.is_loaded = True
        mock.total_docs = 50
        mock.ask.return_value = (MOCK_ANSWER, MOCK_SOURCES, 312.5)
        yield mock


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = (await client.get("/health")).json()
    assert data["status"] == "healthy"
    assert data["vector_store_loaded"] is True
    assert isinstance(data["total_documents"], int)
    assert "model" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_when_pipeline_not_loaded():
    with patch("app.main.rag_pipeline") as mock:
        mock.is_loaded = False
        mock.total_docs = 0
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            data = (await client.get("/health")).json()
    assert data["status"] == "loading"


# ---------------------------------------------------------------------------
# POST /ask — happy paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ask_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "How do I reverse a list in Python?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "How do I reverse a list in Python?"
    assert data["answer"] == MOCK_ANSWER
    assert isinstance(data["sources"], list)
    assert isinstance(data["latency_ms"], float)
    assert "timestamp" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_ask_with_custom_top_k():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "What is a list comprehension?", "top_k": 3})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ask_calls_pipeline_with_correct_args(mock_pipeline):
    question = "How do I use decorators in Python?"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/ask", json={"question": question, "top_k": 4})
    mock_pipeline.ask.assert_called_once_with(question, 4)


# ---------------------------------------------------------------------------
# POST /ask — validation errors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ask_rejects_empty_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ask_rejects_too_short_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "Hi"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ask_rejects_missing_question_field():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ask_rejects_invalid_top_k():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "What is Python?", "top_k": 0})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ask_rejects_top_k_too_large():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "What is Python?", "top_k": 99})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /ask — error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ask_503_when_pipeline_not_loaded():
    with patch("app.main.rag_pipeline") as mock:
        mock.is_loaded = False
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/ask", json={"question": "How do I read a file in Python?"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_ask_500_on_unexpected_error(mock_pipeline):
    mock_pipeline.ask.side_effect = RuntimeError("Unexpected failure")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "How do I use generators?"})
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_ask_400_on_value_error(mock_pipeline):
    mock_pipeline.ask.side_effect = ValueError("No API key configured")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/ask", json={"question": "How do I use generators?"})
    assert resp.status_code == 400
