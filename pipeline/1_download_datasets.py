"""
Step 1: Download all HuggingFace datasets and convert to unified JSONL.

Each record: {"instruction": "...", "output": "..."}

Run:
  python pipeline/1_download_datasets.py

Output: pipeline/raw_hf_combined.jsonl
"""

import json
import os
from datasets import load_dataset

OUT = os.path.join(os.path.dirname(__file__), "raw_hf_combined.jsonl")


def write(records, f):
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")


def fmt(instruction, output):
    if not instruction or not output:
        return None
    instruction = str(instruction).strip()
    output = str(output).strip()
    if len(instruction) < 20 or len(output) < 30:
        return None
    return {"instruction": instruction, "output": output}


total = 0

with open(OUT, "w", encoding="utf-8") as f:

    # 1. Real therapist Q&A — CounselChat licensed clinicians
    print("Downloading Amod/mental_health_counseling_conversations...")
    ds = load_dataset("Amod/mental_health_counseling_conversations", split="train")
    batch = [r for row in ds if (r := fmt(row.get("Context"), row.get("Response")))]
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 2. Therapy dialogue — real + synthetic, SFT-ready instruction/output
    print("Downloading fadodr/mental_health_therapy...")
    ds = load_dataset("fadodr/mental_health_therapy", split="train")
    batch = [r for row in ds if (r := fmt(row.get("instruction"), row.get("output")))]
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 3. 208K simulated psych conversations — largest single source
    print("Downloading IINOVAII/therapy-conversations-combined...")
    ds = load_dataset("IINOVAII/therapy-conversations-combined", split="train")
    batch = []
    for row in ds:
        instruction = (row.get("instruction") or "") + " " + (row.get("input") or "")
        r = fmt(instruction.strip(), row.get("output"))
        if r:
            batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 4. 99K synthetic therapy — llama-format, broad mental health
    print("Downloading vibhorag101/phr_mental_therapy_dataset...")
    ds = load_dataset("vibhorag101/phr_mental_therapy_dataset", split="train")
    batch = []
    for row in ds:
        text = row.get("text", "")
        # parse [INST] ... [/INST] format
        import re
        matches = re.findall(r'\[INST\](.*?)\[/INST\](.*?)(?=\[INST\]|$)', text, re.DOTALL)
        for instruction, output in matches:
            r = fmt(instruction.strip(), output.strip())
            if r:
                batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 5. MentalChat16K — 33 topics, relationships/anxiety/depression/intimacy
    print("Downloading ShenLab/MentalChat16K...")
    ds = load_dataset("ShenLab/MentalChat16K", split="train")
    batch = []
    for row in ds:
        instruction = row.get("instruction") or row.get("input") or row.get("question") or ""
        output = row.get("output") or row.get("response") or row.get("answer") or ""
        r = fmt(instruction, output)
        if r:
            batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 6. CounselChat — licensed therapists, high quality clinical language
    print("Downloading nbertagnolli/counsel-chat...")
    ds = load_dataset("nbertagnolli/counsel-chat", split="train")
    batch = []
    for row in ds:
        q = (row.get("questionTitle") or "") + " " + (row.get("questionText") or "")
        r = fmt(q.strip(), row.get("answerText"))
        if r:
            batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 7. CounselChat mirror — slightly different split/format
    print("Downloading mpingale/mental-health-chat-dataset...")
    ds = load_dataset("mpingale/mental-health-chat-dataset", split="train")
    batch = []
    for row in ds:
        q = (row.get("questionTitle") or "") + " " + (row.get("questionText") or "")
        r = fmt(q.strip(), row.get("answerText"))
        if r:
            batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 8. Psychotherapy — 20 conditions, staged sessions (intro/explore/advice/close)
    print("Downloading entfane/psychotherapy...")
    ds = load_dataset("entfane/psychotherapy", split="train")
    batch = []
    for row in ds:
        for key in ["question", "input", "prompt", "user"]:
            if row.get(key):
                for rkey in ["answer", "output", "response", "assistant"]:
                    if row.get(rkey):
                        r = fmt(row[key], row[rkey])
                        if r:
                            batch.append(r)
                        break
                break
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 9. PsyCoPref — chosen responses only for SFT (rejected used in DPO step 5)
    print("Downloading Psychotherapy-LLM/PsyCoPref (chosen only)...")
    ds = load_dataset("Psychotherapy-LLM/PsyCoPref", split="train")
    batch = []
    for row in ds:
        prompt = row.get("prompt") or row.get("question") or row.get("input") or ""
        chosen = row.get("chosen") or ""
        if isinstance(chosen, list):
            chosen = " ".join(chosen)
        r = fmt(prompt, chosen)
        if r:
            batch.append(r)
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

    # 10. Felladrin pretrain set — large pretraining corpus for domain adaptation
    print("Downloading Felladrin/pretrain-mental-health-counseling-conversations...")
    ds = load_dataset("Felladrin/pretrain-mental-health-counseling-conversations", split="train")
    batch = []
    for row in ds:
        for key in ["question", "input", "prompt", "context"]:
            if row.get(key):
                for rkey in ["answer", "output", "response"]:
                    if row.get(rkey):
                        r = fmt(row[key], row[rkey])
                        if r:
                            batch.append(r)
                        break
                break
    write(batch, f); print(f"  {len(batch)} records"); total += len(batch)

print(f"\nTotal records written: {total:,}")
print(f"Output: {OUT}")
