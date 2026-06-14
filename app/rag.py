import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

from google import genai
from google.genai import types
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings
from app.models import Source

logger = logging.getLogger(__name__)

# Strict RAG prompt — model must answer only from retrieved context
PROMPT_TEMPLATE = """You are a Python programming assistant. Your answers must be grounded STRICTLY in the Stack Overflow context provided below.

Rules:
- Answer ONLY using information from the context — do NOT use outside knowledge
- Include relevant code examples from the context, formatted as markdown code blocks
- If the context does not contain enough information, say exactly: "I don't have enough data in my knowledge base to answer this accurately. Try rephrasing or asking a more specific Python question."
- Be concise but complete

--- CONTEXT START ---
{context}
--- CONTEXT END ---

Question: {question}

Answer:"""


class RAGPipeline:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.client: Optional[genai.Client] = None
        self.total_docs = 0
        self._loaded = False

    def load(self):
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set in .env")

        logger.info("Initialising Google GenAI client...")
        self.client = genai.Client(api_key=settings.google_api_key)

        logger.info("Loading embedding model...")
        from langchain_huggingface import HuggingFaceEmbeddings

        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        store_path = Path(settings.vector_store_path)
        if store_path.exists():
            logger.info(f"Loading FAISS index from {store_path}...")
            self.vector_store = FAISS.load_local(
                str(store_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            logger.warning("FAISS index not found — using bundled sample data.")
            self._load_sample_data()

        self.total_docs = self.vector_store.index.ntotal
        logger.info(f"RAG pipeline ready — {self.total_docs} documents indexed.")
        self._loaded = True

    def _load_sample_data(self):
        import json

        sample_path = Path("data/sample_data.json")
        if not sample_path.exists():
            raise FileNotFoundError(
                "No FAISS index and no sample_data.json found. "
                "Run `python scripts/build_index.py` to build the index."
            )
        with open(sample_path) as f:
            samples = json.load(f)

        docs = [
            Document(
                page_content=f"Q: {item['question']}\n\nA: {item['answer']}",
                metadata={"title": item["question"][:80], "score": item.get("score", 0)},
            )
            for item in samples
        ]
        logger.info(f"Building in-memory FAISS from {len(docs)} sample documents...")
        self.vector_store = FAISS.from_documents(docs, self.embeddings)

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Source")
            parts.append(f"[Source {i}] {title}\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)

    def ask(self, question: str, top_k: Optional[int] = None) -> Tuple[str, List[Source], float]:
        if not self._loaded:
            raise RuntimeError("RAG pipeline not loaded. Call load() first.")

        k = top_k or settings.top_k

        # Retrieve relevant documents
        source_docs = self.vector_store.similarity_search(question, k=k)
        context = self._format_context(source_docs)

        # Build prompt
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # Generate answer with Google GenAI SDK
        t0 = time.perf_counter()
        response = self.client.models.generate_content(
            model=settings.model_name or "gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.1,  # low temp for factual, grounded answers
            ),
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        answer = response.text or "No answer generated."

        sources = [
            Source(
                title=doc.metadata.get("title", "Stack Overflow")[:100],
                score=float(doc.metadata.get("score", 0)),
                snippet=(doc.page_content[:250] + "...") if len(doc.page_content) > 250 else doc.page_content,
            )
            for doc in source_docs
        ]

        return answer, sources, round(latency_ms, 2)

    @property
    def is_loaded(self) -> bool:
        return self._loaded


rag_pipeline = RAGPipeline()
