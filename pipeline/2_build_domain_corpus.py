"""
Step 2: Convert your research notes in /notes/ into fine-tuning pairs.

This reads every .md and .txt file from notes/{author}/ folders,
chunks them into passages, and generates instruction/output pairs
using a simple template so the model learns to APPLY the concepts,
not just recite them.

Run AFTER you've populated your notes folders:
  notes/durvasula/   — Ramani Durvasula research notes
  notes/freyd/       — Jennifer Freyd / DARVO / betrayal trauma
  notes/vaknin/      — Sam Vaknin / supply mechanics / shared fantasy
  notes/hughes/      — Chase Hughes / behavioral influence
  notes/navarro/     — Joe Navarro / nonverbal / body language
  notes/taylor/      — Jessica Taylor / victim-blaming / systemic
  notes/general/     — anything else: coercive control, IPV research, etc.

Run:
  python pipeline/2_build_domain_corpus.py

Output: pipeline/domain_pairs.jsonl
"""

import glob
import json
import os
import re

NOTES_DIR = os.path.join(os.path.dirname(__file__), "..", "notes")
OUT = os.path.join(os.path.dirname(__file__), "domain_pairs.jsonl")

AUTHOR_CONTEXT = {
    "durvasula": "Ramani Durvasula's framework on narcissistic abuse, covert and overt narcissism, idealize-devalue-discard cycles, love bombing, narcissistic injury, hoovering, and why victims stay.",
    "freyd": "Jennifer Freyd's betrayal trauma theory, DARVO (Deny Attack Reverse Victim and Offender), institutional betrayal, and why victims of trusted abusers dissociate from recognizing abuse.",
    "vaknin": "Sam Vaknin's analysis of narcissistic supply mechanics, the shared fantasy, narcissistic mortification, somatic vs cerebral narcissism, and why no contact disrupts the supply cycle.",
    "hughes": "Chase Hughes's behavioral influence stack, compliance triggers, rapport exploitation, identity anchoring, manufactured vulnerability as a weapon, and the profile of a manipulator.",
    "navarro": "Joe Navarro's nonverbal intelligence framework — limbic freeze/flight/fight responses, comfort and discomfort signals, territorial and dominance behavior, and how to read deception.",
    "taylor": "Jessica Taylor's analysis of victim-blaming as systemic mechanism, how mental health systems retraumatize survivors, why trauma responses are rational adaptations, and misuse of diagnosis to silence victims.",
    "general": "Research on coercive control, intimate partner violence, post-separation abuse, trauma bonding, intermittent reinforcement, and psychological manipulation.",
}

INSTRUCTION_TEMPLATES = [
    "Someone describes the following situation: {passage}\n\nWhat is happening here and what does the research say about this pattern?",
    "A person experiencing abuse asks: can you help me understand what this means? They wrote: {passage}",
    "Using the clinical literature on psychological abuse, analyze this: {passage}",
    "What behavioral pattern is operating in the following scenario, and what mechanism drives it? {passage}",
    "Someone has just described what is happening to them: {passage}\n\nName the tactic, explain the mechanism, and tell them what they need to know.",
]

import random
random.seed(42)


def chunk_text(text, min_len=80, max_len=600):
    chunks = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para) < min_len:
            continue
        if len(para) <= max_len:
            chunks.append(para)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for s in sentences:
                if len(current) + len(s) < max_len:
                    current += (" " if current else "") + s
                else:
                    if len(current) >= min_len:
                        chunks.append(current)
                    current = s
            if len(current) >= min_len:
                chunks.append(current)
    return chunks


def make_pair(chunk, author):
    template = random.choice(INSTRUCTION_TEMPLATES)
    instruction = template.format(passage=chunk)
    output = (
        f"Based on {AUTHOR_CONTEXT.get(author, 'the clinical literature on psychological abuse')}:\n\n"
        f"{chunk}"
    )
    return {"instruction": instruction, "output": output}


total = 0
with open(OUT, "w", encoding="utf-8") as f:
    for author in AUTHOR_CONTEXT:
        folder = os.path.join(NOTES_DIR, author)
        files = (
            glob.glob(os.path.join(folder, "**/*.md"), recursive=True)
            + glob.glob(os.path.join(folder, "**/*.txt"), recursive=True)
        )
        if not files:
            print(f"  [{author}] no files yet — add notes to notes/{author}/")
            continue

        count = 0
        for path in files:
            with open(path, "r", encoding="utf-8") as fp:
                text = fp.read()
            for chunk in chunk_text(text):
                pair = make_pair(chunk, author)
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                count += 1

        print(f"  [{author}] {count} pairs from {len(files)} files")
        total += count

print(f"\nTotal domain pairs: {total}")
print(f"Output: {OUT}")
