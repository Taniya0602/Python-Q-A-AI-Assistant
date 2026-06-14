"""
Build a FAISS vector index from processed Q&A data.

Usage (after processing the Kaggle dataset):
    python scripts/build_index.py

Usage (with custom paths):
    python scripts/build_index.py --data data/processed.json --index data/faiss_index
"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def build_index(data_path: str, index_path: str, batch_size: int = 1_000):
    data_file = Path(data_path)
    if not data_file.exists():
        raise FileNotFoundError(
            f"{data_file} not found.\n"
            "Run `python -m data.process` first (requires Kaggle credentials),\n"
            "or use the bundled sample_data.json — the app will load it automatically."
        )

    with open(data_file) as f:
        records = json.load(f)

    logger.info(f"Loaded {len(records)} Q&A records from {data_file}")

    logger.info(f"Initialising embedding model: {settings.embedding_model}")
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    logger.info("Building FAISS index — this may take a few minutes for large datasets...")
    docs = []
    for rec in tqdm(records, desc="Preparing documents"):
        content = f"Q: {rec['question']}\n{rec.get('question_body', '')}\n\nA: {rec['answer']}"
        docs.append(
            Document(
                page_content=content[:3_000],
                metadata={
                    "id": rec.get("id", 0),
                    "title": rec["question"][:100],
                    "score": rec.get("score", 0),
                    "answer_score": rec.get("answer_score", 0),
                },
            )
        )

    vector_store = None
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        if vector_store is None:
            vector_store = FAISS.from_documents(batch, embeddings)
        else:
            vector_store.add_documents(batch)
        logger.info(f"  Indexed {min(i + batch_size, len(docs))}/{len(docs)} documents")

    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(index_path)
    logger.info(f"FAISS index saved to {index_path} ({vector_store.index.ntotal} vectors)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed.json", help="Path to processed Q&A JSON")
    parser.add_argument("--index", default=settings.vector_store_path, help="Output FAISS index path")
    parser.add_argument("--batch-size", type=int, default=1_000)
    args = parser.parse_args()

    build_index(args.data, args.index, args.batch_size)
