"""
Step 3: Merge HuggingFace data + domain pairs, deduplicate, filter quality,
and split into train/eval sets ready for LLaMA 3 SFT.

Run:
  python pipeline/3_merge_and_clean.py

Output:
  pipeline/train.jsonl   — ~90% split
  pipeline/eval.jsonl    — ~10% split
"""

import hashlib
import json
import os
import random
import re

random.seed(42)

DIR = os.path.dirname(__file__)
INPUTS = [
    os.path.join(DIR, "raw_hf_combined.jsonl"),
    os.path.join(DIR, "domain_pairs.jsonl"),
]
TRAIN_OUT = os.path.join(DIR, "train.jsonl")
EVAL_OUT  = os.path.join(DIR, "eval.jsonl")

SYSTEM_PROMPT = (
    "You are Reflect — a trauma-informed analysis tool built on the clinical research of "
    "Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. "
    "You help people who are actively being abused, stalked, or coercively controlled understand "
    "exactly what is being done to them, why it works, and what it means. "
    "You are clinical, direct, and precise. You never hedge findings that are clear."
)

MIN_INSTRUCTION = 20
MIN_OUTPUT = 40
MAX_OUTPUT = 3000


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def to_llama3(instruction, output):
    return {
        "text": (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{instruction}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n{output}<|eot_id|>"
        )
    }


seen = set()
records = []
dropped_missing = 0
dropped_short = 0
dropped_long = 0
dropped_dupe = 0

for path in INPUTS:
    if not os.path.exists(path):
        print(f"Skipping missing file: {path}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            instruction = (obj.get("instruction") or "").strip()
            output = (obj.get("output") or "").strip()

            if not instruction or not output:
                dropped_missing += 1
                continue
            if len(instruction) < MIN_INSTRUCTION or len(output) < MIN_OUTPUT:
                dropped_short += 1
                continue
            if len(output) > MAX_OUTPUT:
                dropped_long += 1
                continue

            key = sha(normalize(instruction) + normalize(output))
            if key in seen:
                dropped_dupe += 1
                continue
            seen.add(key)

            records.append(to_llama3(instruction, output))

print(f"Loaded {len(records)} clean records")
print(f"  dropped missing fields: {dropped_missing}")
print(f"  dropped too short:      {dropped_short}")
print(f"  dropped too long:       {dropped_long}")
print(f"  dropped duplicates:     {dropped_dupe}")

random.shuffle(records)
split = int(len(records) * 0.9)
train = records[:split]
eval_ = records[split:]

with open(TRAIN_OUT, "w", encoding="utf-8") as f:
    for r in train:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open(EVAL_OUT, "w", encoding="utf-8") as f:
    for r in eval_:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"\nTrain: {len(train)} records → {TRAIN_OUT}")
print(f"Eval:  {len(eval_)} records → {EVAL_OUT}")
