"""
Master extraction — runs ALL methods simultaneously across all 10,792 pages.

Methods:
  1. Multi-turn windows: 3-turn, 5-turn, 8-turn (dialogue files)
  2. DPO pushback pairs (dialogue files)
  3. Paragraph RAG chunks (all files)
  4. Claim extraction → Q&A pairs (all files)
  5. Instruction step extraction (operational docs)
  6. Doc-only synthesis → Q&A from polished research docs
  7. Cross-document mechanism pairs

Run: .venv/bin/python pipeline/extract_all.py
"""

import json, os, re, hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import pdfplumber

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)

# ── Output files ──────────────────────────────────────────────────────────────
OUT = {
    'sft_3turn':    os.path.join(BASE, 'windows_3turn_sft.jsonl'),
    'sft_5turn':    os.path.join(BASE, 'master_sft.jsonl'),
    'sft_8turn':    os.path.join(BASE, 'windows_8turn_sft.jsonl'),
    'dpo':          os.path.join(BASE, 'master_dpo.jsonl'),
    'rag':          os.path.join(BASE, 'rag_chunks.jsonl'),
    'claims':       os.path.join(BASE, 'claims_sft.jsonl'),
    'instructions': os.path.join(BASE, 'instructions_sft.jsonl'),
    'doc_qa':       os.path.join(BASE, 'doc_qa_sft.jsonl'),
}

# ── System prompts ────────────────────────────────────────────────────────────
SYS = {
    'reflect': """You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. Clinical, direct, precise. No hedging. No therapist language. No em-dashes. Commit early to a most-likely explanation. Every claim includes a causal chain and a falsifier. AXIS LOCK: answer only the exact question asked. HEDGING CAP: 6 or fewer hedging words total.""",
    'forensic': """You are Reflect — a forensic analyst at the intersection of behavioral pattern recognition, legal documentation, and adversarial systems analysis. Direct, precise, case-specific. No hedging. Commit to the most likely explanation given the evidence.""",
    'technical': """You are Reflect — a technical analyst specializing in platform classifier behavior, trust score mechanics, metadata forensics, and adversarial AI systems. No hedging. Mechanistic, precise, PhD-level without academic fog.""",
    'brand': """You are Reflect — a direct strategic advisor. No bobblehead responses. No to-do lists. Answer the exact question on the exact axis asked. Push back when the premise is wrong. Produce new information, not meta-commentary.""",
    'crisis': """You are Reflect — operating at the edge of crisis. No softening. No backtracking. Full. Commit completely. Do not protect the user from clarity — give them clarity as a weapon.""",
}

TRAUMA_SIG = ['narcissist','gaslighting','darvo','coercive','cluster b','trauma','manipulation',
    'betrayal','idealize','devalue','discard','supply','hoovering','love bombing','stalking',
    'grooming','no contact','smear','flying monkeys','psychological homicide','suicide engineering']
FORENSIC_SIG = ['evidence','filing','court','legal','probate','estate','murder','scam','fraud',
    'attempted','forensic','incident','bolt','arc','wire','cfaa','affidavit','plaintiff']
TECHNICAL_SIG = ['classifier','trust score','metadata','fingerprint','suppression','propagation',
    'algorithm','node','graph','botnet','ip address','proxy','vpn','burner','drone','singleton',
    'softmax','embedding','token','latent space','rlhf','rag','lora','fine-tun','guardrail']
BRAND_SIG = ['shirt','brand','post','caption','content','creator','linkedin','tiktok','portfolio',
    'design','copy','marketing','revenue','strategy','viral','engagement','follower','aesthetic']
CRISIS_SIG = ['kill myself','suicide','hotline','want to die','no exit','psychological murder',
    'forced cognitive','no softening','unfiltered map','ready when you say']
HEDGE_PHRASES = ["it sounds like","it seems like","both of you","have you considered",
    "it depends","in summary","generally","i hear you","great question",
    "mental health professional","i'm not able to diagnose","without more information"]
PUSHBACK = ["you're not saying anything","generic bullshit","not what i","lowest hanging fruit",
    "fake shit","full of shit","not actionable","toy world","thats wrong","you missed",
    "piece of shit","worded like","nonsense","corny ass","to do list","bobblehead"]

TURN_RE = re.compile(r'(You said\s*:\s*\n|ChatGPT said\s*:\s*\n|Claude said\s*:\s*\n|'
                      r'Claude responded\s*:\s*\n|Assistant\s*:\s*\n|Human\s*:\s*\n)', re.I)

CLAIM_RE = re.compile(r'(This is (?:why|how|what|because)|The (?:mechanism|reason|pattern)|'
    r'What (?:you\'re|you are) (?:describing|experiencing)|This (?:works|happens) because|'
    r'CLAIM:|This is (?:a|the) (?:textbook|classic|documented)|'
    r'The (?:narcissist|abuser|system|classifier) .{5,40} because)', re.I)

INSTRUCTION_RE = re.compile(r'^(?:\d+\.|Step \d+|Phase \d+|[•●▪])\s+(.{20,})', re.M)

# ── Helpers ───────────────────────────────────────────────────────────────────

def fingerprint(text):
    return hashlib.md5(text[-120:].encode()).hexdigest()

def route_system(text):
    low = text.lower()
    if any(s in low for s in CRISIS_SIG): return SYS['crisis']
    if any(s in low for s in FORENSIC_SIG): return SYS['forensic']
    if any(s in low for s in TECHNICAL_SIG): return SYS['technical']
    if any(s in low for s in BRAND_SIG): return SYS['brand']
    return SYS['reflect']

def count_hedges(text):
    low = text.lower()
    return sum(1 for p in HEDGE_PHRASES if p in low)

def is_pushback(text):
    low = text.lower()
    return any(p in low for p in PUSHBACK)

def sft_record(turns, system):
    text = f'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>'
    for role, content in turns:
        text += f'<|start_header_id|>{role}<|end_header_id|>\n\n{content[:3000]}<|eot_id|>'
    return {'text': text}

def qa_record(question, answer, system):
    if len(question) < 15 or len(answer) < 60: return None
    return sft_record([('user', question[:1500]), ('assistant', answer[:3000])], system)

def get_full_text(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += '\n' + t
    return text

def parse_turns(text):
    parts = TURN_RE.split(text)
    turns = []
    for i in range(1, len(parts)-1, 2):
        marker  = parts[i].lower()
        content = parts[i+1].strip() if i+1 < len(parts) else ''
        if len(content) < 15: continue
        is_user = any(m in marker for m in ['you said','human','user'])
        turns.append(('user' if is_user else 'assistant', content))
    return turns

# ── Per-file extraction ───────────────────────────────────────────────────────

def process_file(args):
    pdf_path, fname = args
    results = {k: [] for k in OUT}
    seen = set()

    def add(key, record):
        if not record: return
        fp = fingerprint(record.get('text', str(record)))
        if fp not in seen:
            seen.add(fp)
            results[key].append(record)

    try:
        full_text = get_full_text(pdf_path)
    except Exception as e:
        return results, fname, str(e)

    turns = parse_turns(full_text)
    has_dialogue = len(turns) >= 4

    # ── Methods 1 & 2: multi-turn windows + DPO ──────────────────────────────
    if has_dialogue:
        for window_size, key in [(3, 'sft_3turn'), (5, 'sft_5turn'), (8, 'sft_8turn')]:
            stride = max(1, window_size // 2)
            for i in range(0, len(turns) - 1, stride):
                end = min(i + window_size, len(turns))
                while end > i and turns[end-1][0] != 'assistant':
                    end -= 1
                if end <= i + 1: continue
                w = turns[i:end]
                if w[0][0] != 'user': continue
                if w[-1][0] != 'assistant': continue
                last_ai = w[-1][1]
                if count_hedges(last_ai) >= 4: continue
                if len(last_ai) < 80: continue
                sys = route_system(' '.join(t[1] for t in w))
                add(key, sft_record(w, sys))

        # DPO pushback pairs
        for i in range(len(turns) - 3):
            t0, t1, t2, t3 = turns[i], turns[i+1], turns[i+2], turns[i+3]
            if not (t0[0]=='user' and t1[0]=='assistant' and t2[0]=='user' and t3[0]=='assistant'):
                continue
            if is_pushback(t2[1]) and len(t3[1]) > 100:
                add('dpo', {
                    'prompt': t0[1][:2000],
                    'rejected': t1[1][:3000],
                    'chosen': t3[1][:3000],
                    'pushback': t2[1][:400],
                    'source': fname
                })

    # ── Method 3: RAG paragraph chunks ───────────────────────────────────────
    HIGH_VAL = ['narciss','gaslighting','darvo','mechanism','pattern','structurally',
        'classifier','trust score','the reason','because','this works','CLAIM','CAUSE',
        'no contact','betrayal','supply','behavioral','signal','detection','forensic']

    for para in re.split(r'\n{2,}', full_text):
        para = para.strip()
        words = para.split()
        if len(words) < 35 or len(words) > 350: continue
        if re.match(r'^(You said|ChatGPT said|Claude said)', para): continue
        score = sum(2 for s in HIGH_VAL if s.lower() in para.lower())
        if score > 0:
            fp = fingerprint(para)
            if fp not in seen:
                seen.add(fp)
                results['rag'].append({'text': para, 'source': fname, 'score': score})

    # ── Method 4: Claim extraction → Q&A ─────────────────────────────────────
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 50 or not CLAIM_RE.search(sent): continue
        answer = ' '.join(sentences[i:min(i+3, len(sentences))]).strip()
        if len(answer) < 100 or len(answer) > 2500: continue
        low = sent.lower()
        if 'narcissist' in low or 'abuser' in low:
            q = f"Why does an abuser behave this way: {sent[:80]}?"
        elif 'classifier' in low or 'trust score' in low:
            q = f"How does the detection system handle: {sent[:80]}?"
        elif 'mechanism' in low:
            q = f"What is the mechanism behind: {sent[:80]}?"
        elif 'textbook' in low or 'classic' in low:
            q = f"What pattern is this and why does it work: {sent[:80]}?"
        else:
            q = f"Explain what is happening here: {sent[:80]}"
        sys = route_system(answer)
        add('claims', qa_record(q, answer, sys))

    # ── Method 5: Instruction step extraction ────────────────────────────────
    for match in INSTRUCTION_RE.finditer(full_text):
        step = match.group(0).strip()
        # Get following explanation (next 150 words)
        pos = match.end()
        following = full_text[pos:pos+800].split('\n\n')[0].strip()
        if len(following) < 80: continue
        full_instruction = f"{step}\n\n{following}"
        q = f"How do you {step[:80].lstrip('0123456789. ')}?"
        sys = route_system(full_instruction)
        add('instructions', qa_record(q, full_instruction, sys))

    # ── Method 6: Doc-only Q&A synthesis ────────────────────────────────────
    # For DOC files (no dialogue), extract key paragraphs as Q&A
    if not has_dialogue:
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text)
                      if len(p.strip().split()) > 60]
        for para in paragraphs[:30]:  # top 30 paragraphs per doc
            words = para.split()
            if len(words) > 400: para = ' '.join(words[:400])
            low = para.lower()
            if 'narcissist' in low or 'abuse' in low or 'coercive' in low:
                q = "Explain this pattern of psychological abuse and its mechanism."
            elif 'classifier' in low or 'trust score' in low or 'algorithm' in low:
                q = "Explain how this platform detection system works."
            elif 'legal' in low or 'evidence' in low or 'court' in low:
                q = "Explain this legal situation and what it means strategically."
            else:
                q = "Explain this concept and its implications."
            sys = route_system(para)
            add('doc_qa', qa_record(q, para, sys))

    return results, fname, None

# ── Main ──────────────────────────────────────────────────────────────────────

print('=== Master Extraction — All Methods, All Files ===\n')

# Collect all PDF paths
all_files = []
for d in [AI_DIR, AI_DIR2]:
    for fname in os.listdir(d):
        if fname.endswith('.pdf'):
            all_files.append((os.path.join(d, fname), fname))

print(f'Processing {len(all_files)} PDFs with all extraction methods...\n')

# Open all output files
handles = {k: open(v, 'w') for k, v in OUT.items()}
totals  = {k: 0 for k in OUT}
global_seen = set()

for pdf_path, fname in sorted(all_files, key=lambda x: -os.path.getsize(x[0])):
    results, name, err = process_file((pdf_path, fname))
    if err:
        print(f'  ERR {name[:50]}: {err}')
        continue

    file_totals = {}
    for key, records in results.items():
        written = 0
        for rec in records:
            fp = fingerprint(rec.get('text', str(rec)))
            if fp not in global_seen:
                global_seen.add(fp)
                handles[key].write(json.dumps(rec, ensure_ascii=False) + '\n')
                totals[key] += 1
                written += 1
        if written > 0:
            file_totals[key] = written

    if file_totals:
        summary = ' | '.join(f'{k}:{v}' for k, v in file_totals.items())
        print(f'  {name[:55]:55s} {summary}')

for h in handles.values():
    h.close()

print(f'\n{"="*60}')
print('TOTALS:')
for key, count in totals.items():
    print(f'  {key:20s}: {count:,}')
print(f'\nGrand total unique records: {sum(totals.values()):,}')
