"""
Paragraph-level RAG chunking across all 10,792 pages.
Every substantive paragraph becomes a retrieval document.
Produces: rag_chunks.jsonl — the retrieval corpus Reflect uses at inference time.
"""
import json, os, re
import pdfplumber

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)
OUT     = os.path.join(BASE, 'rag_chunks.jsonl')

# Minimum paragraph quality
MIN_WORDS = 40
MAX_WORDS = 400

SKIP_PATTERNS = [
    r'^\s*\d+\s*$',           # page numbers
    r'^(You said|ChatGPT said|Claude said)',  # dialogue markers
    r'^\s*[•●▪◦\-]\s*$',     # lone bullets
    r'FontBBox',
]

HIGH_VALUE_SIGNALS = [
    'narciss','gaslighting','darvo','coercive','cluster b','trauma','manipulation',
    'classifier','trust score','metadata','fingerprint','suppression','algorithm',
    'mechanism','pattern','structurally','operationally','forensic','evidence',
    'the reason','because','this works','this happens','this is how','what this means',
    'CLAIM','CAUSE','This would be wrong','Next.*observe',
    'no contact','betrayal','supply','hoovering','love bombing',
    'behavioral','signal','detection','propagation','identity',
]

def is_skip(text):
    text = text.strip()
    if not text: return True
    for pat in SKIP_PATTERNS:
        if re.search(pat, text, re.I): return True
    return False

def quality_score(text):
    low = text.lower()
    score = 0
    words = len(text.split())
    if words < MIN_WORDS: return 0
    if words > MAX_WORDS: return 0
    for sig in HIGH_VALUE_SIGNALS:
        if sig.lower() in low:
            score += 2
    # Prefer paragraphs with concrete claims
    if any(c in text for c in ['CLAIM:', 'CAUSE:', 'This would be wrong', 'the mechanism']):
        score += 5
    return score

def extract_chunks(pdf_path, source_name):
    chunks = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text: continue
                # Split into paragraphs
                paragraphs = re.split(r'\n{2,}', text)
                for para in paragraphs:
                    para = para.strip()
                    if is_skip(para): continue
                    score = quality_score(para)
                    if score > 0:
                        chunks.append({
                            'text': para,
                            'source': source_name,
                            'page': page_num + 1,
                            'score': score,
                        })
    except Exception as e:
        pass
    return chunks

print('=== RAG Chunk Extraction — All 10,792 Pages ===\n')

all_chunks = []
seen = set()

for d in [AI_DIR, AI_DIR2]:
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.pdf'): continue
        path = os.path.join(d, fname)
        chunks = extract_chunks(path, fname[:60])
        # Dedup within file
        new = 0
        for c in chunks:
            key = c['text'][:100]
            if key not in seen:
                seen.add(key)
                all_chunks.append(c)
                new += 1
        if new > 0:
            print(f"  {new:4d} chunks  {fname[:65]}")

# Sort by quality score, write top chunks
all_chunks.sort(key=lambda x: -x['score'])

with open(OUT, 'w') as f:
    for c in all_chunks:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')

print(f'\nTotal RAG chunks: {len(all_chunks):,}')
print(f'High score (>=4): {sum(1 for c in all_chunks if c["score"] >= 4):,}')
print(f'Output: {OUT}')
