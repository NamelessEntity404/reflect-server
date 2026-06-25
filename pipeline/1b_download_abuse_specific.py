"""
Step 1b: Download abuse-specific and manipulation-specific datasets.
These are separate from the general therapy data in 1_download_datasets.py
because they need different processing — they're not instruction/output pairs,
they're raw text, annotations, or Reddit posts that need conversion.

Run AFTER step 1:
  python pipeline/1b_download_abuse_specific.py

Output: pipeline/raw_abuse_specific.jsonl
"""

import json
import os
import re
from datasets import load_dataset

OUT = os.path.join(os.path.dirname(__file__), "raw_abuse_specific.jsonl")

MANIPULATION_TECHNIQUES = {
    "Persuasion or Seduction": "love bombing, flattery as a weapon, manufactured intimacy to extract compliance",
    "Intimidation": "implicit or explicit threats, creating fear without direct statement",
    "Rationalization": "reframing abuse as reasonable, logical-sounding justifications for harmful behavior",
    "Accusation": "preemptive blame, accusing the victim of what the abuser is doing (projection)",
    "Evasion": "deflection, subject-changing, word salad, non-answers to direct questions",
    "Shaming or Belittlement": "contempt as control, making the victim feel fundamentally defective",
    "Playing Victim Role": "DARVO mechanics — reversing victim and offender, manufacturing grievance",
    "Denial": "gaslighting at its core — denying documented reality, making the victim doubt perception",
}

VULNERABILITY_TARGETS = {
    "Dependency": "trauma bonding, manufactured need, intermittent reinforcement creating addiction to approval",
    "Low Self-Esteem": "targeting self-doubt, amplifying insecurity through devalue phase",
    "Naivety": "exploiting trust, good faith, and assumption that others operate honestly",
    "Emotional Sensitivity": "weaponizing empathy — the victim's care becomes the lever",
}


def write(records, f):
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")


def fmt(instruction, output):
    if not instruction or not output:
        return None
    instruction, output = str(instruction).strip(), str(output).strip()
    if len(instruction) < 20 or len(output) < 30 or len(output) > 3000:
        return None
    return {"instruction": instruction, "output": output}


total = 0

with open(OUT, "w", encoding="utf-8") as f:

    # ── 1. MentalManip — 4K annotated manipulation dialogues ────────────────
    # Convert: dialogue + technique label → clinical analysis of what's happening
    print("Downloading audreyeleven/MentalManip...")
    try:
        ds = load_dataset("audreyeleven/MentalManip", split="train")
        batch = []
        for row in ds:
            dialogue = row.get("dialogue") or row.get("text") or row.get("conversation") or ""
            technique = row.get("technique") or row.get("manipulation_technique") or row.get("label") or ""
            is_manipulative = row.get("label") == 1 or row.get("manipulative") == True or str(row.get("manipulation", "")).lower() == "true"

            if not dialogue or not is_manipulative:
                continue

            technique_str = str(technique).strip() if technique else "psychological manipulation"
            explanation = MANIPULATION_TECHNIQUES.get(technique_str, "a documented manipulation tactic used to control the target's behavior or perception")

            instruction = f"Analyze this conversation for manipulation tactics:\n\n{dialogue}"
            output = (
                f"This conversation exhibits {technique_str} — {explanation}.\n\n"
                f"The manipulation operates by targeting the victim's psychological state through language "
                f"designed to alter their perception, create compliance, or undermine their ability to "
                f"accurately assess what is happening to them. This is a documented pattern in psychological "
                f"abuse and coercive control literature.\n\n"
                f"Key indicators in this exchange: the power dynamic is asymmetric, the manipulator "
                f"controls the frame of the conversation, and the target's natural responses are being "
                f"used against them."
            )
            r = fmt(instruction, output)
            if r:
                batch.append(r)

        write(batch, f)
        print(f"  {len(batch)} records")
        total += len(batch)
    except Exception as e:
        print(f"  SKIP: {e}")


    # ── 3. CBT-Bench → cognitive distortion identification ──────────────────
    print("Downloading Psychotherapy-LLM/CBT-Bench...")
    try:
        ds = load_dataset("Psychotherapy-LLM/CBT-Bench", split="train")
        batch = []
        for row in ds:
            question = row.get("question") or row.get("input") or row.get("prompt") or ""
            answer = row.get("answer") or row.get("output") or row.get("response") or ""
            r = fmt(question, answer)
            if r:
                batch.append(r)
        write(batch, f)
        print(f"  {len(batch)} records")
        total += len(batch)
    except Exception as e:
        print(f"  SKIP: {e}")

print(f"\nTotal abuse-specific records: {total:,}")
print(f"Output: {OUT}")
