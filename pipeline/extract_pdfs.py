"""
Extract training data from personal PDF conversation logs.
Processes page-by-page to avoid OOM on large files.

Run:
    python pipeline/extract_pdfs.py
"""

import json, os, re
import pdfplumber

PDF_DIR  = '/Users/nicoleackerman/Downloads/2024-2025 PDFS'
BASE     = os.path.dirname(__file__)
NOTES    = os.path.join(BASE, '..', 'notes', 'general')
SFT_OUT  = os.path.join(BASE, 'personal_sft.jsonl')

os.makedirs(NOTES, exist_ok=True)

SYSTEM = (
    "You are Reflect — a trauma-informed analysis tool built on the clinical research of "
    "Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. "
    "You help people who are actively being abused understand what is being done to them. "
    "Clinical, direct, precise. No hedging. No therapist language."
)

# AI responses with these = direct/good → SFT chosen
DIRECT = [
    "darvo","gaslighting","narcissistic","coercive control","love bombing",
    "cluster b","triangulation","supply","hoovering","idealize","devalue","discard",
    "smear campaign","flying monkeys","no contact","betrayal trauma","manipulation",
    "psychological abuse","this is textbook","this is a documented","the pattern here",
    "this is called","the mechanism","weaponized","epistemic","psychodrama",
    "character assassination","manufactured","coercive controller","semantic asymmetry",
]

# AI responses with these = hedging/gaslighting → skip or DPO rejected
HEDGE = [
    "it sounds like","it seems like","both of you","both sides","couples therapy",
    "have you considered their","their perspective","i can't verify",
    "without more information","there could be many explanations",
    "i'm not able to diagnose","misunderstanding","that must be hard",
    "try to understand where they","see it from their",
]

def to_llama3(user, ai):
    if len(user) < 20 or len(ai) < 40 or len(ai) > 3000:
        return None
    return {"text": (
        f"<|begin_of_text|>"
        f"<|start_header_id|>system<|end_header_id|>\n\n{SYSTEM}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n{ai}<|eot_id|>"
    )}

def classify(text):
    low = text.lower()
    d = sum(1 for s in DIRECT if s in low)
    h = sum(1 for s in HEDGE if s in low)
    if d >= 2 and h == 0: return 'direct'
    if h >= 2: return 'hedge'
    return 'neutral'

def parse_turns(text):
    """Extract (user, ai) pairs from 'You said:' / 'ChatGPT said:' format."""
    parts = re.split(r'(You said:|ChatGPT said:|Claude said:)', text)
    turns = []
    for i in range(1, len(parts)-1, 2):
        marker  = parts[i]
        content = parts[i+1].strip() if i+1 < len(parts) else ''
        if len(content) < 20:
            continue
        speaker = 'user' if 'You said' in marker else 'ai'
        turns.append((speaker, content))

    pairs = []
    for i in range(len(turns)-1):
        if turns[i][0] == 'user' and turns[i+1][0] == 'ai':
            pairs.append((turns[i][1], turns[i+1][1]))
    return pairs

def stream_pdf(path, max_pages=None):
    """Yield text one page at a time — never loads whole PDF."""
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        for page in pages:
            t = page.extract_text()
            if t:
                yield t

def process_conversation_pdf(path, label, sft_file, max_pages=None):
    """Stream a conversation PDF and write SFT pairs incrementally."""
    buffer = ''
    total_pairs = 0
    direct = 0

    for page_text in stream_pdf(path, max_pages):
        buffer += '\n' + page_text
        # Keep buffer manageable — only last 8K chars carry-over for context
        if len(buffer) > 16000:
            pairs = parse_turns(buffer)
            for user, ai in pairs:
                cls = classify(ai)
                if cls == 'direct':
                    r = to_llama3(user[:1200], ai[:2000])
                    if r:
                        sft_file.write(json.dumps(r, ensure_ascii=False) + '\n')
                        direct += 1
                total_pairs += 1
            buffer = buffer[-4000:]  # keep tail for cross-page turns

    # Final flush
    pairs = parse_turns(buffer)
    for user, ai in pairs:
        cls = classify(ai)
        if cls == 'direct':
            r = to_llama3(user[:1200], ai[:2000])
            if r:
                sft_file.write(json.dumps(r, ensure_ascii=False) + '\n')
                direct += 1
        total_pairs += 1

    print(f"  {label}: {total_pairs} turns → {direct} direct SFT pairs")
    return direct

def save_notes(path, label, filename, max_pages=10):
    """Save first N pages of a PDF to notes folder."""
    text = ''
    for page_text in stream_pdf(path, max_pages):
        text += page_text + '\n\n'
    out = os.path.join(NOTES, filename)
    with open(out, 'w') as f:
        f.write(f"# {label}\n\n{text}")
    print(f"  → notes/{filename} ({len(text)} chars)")


print("\n=== Reflect Training Data Extraction ===\n")
total = 0

with open(SFT_OUT, 'w') as sft:

    # 1. NLP Cluster B — 24 pages, pure gold
    print("1. NLP and Narrative Control (Cluster B)...")
    path = os.path.join(PDF_DIR, 'NLP and Narrative Control Dealing with Cluster B Styles.pdf')
    save_notes(path, 'Cluster B NLP and Narrative Control', 'cluster_b_dynamics.md', max_pages=24)
    total += process_conversation_pdf(path, 'Cluster B', sft)

    # 2. Legal Conflict — 878 pages, stream carefully, cap at 400 pages
    print("\n2. Legal Conflict Living Situation (878 pages, capped at 400)...")
    path = os.path.join(PDF_DIR, 'Legal Filings GPT - Legal Conflict Living Situation.pdf')
    save_notes(path, 'Legal Conflict Documentation', 'legal_conflict.md', max_pages=5)
    total += process_conversation_pdf(path, 'Legal Conflict', sft, max_pages=400)

    # 3. Full Thread Legal Filings — 66 pages
    print("\n3. Full Thread Legal Filings...")
    path = os.path.join(PDF_DIR, 'Full Thread Legal Filings GPT.pdf')
    total += process_conversation_pdf(path, 'Legal Filings', sft)

    # 4. Emotional Economy → notes only
    print("\n4. Emotional Economy → notes...")
    path = os.path.join(PDF_DIR, 'EMOTIONAL ECONOMY.pdf')
    save_notes(path, 'Emotional Economy — Abuse Conditioning', 'emotional_economy.md', max_pages=3)

    # 5. RLHF RAG research → notes
    print("\n5. RLHF RAG research → notes...")
    path = os.path.join(PDF_DIR, 'rlhf rag retrieval mixure of expert think tanks ive created.pdf')
    save_notes(path, 'RLHF RAG Research Notes', 'rlhf_research.md', max_pages=14)

    # 6. 200k Year GPT Brand Depth — 615 pages, cap at 200
    print("\n6. 200k Year GPT (capped at 200 pages)...")
    path = os.path.join(PDF_DIR, '200k A Year GPT - Building Brand Depth.pdf')
    total += process_conversation_pdf(path, '200k GPT Brand', sft, max_pages=200)

    # 7. Latent Space ML theory → notes
    print("\n7. Latent Space ML theory → notes...")
    path = os.path.join(PDF_DIR, 'Latent Space Softmax function Poetry Tokenization Embedding Position Encvoding Probabilty Distributions Temprature and Entroy-2.pdf')
    save_notes(path, 'Latent Space ML Theory', 'latent_space_ml.md', max_pages=10)

print(f"\n=== Done ===")
print(f"Total SFT pairs extracted: {total}")
print(f"Output: {SFT_OUT}")
print(f"Notes:  {NOTES}")
