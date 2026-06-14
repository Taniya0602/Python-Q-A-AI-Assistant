import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import AnswerResponse, ErrorResponse, HealthResponse, QuestionRequest
from app.rag import rag_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: loading RAG pipeline...")
    rag_pipeline.load()
    yield
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Python Programming Q&A Assistant",
    description="AI-powered Q&A for Python learners, grounded in Stack Overflow data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Returns service health and vector store status."""
    return HealthResponse(
        status="healthy" if rag_pipeline.is_loaded else "loading",
        vector_store_loaded=rag_pipeline.is_loaded,
        total_documents=rag_pipeline.total_docs,
        model=settings.model_name,
    )


@app.post("/ask", response_model=AnswerResponse, tags=["Q&A"])
async def ask(request: QuestionRequest):
    """
    Ask a Python programming question.

    Returns a grounded answer with sources retrieved from Stack Overflow.
    """
    if not rag_pipeline.is_loaded:
        raise HTTPException(status_code=503, detail="Pipeline is still loading. Please try again shortly.")

    try:
        answer, sources, latency_ms = rag_pipeline.ask(request.question, request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        err = str(exc)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            raise HTTPException(
                status_code=429,
                detail="Free-tier API quota reached (20 requests/day for Gemini 2.5 Flash). Quota resets in ~24 hours. Please try again later.",
            )
        logger.exception("Error while processing question")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your question.")

    return AnswerResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        model=settings.model_name,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Internal server error", detail=str(exc)).model_dump(mode="json"),
    )
