"""
Data cleaning pass for both the RAG notes folder and a fine-tuning JSONL
dataset: deduplication, basic quality filtering, and format validation.
Run this before feeding either into the rest of the pipeline.

Usage:
    python clean_data.py --notes ./notes --jsonl train_data.jsonl
"""

import argparse
import glob
import hashlib
import json
import os
import re


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_notes_folder(notes_dir: str, min_len: int = 20) -> dict:
    seen_hashes = set()
    report = {
        "files_scanned": 0,
        "chunks_kept": 0,
        "chunks_dropped_dupe": 0,
        "chunks_dropped_short": 0,
    }

    paths = glob.glob(os.path.join(notes_dir, "**/*.md"), recursive=True) + \
        glob.glob(os.path.join(notes_dir, "**/*.txt"), recursive=True)

    for path in paths:
        report["files_scanned"] += 1
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        kept_paragraphs = []
        for para in text.split("\n\n"):
            norm = normalize_text(para)
            if len(norm) < min_len:
                report["chunks_dropped_short"] += 1
                continue
            h = hash_text(norm.lower())
            if h in seen_hashes:
                report["chunks_dropped_dupe"] += 1
                continue
            seen_hashes.add(h)
            kept_paragraphs.append(para.strip())
            report["chunks_kept"] += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(kept_paragraphs))

    return report


def clean_jsonl(path: str, min_output_len: int = 10) -> dict:
    seen_hashes = set()
    kept = []
    dropped_dupe = 0
    dropped_short = 0
    dropped_malformed = 0

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            dropped_malformed += 1
            continue

        if "instruction" not in obj or "output" not in obj:
            dropped_malformed += 1
            continue

        norm_output = normalize_text(obj["output"])
        if len(norm_output) < min_output_len:
            dropped_short += 1
            continue

        key = hash_text(normalize_text(obj["instruction"]).lower() + norm_output.lower())
        if key in seen_hashes:
            dropped_dupe += 1
            continue
        seen_hashes.add(key)
        kept.append(obj)

    out_path = path.replace(".jsonl", "_clean.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for obj in kept:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    return {
        "total_lines": len(lines),
        "kept": len(kept),
        "dropped_dupe": dropped_dupe,
        "dropped_short": dropped_short,
        "dropped_malformed": dropped_malformed,
        "output_path": out_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--notes", default=None, help="Path to notes folder to clean")
    parser.add_argument("--jsonl", default=None, help="Path to fine-tuning JSONL to clean")
    args = parser.parse_args()

    if args.notes:
        print("Notes cleaning report:", json.dumps(clean_notes_folder(args.notes), indent=2))

    if args.jsonl:
        print("JSONL cleaning report:", json.dumps(clean_jsonl(args.jsonl), indent=2))
