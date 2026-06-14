"""
Process the raw Stack Overflow Python dataset from Kaggle into Q&A pairs.

Usage:
    # 1. Set up Kaggle credentials (~/.kaggle/kaggle.json)
    # 2. Run:
    python -m data.process
"""
import json
import logging
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

logger = logging.getLogger(__name__)


def download_dataset(dest: str = "data/raw"):
    """Download the dataset from Kaggle (requires kaggle.json credentials)."""
    import kaggle

    Path(dest).mkdir(parents=True, exist_ok=True)
    logger.info("Downloading Stack Overflow Python dataset from Kaggle...")
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(
        "stackoverflow/pythonquestions",
        path=dest,
        unzip=True,
        quiet=False,
    )
    logger.info(f"Dataset downloaded to {dest}/")


def clean_html(html: str) -> str:
    if not html or not isinstance(html, str):
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)


def process_dataset(
    data_dir: str = "data/raw",
    output_path: str = "data/processed.json",
    min_score: int = 5,
    max_records: int = 50_000,
) -> list:
    data_dir = Path(data_dir)
    logger.info("Loading Questions.csv...")
    questions = pd.read_csv(
        data_dir / "Questions.csv",
        encoding="latin-1",
        usecols=["Id", "Title", "Body", "Score"],
    )
    questions = questions[questions["Score"] >= min_score].head(max_records * 2)

    logger.info("Loading Answers.csv...")
    answers = pd.read_csv(
        data_dir / "Answers.csv",
        encoding="latin-1",
        usecols=["Id", "ParentId", "Body", "Score"],
    )

    # Keep only the best answer per question
    best_answers = (
        answers.sort_values("Score", ascending=False)
        .drop_duplicates(subset="ParentId")
        .rename(columns={"Id": "AnswerId", "Body": "AnswerBody", "Score": "AnswerScore"})
    )

    merged = questions.merge(
        best_answers[["ParentId", "AnswerBody", "AnswerScore"]],
        left_on="Id",
        right_on="ParentId",
        how="inner",
    ).head(max_records)

    logger.info(f"Processing {len(merged)} Q&A pairs...")
    records = []
    for _, row in tqdm(merged.iterrows(), total=len(merged), desc="Processing"):
        q_body = clean_html(str(row["Body"]))
        a_body = clean_html(str(row["AnswerBody"]))
        if not q_body or not a_body:
            continue
        records.append(
            {
                "id": int(row["Id"]),
                "question": str(row["Title"]),
                "question_body": q_body[:1000],
                "answer": a_body[:2000],
                "score": int(row["Score"]),
                "answer_score": int(row["AnswerScore"]),
            }
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    logger.info(f"Saved {len(records)} records to {output_path}")
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Download from Kaggle first")
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output", default="data/processed.json")
    parser.add_argument("--min-score", type=int, default=5)
    parser.add_argument("--max-records", type=int, default=50_000)
    args = parser.parse_args()

    if args.download:
        download_dataset(args.data_dir)

    process_dataset(args.data_dir, args.output, args.min_score, args.max_records)
