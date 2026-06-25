#!/bin/bash
# Reflect Training Pipeline — run everything in order
# Usage: bash run_pipeline.sh
# All scripts run inside .venv which has all correct dependencies

set -e
cd "$(dirname "$0")"

PYTHON=".venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "ERROR: .venv not found. Run:"
    echo "  python3 -m venv .venv && .venv/bin/pip install numpy scikit-learn datasketch sentence-transformers pdfplumber anthropic"
    exit 1
fi

echo "=== Step 1: Build multi-turn dataset from all PDFs ==="
$PYTHON -W ignore pipeline/build_dataset.py

echo "=== Step 2: MinHash LSH + embedding dedup ==="
$PYTHON -W ignore pipeline/clean_dataset.py

echo "=== Step 3: Behavioral signal extraction + FAISS dedup ==="
$PYTHON -W ignore pipeline/behavioral_signals.py

echo "=== Step 4: Upload all outputs to Kaggle ==="
$PYTHON -W ignore pipeline/upload_to_kaggle.py

echo ""
echo "PIPELINE COMPLETE"
echo "Files:"
wc -l pipeline/master_sft.jsonl pipeline/master_dpo.jsonl pipeline/clean_sft.jsonl pipeline/behavioral_sft.jsonl 2>/dev/null
