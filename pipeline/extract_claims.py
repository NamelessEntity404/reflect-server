"""
Claim extraction across all 10,792 pages.
Every sentence that makes a mechanistic claim → Q&A training pair.
Produces: claims_sft.jsonl
"""
import json, os, re
import pdfplumber

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)
OUT     = os.path.join(BASE, 'claims_sft.jsonl')

SYSTEM = """You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. You help people who are actively being abused understand what is being done to them. Clinical, direct, precise. No hedging. No therapist language. Commit early to a most-likely explanation. Every claim includes a causal chain and a falsifier."""

# Patterns that signal a mechanistic claim being made
CLAIM_STARTERS = [
    r'(This is (?:why|how|what|because))',
    r'(The (?:mechanism|reason|pattern|system|process|dynamic))',
    r'(What (?:you\'re|you are) (?:describing|experiencing|seeing))',
    r'(This (?:works|happens|occurs|functions) because)',
    r'(The (?:effect|result|outcome) (?:is|of))',
    r'(They (?:do this|use this|rely on) because)',
    r'(When (?:you|they|the) .{10,50} (?:it|this) (?:triggers|causes|creates))',
    r'(CLAIM:)',
    r'(This is (?:a|the) (?:textbook|classic|documented|known))',
    r'(What makes this .{5,30} is)',
    r'(The (?:narcissist|abuser|system|classifier) .{5,30} because)',
]

CLAIM_RE = re.compile('|'.join(CLAIM_STARTERS), re.I)

# Question templates for each claim type
def make_question(claim_text, context):
    low = claim_text.lower()
    if 'narcissist' in low or 'abuser' in low:
        return f"Why does an abuser do this: {claim_text[:80]}?"
    if 'classifier' in low or 'algorithm' in low or 'trust score' in low:
        return f"How does the classifier system handle this: {claim_text[:80]}?"
    if 'mechanism' in low or 'how' in low:
        return f"Explain the mechanism behind: {claim_text[:80]}"
    if 'textbook' in low or 'documented' in low or 'classic' in low:
        return f"What pattern is this and why does it work: {claim_text[:80]}?"
    return f"Explain what's happening here: {claim_text[:80]}"

def to_sft(question, answer):
    if len(question) < 20 or len(answer) < 80: return None
    return {'text': (
        f'<|begin_of_text|>'
        f'<|start_header_id|>system<|end_header_id|>\n\n{SYSTEM}<|eot_id|>'
        f'<|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|>'
        f'<|start_header_id|>assistant<|end_header_id|>\n\n{answer}<|eot_id|>'
    )}

def extract_claims_from_text(text, source):
    pairs = []
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 50: continue
        if not CLAIM_RE.search(sent): continue
        # Use surrounding context as the answer (sentence + next 2 sentences)
        context_end = min(i + 3, len(sentences))
        answer = ' '.join(sentences[i:context_end]).strip()
        if len(answer) < 100: continue
        if len(answer) > 2000: answer = answer[:2000]
        question = make_question(sent, answer)
        r = to_sft(question, answer)
        if r:
            pairs.append(r)
    return pairs

print('=== Claim Extraction — All 10,792 Pages ===\n')

all_pairs = []
seen = set()

for d in [AI_DIR, AI_DIR2]:
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.pdf'): continue
        path = os.path.join(d, fname)
        file_pairs = []
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text: continue
                    for r in extract_claims_from_text(text, fname):
                        key = r['text'][-150:]
                        if key not in seen:
                            seen.add(key)
                            file_pairs.append(r)
        except: pass
        if file_pairs:
            all_pairs.extend(file_pairs)
            print(f"  {len(file_pairs):4d} claim pairs  {fname[:65]}")

with open(OUT, 'w') as f:
    for r in all_pairs:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f'\nTotal claim pairs: {len(all_pairs):,}')
print(f'Output: {OUT}')
