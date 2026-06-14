"""
Integration tests — runs the real RAG pipeline against 10 diverse Python questions.

Requirements: ANTHROPIC_API_KEY set in .env
Run: pytest tests/test_queries.py -v -s

Results are saved to data/test_results.json for the submission.
"""
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

TEST_QUERIES = [
    {
        "id": 1,
        "category": "Basic Operations",
        "question": "How do I reverse a list in Python?",
        "keywords": ["reverse", "[::-1]", ".reverse()"],
    },
    {
        "id": 2,
        "category": "Data Structures",
        "question": "What is the difference between a list and a tuple in Python?",
        "keywords": ["mutable", "immutable", "tuple", "list"],
    },
    {
        "id": 3,
        "category": "Functional Programming",
        "question": "How do list comprehensions work in Python?",
        "keywords": ["comprehension", "for", "if"],
    },
    {
        "id": 4,
        "category": "File I/O",
        "question": "How do I read a file line by line in Python?",
        "keywords": ["open", "with", "readline", "for"],
    },
    {
        "id": 5,
        "category": "OOP",
        "question": "How do I use decorators in Python?",
        "keywords": ["decorator", "wraps", "functools", "@"],
    },
    {
        "id": 6,
        "category": "Advanced",
        "question": "What are Python generators and when should I use them?",
        "keywords": ["yield", "generator", "lazy", "memory"],
    },
    {
        "id": 7,
        "category": "Error Handling",
        "question": "How do I handle multiple exceptions in Python?",
        "keywords": ["try", "except", "exception", "finally"],
    },
    {
        "id": 8,
        "category": "Standard Library",
        "question": "How do I use the collections.Counter to count elements?",
        "keywords": ["Counter", "collections", "count", "most_common"],
    },
    {
        "id": 9,
        "category": "Async",
        "question": "How does async/await work in Python?",
        "keywords": ["async", "await", "asyncio", "coroutine"],
    },
    {
        "id": 10,
        "category": "Edge Case",
        "question": "How can I check if a variable is None in Python?",
        "keywords": ["None", "is None", "isinstance"],
    },
]


@pytest.fixture(scope="module")
def pipeline():
    from app.rag import RAGPipeline

    p = RAGPipeline()
    p.load()
    return p


@pytest.mark.integration
@pytest.mark.parametrize("query", TEST_QUERIES, ids=[q["id"] for q in TEST_QUERIES])
def test_query(pipeline, query, tmp_path_factory):
    answer, sources, latency_ms = pipeline.ask(query["question"])

    assert answer, "Answer must not be empty"
    assert len(answer) > 20, "Answer seems too short"
    assert len(sources) > 0, "At least one source should be returned"
    assert latency_ms > 0

    # At least one keyword should appear in the answer (case-insensitive)
    answer_lower = answer.lower()
    matched = [kw for kw in query["keywords"] if kw.lower() in answer_lower]
    assert matched, (
        f"None of the expected keywords {query['keywords']} found in answer:\n{answer[:300]}"
    )


def run_and_save():
    """Run all queries manually and save results to data/test_results.json."""
    from app.rag import RAGPipeline

    pipeline = RAGPipeline()
    pipeline.load()

    results = []
    for query in TEST_QUERIES:
        print(f"\n[{query['id']}/10] {query['question']}")

        # Retry up to 3 times on rate-limit (429) with back-off
        for attempt in range(3):
            try:
                t0 = time.perf_counter()
                answer, sources, latency_ms = pipeline.ask(query["question"])
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 30
                    print(f"  ⏳ Rate limit hit — waiting {wait}s before retry {attempt + 2}/3...")
                    time.sleep(wait)
                else:
                    raise

        result = {
            "id": query["id"],
            "category": query["category"],
            "question": query["question"],
            "answer": answer,
            "sources": [s.model_dump() for s in sources],
            "latency_ms": round(latency_ms, 1),
            "keywords_found": [kw for kw in query["keywords"] if kw.lower() in answer.lower()],
            "pass": bool([kw for kw in query["keywords"] if kw.lower() in answer.lower()]),
        }
        results.append(result)
        print(f"  ✓ {latency_ms:.0f}ms — keywords matched: {result['keywords_found']}")

        # Stay under free-tier rate limit (5 req/min) — skip pause after last query
        if query["id"] < len(TEST_QUERIES):
            time.sleep(13)

    out = Path("data/test_results.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {out}")

    passed = sum(1 for r in results if r["pass"])
    print(f"\n{'='*50}")
    print(f"Passed: {passed}/{len(results)}")
    return results


if __name__ == "__main__":
    run_and_save()
