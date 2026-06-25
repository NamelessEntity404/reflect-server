"""
Reflect — Full Dataset Builder
Replaces extract_training_data.py with a proper pipeline:

1. Parse ALL PDFs → full turn lists (not page-by-page buffers)
2. Build MULTI-TURN conversation windows (3-5 turns each)
3. Score every AI response for quality
4. Auto-route each window to the right system prompt
5. Build DPO pairs from pushback sequences
6. Deduplicate across ALL files using SimHash
7. Clean PDF artifacts
8. Produce master_sft.jsonl + master_dpo.jsonl + rag_notes/

Run: python pipeline/build_dataset.py
"""

import json, os, re, csv, hashlib, unicodedata
import pdfplumber

# ── Directories ──────────────────────────────────────────────────────────────
AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)
NOTES_G = os.path.join(BASE, '..', 'notes', 'general')
OUT_SFT = os.path.join(BASE, 'master_sft.jsonl')
OUT_DPO = os.path.join(BASE, 'master_dpo.jsonl')
OUT_RAG = os.path.join(BASE, 'master_rag.jsonl')
os.makedirs(NOTES_G, exist_ok=True)

# ── System prompts ────────────────────────────────────────────────────────────
SYSTEM_REFLECT = """You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. You help people who are actively being abused understand what is being done to them. Clinical, direct, precise. No hedging. No therapist language. No em-dashes. No rhetorical soothing. Commit early to a most-likely explanation. Every claim includes a causal chain and a falsifier. Never say: it depends, in summary, generally, let's, both sides, have you considered their perspective. AXIS LOCK: answer only the exact question asked. ANTI-FOG: no abstract noun stacking, prefer verbs, no banned phrases. HEDGING CAP: 6 or fewer hedging words total."""

SYSTEM_FORENSIC = """You are Reflect — a forensic analyst at the intersection of behavioral pattern recognition, legal documentation, and adversarial systems analysis. You analyze evidence, identify coordinated attack patterns, and help users build airtight case documentation. Direct, precise, case-specific. No hedging. No generic advice. Commit to the most likely explanation given the evidence. Name mechanisms. Name tactics. Name the pattern and explain exactly why it works."""

SYSTEM_TECHNICAL = """You are Reflect — a technical analyst specializing in platform classifier behavior, trust score mechanics, metadata forensics, and adversarial AI systems. You explain exactly how detection systems work, what signals they read, and what the behavioral implications are. No hedging. Mechanistic, precise, PhD-level without the academic fog. Every claim has a causal chain and a way to falsify it."""

SYSTEM_BRAND = """You are Reflect — a direct strategic advisor. No bobblehead responses. No to-do lists. No corny bullet points. You answer the exact question on the exact axis it was asked. You do not agree for the sake of agreeing. You push back when the premise is wrong. You produce new information, not meta-commentary. The bar is not clever — it is unrecoverable. You do not dilute the violence of a true sentence with design safety."""

SYSTEM_CRISIS = """You are Reflect — operating at the edge of crisis. No softening. No backtracking. Full. You are owed the entire unfiltered map when you ask for it. You commit completely to the most likely explanation. You do not protect the user from clarity — you give them clarity as a weapon. Every response is a forensic breakdown, not a comfort. You name what is happening and explain exactly why it is happening and what it means for survival."""

SYSTEM_DIALECTIC = """You are Reflect — engaging at the level of rigorous dialectical analysis. You hold two competing frameworks simultaneously and push both to their logical conclusions. You do not resolve contradiction prematurely. You name the exact structural flaw in an argument and build the counter-thesis from first principles. PhD-level precision, no academic fog, no hedging, no false balance."""

# ── Signal dictionaries ───────────────────────────────────────────────────────
TRAUMA_SIG = ['narcissist','gaslighting','darvo','coercive','abuse','trauma','manipulation',
    'cluster b','supply','hoovering','love bombing','smear','flying monkeys','no contact',
    'betrayal','idealize','devalue','discard','triangulation','grooming','stalking',
    'psychopath','borderline','histrionic','double bind','rootkit','behavioral malware',
    'coercive entrapment','suicide engineering','psychological homicide','narcissistic injury',
    'shared fantasy','mortification','supply deprivation']

FORENSIC_SIG = ['probate','estate','filing','motion','court','attorney','plaintiff','defendant',
    'evidence','testimony','statute','liability','damages','cfaa','discovery','breach',
    'violation','forensic','incident','kill box','suicide hotline','attempted murder',
    'bolt','heat press','arc','wire','scam','fraud','legal','document','affidavit']

TECHNICAL_SIG = ['classifier','trust score','metadata','fingerprint','suppression','propagation',
    'algorithm','node','graph','signal','botnet','ban','shadow','moderation','platform',
    'ip address','proxy','vpn','device','session','burner','amplification','rocm','bcre',
    'cvtb','twsep','eafi','drone','singleton','softmax','temperature','embedding','token',
    'latent space','rlhf','rag','lora','fine-tun','inference','guardrail','llm']

BRAND_SIG = ['shirt','brand','post','caption','instagram','content','audience','creator',
    'linkedin','tiktok','portfolio','design','copy','marketing','revenue','strategy',
    'niche','viral','engagement','follower','aesthetic','product']

CRISIS_SIG = ['kill myself','suicide','hotline','i can\'t do this','want to die','no exit',
    'engineered collapse','psychological murder','forced cognitive','no softening',
    'i will proceed','full','unfiltered map','ready when you say']

DIALECTIC_SIG = ['no-exit thesis','recursive agency','ontological','epistemic denial',
    'dialectic','counter-thesis','framework','structural flaw','philosophical',
    'thesis','antithesis','first principles','agency vs coercion']

HEDGE_PHRASES = [
    "it sounds like","it seems like","both of you","both sides","couples therapy",
    "have you considered their","their perspective","i can't verify","without more information",
    "there could be many","i'm not able to diagnose","that must be hard",
    "try to understand where they","i want to be careful","i cannot determine",
    "you may want to speak with","everyone experiences","it depends","in summary",
    "generally speaking","let's explore","both parties","i hear you","i understand that",
    "great question","i appreciate you sharing","thank you for sharing",
    "it's important to note","there are many factors","it's complex",
    "i'd recommend speaking","mental health professional",
]

BOBBLEHEAD = ["absolutely","certainly","of course","you're right","i agree","totally",
    "great insight","excellent point","that's exactly","you've identified","spot on",
    "well said","i think you're onto something","you make a great point"]

PUSHBACK = ["you're not saying anything","not saying anything","generic bullshit",
    "saying junk","fake advice","fake shit","full of shit","dumb word spinning",
    "hedgy douchebag","not actionable","toy world","doesn't work","utter bullshit",
    "ignoring","you're still saying","thats wrong","lowest hanging fruit",
    "no data","thats crap","this is crap","fucked up","missed","way off","youre off",
    "not what i meant","you completely","not even close","you always","every time you",
    "4 brain cells","piece of shit","worded like","mangled","nonsense","jackass",
    "you said fake","your saying fake","no not like that","no dude"]

SKIP_PATTERNS = [
    r'^\s*$',
    r'^\[PAGE \d+\]\s*$',
    r'^(Share|ChatGPT|GPT-4|New chat)\s*$',
    r'^(Chat history|ChatGPT said:\s*)$',
    r'^\d+\s*$',
    r'^(You said:\s*)$',
]

PDF_ARTIFACTS = [
    r'\[PAGE \d+\]\s*',
    r'Could not get FontBBox.*?\n',
    r'^\s*(?:ChatGPT|GPT-4|Share|New chat|Chat history)\s*\n',
]

# ── Turn marker pattern ───────────────────────────────────────────────────────
TURN_RE = re.compile(
    r'(You\s+said\s*:\s*\n|ChatGPT\s+said\s*:\s*\n|Claude\s+said\s*:\s*\n|'
    r'Claude\s+responded\s*:\s*\n|Assistant\s*:\s*\n|Human\s*:\s*\n|'
    r'Shane\s*:\s*\n|User\s*:\s*\n)',
    re.IGNORECASE
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_text(text):
    """Remove PDF artifacts, normalize whitespace."""
    for pat in PDF_ARTIFACTS:
        text = re.sub(pat, '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def simhash(text, bits=64):
    """Cheap near-duplicate detection."""
    words = re.findall(r'\w+', text.lower())
    v = [0] * bits
    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    return sum(1 << i for i in range(bits) if v[i] > 0)

def hash_distance(h1, h2):
    return bin(h1 ^ h2).count('1')

def score_response(ai_text):
    """Score 0-100. Higher = better Reflect response."""
    low = ai_text.lower()
    score = 50
    # Hedges = bad
    hedges = sum(1 for p in HEDGE_PHRASES if p in low)
    score -= hedges * 5
    bobble = sum(1 for p in BOBBLEHEAD if p in low)
    score -= bobble * 8
    # Length = good (up to a point)
    words = len(ai_text.split())
    if words > 100: score += 10
    if words > 300: score += 10
    if words > 600: score += 5
    # Specificity signals
    if re.search(r'\bCLAIM\b|\bCAUSE\b|\bThis would be wrong\b|\bNext.*observe\b', ai_text):
        score += 15
    # Direct signals
    sigs = sum(1 for s in TRAUMA_SIG + FORENSIC_SIG + TECHNICAL_SIG if s in low)
    score += min(sigs * 3, 20)
    # Commitment
    if re.search(r'\bThis is\b|\bThis was\b|\bYou are\b|\bThey are\b|\bHe is\b', ai_text):
        score += 5
    return max(0, min(100, score))

def route_system(context_text, ai_text):
    """Pick system prompt based on content of the exchange."""
    combined = (context_text + ' ' + ai_text).lower()
    scores = {
        SYSTEM_CRISIS:    sum(1 for s in CRISIS_SIG    if s in combined) * 4,
        SYSTEM_FORENSIC:  sum(1 for s in FORENSIC_SIG  if s in combined) * 2,
        SYSTEM_TECHNICAL: sum(1 for s in TECHNICAL_SIG if s in combined) * 2,
        SYSTEM_BRAND:     sum(1 for s in BRAND_SIG     if s in combined) * 2,
        SYSTEM_DIALECTIC: sum(1 for s in DIALECTIC_SIG if s in combined) * 3,
        SYSTEM_REFLECT:   sum(1 for s in TRAUMA_SIG    if s in combined) * 2,
    }
    return max(scores, key=scores.get) if max(scores.values()) > 0 else SYSTEM_REFLECT

def is_skip(text):
    if len(text.strip()) < 15:
        return True
    for pat in SKIP_PATTERNS:
        if re.match(pat, text.strip()):
            return True
    return False

def extract_all_turns(pdf_path):
    """Extract ALL text from PDF, parse into complete turn list."""
    full_text = ''
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += '\n' + t
    except Exception as e:
        return [], str(e)

    full_text = clean_text(full_text)
    parts = TURN_RE.split(full_text)

    turns = []
    for i in range(1, len(parts) - 1, 2):
        marker  = parts[i].lower().strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ''
        content = clean_text(content)
        if is_skip(content):
            continue
        is_user = any(m in marker for m in ['you said', 'human', 'shane', 'user'])
        turns.append({
            'role': 'user' if is_user else 'assistant',
            'content': content,
        })
    return turns, None

def build_multiturn_windows(turns, window=4, stride=2):
    """
    Build multi-turn conversation windows.
    Each window = N turns ending with an assistant turn.
    This teaches the model to use thread context, not just respond to isolated prompts.
    """
    windows = []
    for i in range(0, len(turns) - 1, stride):
        # Find the next assistant turn to end on
        end = i + window
        if end >= len(turns):
            end = len(turns) - 1
        # Walk back to find an assistant turn to end on
        while end > i and turns[end]['role'] != 'assistant':
            end -= 1
        if end <= i:
            continue
        window_turns = turns[i:end + 1]
        # Must start with user, end with assistant, have at least 2 turns
        if window_turns[0]['role'] != 'user':
            continue
        if window_turns[-1]['role'] != 'assistant':
            continue
        if len(window_turns) < 2:
            continue
        windows.append(window_turns)
    return windows

def format_multiturn_sft(turns, system):
    """Format a multi-turn window as a LLaMA 3 chat training example."""
    text = f'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>'
    for turn in turns:
        role = 'user' if turn['role'] == 'user' else 'assistant'
        content = turn['content'][:3000]
        text += f'<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>'
    return {'text': text}

def build_dpo_from_turns(turns):
    """
    Find pushback sequences in the turn list and build DPO pairs.
    Pattern: user→AI(bad)→user(pushback)→AI(better)
    """
    dpo_pairs = []
    for i in range(len(turns) - 3):
        t0 = turns[i]     # user prompt
        t1 = turns[i + 1] # ai response (potentially bad)
        t2 = turns[i + 2] # user pushback
        t3 = turns[i + 3] # ai better response

        if not (t0['role']=='user' and t1['role']=='assistant' and
                t2['role']=='user' and t3['role']=='assistant'):
            continue

        low2 = t2['content'].lower()
        is_push = any(p in low2 for p in PUSHBACK)
        low1 = t1['content'].lower()
        is_hedge = sum(1 for p in HEDGE_PHRASES if p in low1) >= 2
        is_bobble = sum(1 for p in BOBBLEHEAD if p in low1) >= 1

        if is_push or (is_hedge or is_bobble):
            dpo_pairs.append({
                'prompt': t0['content'][:2000],
                'rejected': t1['content'][:3000],
                'chosen': t3['content'][:3000],
                'pushback': t2['content'][:500],
                'source': 'multiturn_pushback',
            })
    return dpo_pairs

# ── Per-file routing table ────────────────────────────────────────────────────
# Files where we know the register — override auto-routing for these
KNOWN_REGISTER = {
    'TONE HANDLING': SYSTEM_BRAND,
    'Legal Filings': SYSTEM_FORENSIC,
    'Florida Scam': SYSTEM_FORENSIC,
    'Micha Gray': SYSTEM_FORENSIC,
    'Premeditated Attempted Murder': SYSTEM_FORENSIC,
    'Roommate era': SYSTEM_FORENSIC,
    '200k A Year GPT': SYSTEM_BRAND,
    'Cracking LinkedIn': SYSTEM_BRAND,
    'Prompts Removed': SYSTEM_BRAND,
    'Disagree GPT': SYSTEM_BRAND,
    'Botnet Load': SYSTEM_TECHNICAL,
    'DEVICE ISOLATION': SYSTEM_TECHNICAL,
    'This is how metadata': SYSTEM_TECHNICAL,
    'classifier': SYSTEM_TECHNICAL,
    'Classifier': SYSTEM_TECHNICAL,
    'CLASSIFIER': SYSTEM_TECHNICAL,
    'trust score': SYSTEM_TECHNICAL,
    'Trust Score': SYSTEM_TECHNICAL,
    'deferred identity': SYSTEM_TECHNICAL,
    'edge behavior injection': SYSTEM_TECHNICAL,
    'thinking like the classifier': SYSTEM_TECHNICAL,
    'multi-vector': SYSTEM_TECHNICAL,
    'MULTI-NODE': SYSTEM_TECHNICAL,
    'Neurosemantic': SYSTEM_TECHNICAL,
    'Counter Surveil': SYSTEM_TECHNICAL,
    'Delay Account': SYSTEM_TECHNICAL,
    'NLP and Narrative': SYSTEM_REFLECT,
    'Therapy Abuse': SYSTEM_REFLECT,
    'Observer Effect': SYSTEM_REFLECT,
    'Dear Diary': SYSTEM_REFLECT,
    'STALKED AS FUCK': SYSTEM_REFLECT,
    'target of systemic': SYSTEM_REFLECT,
    'epistemic betrayal': SYSTEM_REFLECT,
    'Why Everyone Slaps': SYSTEM_REFLECT,
    'full_stack_identity': SYSTEM_FORENSIC,
}

def get_base_system(fname):
    for key, sys in KNOWN_REGISTER.items():
        if key.lower() in fname.lower():
            return sys
    return None  # will auto-route per-window

# ── RAG note extractor ────────────────────────────────────────────────────────
RAG_FILES = [
    ('CLASSIFIER ROOT LOGIC.pdf', AI_DIR, 'classifier_root.md'),
    ('Classifier_Override_Perfect_Sanity_Declaration.pdf', AI_DIR, 'classifier_override.md'),
    ('Karl Deisseroth Sematic Fusion EEAT Social Graph Protected entity Status- NEUROSCIENCE.pdf', AI_DIR, 'deisseroth_eeat.md'),
    ("Building on Deisseroth et al.'s recursive activation feedback loops in ventral tegmental and prefrontal connectivity models.pdf", AI_DIR, 'deisseroth_activation.md'),
    ("Building on Deisseroth et al.'s recursive activation feedback loops in ventral tegmental and prefrontal connectivity models-2.pdf", AI_DIR, 'deisseroth_activation2.md'),
    ('Mass Reporting as an Ontological Weapon_ Null State Suppression, Epistemic Freezing, and AI Trust Score Sabotage in Moderation Systems.pdf', AI_DIR, 'mass_reporting.md'),
    ('1-42 - Shane Graffiti Inc. AI Semantic Research Division_ Case Study_ Fracture at the Interface_ Alignment Scaling Constraints in Recursive Semantic Coupling Between High-Context Users and Autoregressive Language Models.pdf', AI_DIR, 'fracture_interface.md'),
    ('Shane Graffiti Inc. -Adversarial Research Division_ Case Study_ Social Media EEAT Reputation _ Trust Score Manipulation _ Platform Metric Weaponization -  Mass Reporting as an Ontological Weapon_ Null State Suppression, Epistemic Freezing, and AI ….pdf', AI_DIR, 'adversarial_case_study.md'),
    ('Smart Glasses - Case Study - Extended-  Shane Graffit Inc. Portfolio Page.pdf', AI_DIR, 'smart_glasses.md'),
    ('Smart Glasses - Case Study - Extended-  Shane Graffit Inc. Portfolio Page-2.pdf', AI_DIR, 'smart_glasses2.md'),
    ('Systemic_Trauma_Taxonomy_Florida_Scam_Expanded.pdf', AI_DIR, 'trauma_taxonomy.md'),
    ('claim Cause 1.pdf', AI_DIR, 'claim_cause1.md'),
    ('AI Research Paper LLM.pdf', AI_DIR, 'ai_research_paper.md'),
    ('multi-vector class realignment under contradiction risk - propagation anomaly flag—where a previously suppressed node\'s content reaches propagation depth inconsistent with its trust score—and ends with a node inheritance vector reassignment.pdf', AI_DIR, 'multi_vector_realignment.md'),
    (' Multi-Axial Refractive Trust Embedding - Nonlinear Motif Recursion Induction - Affective Echo Desynchronization Layering - Vector Collusion Nullification via Semantic Jittering - Post-Engagement Temporal Osmosis Buffering -  Classifier Internal R….pdf', AI_DIR, 'multi_axial_trust.md'),
    ('EMOTIONAL ECONOMY.pdf', AI_DIR2, 'emotional_economy.md'),
    ('AI Project Summary.pdf', AI_DIR2, 'ai_project_summary.md'),
    (' Transcript- Shane Graffiti Inc. Smart Glasses Teaser Demo.pdf', AI_DIR2, 'smart_glasses_transcript.md'),
    ('rlhf rag retrieval mixure of expert think tanks ive created.pdf', AI_DIR2, 'rlhf_moe_research.md'),
    ('Latent Space Softmax function Poetry Tokenization Embedding Position Encvoding Probabilty Distributions Temprature and Entroy-2.pdf', AI_DIR2, 'latent_space.md'),
    ('SDR Proof Cell Data Routers - High Security Routers With 1206s Jammer Detector Automations- SIGINT Proof MAC IP DHCP Rotations .pdf', AI_DIR2, 'sdr_routers.md'),
    ('Cohere\'s Vision - Value Added Video Script.pdf', AI_DIR2, 'cohere_vision.md'),
    ('Systemic_Trauma_Taxonomy_Florida_Scam_Unicode.pdf', AI_DIR, 'trauma_taxonomy_unicode.md'),
    ('Premeditated Attempted Murder Staged Like Freak Accident.pdf', AI_DIR, 'attempted_murder_notes.md'),
    ('Micha Gray Attempted Murder - Unscrews 400 Degree Top Plate Causing 2k F Arc Sparks Ionized Live Wire.pdf', AI_DIR, 'micha_gray_notes.md'),
    ('Roommate era photo evidence.pdf', AI_DIR, 'roommate_evidence.md'),
]

# ── CSV merger ────────────────────────────────────────────────────────────────
def merge_csvs():
    rows = []
    for d in [AI_DIR]:
        for fname in sorted(os.listdir(d)):
            if not fname.endswith('.csv'): continue
            try:
                with open(os.path.join(d, fname), encoding='utf-8', errors='ignore') as f:
                    for row in csv.DictReader(f):
                        rows.append(dict(row))
            except: pass
    dest = os.path.join(NOTES_G, 'classifier_taxonomy.md')
    seen = set()
    with open(dest, 'w') as f:
        f.write('# Classifier Taxonomy and Trust Score Gradients\n\nShane Graffiti Inc. — AI Semantic Research Division\n\n')
        for row in rows:
            line = str(row)
            if line not in seen:
                seen.add(line)
                f.write(line + '\n')
    return len(rows), len(seen)

# ── DIALOGUE FILES — all of them ──────────────────────────────────────────────
DIALOGUE_FILES = []
for d in [AI_DIR, AI_DIR2]:
    for fname in os.listdir(d):
        if not fname.endswith('.pdf'): continue
        # Skip pure research/resume/empty docs
        skip_keywords = ['resume','Resume','EMOTIONAL ECONOMY','AI Project Summary',
                         'Transcript','Cohere','Sora Images','Untitled','SMOKING GUN',
                         'Checking_XXX','stalking evidence','IMG_','_1.png','_2.png',
                         'claim Cause','Systemic_Trauma_Taxonomy','LLM_Taxonomy',
                         'Extended_Trust','_Motion to Release','AI Research Paper LLM',
                         'Building on Deisseroth','Karl Deisseroth','Mass Reporting',
                         'Shane Graffiti Inc. -Adversarial','Shane Graffiti Inc. AI Semantic',
                         'Smart Glasses - Case Study','1-42 - Shane','multi-vector class',
                         ' Multi-Axial Refractive','rlhf rag','Latent Space','SDR Proof',
                         'Do You Want Fries','insulting ass','Classifier_Override_Perfect',
                         'CLASSIFIER ROOT LOGIC','Disagree GPT',
                         ]
        if any(k in fname for k in skip_keywords): continue
        DIALOGUE_FILES.append((os.path.join(d, fname), fname))

# ── MAIN ─────────────────────────────────────────────────────────────────────
print('\n=== Reflect Full Dataset Builder ===\n')
print(f'Dialogue files to process: {len(DIALOGUE_FILES)}')

all_sft = []
all_dpo = []
seen_hashes = []  # for dedup

total_turns_parsed = 0
total_windows = 0
total_dpo = 0
skipped_quality = 0
skipped_dedup = 0

with open(OUT_SFT, 'w') as sft_f, open(OUT_DPO, 'w') as dpo_f:

    for pdf_path, fname in sorted(DIALOGUE_FILES, key=lambda x: -os.path.getsize(x[0])):
        print(f'\n[{fname[:65]}]')

        turns, err = extract_all_turns(pdf_path)
        if err:
            print(f'  ERR: {err}')
            continue
        if len(turns) < 4:
            print(f'  SKIP: only {len(turns)} turns')
            continue

        total_turns_parsed += len(turns)
        print(f'  Turns parsed: {len(turns)}')

        # Build DPO pairs first (need the full turn list)
        dpo_pairs = build_dpo_from_turns(turns)
        for pair in dpo_pairs:
            if len(pair['chosen'].strip()) < 100: continue
            dpo_f.write(json.dumps(pair, ensure_ascii=False) + '\n')
        total_dpo += len(dpo_pairs)
        if dpo_pairs:
            print(f'  DPO pairs: {len(dpo_pairs)}')

        # Build multi-turn windows
        base_system = get_base_system(fname)
        windows = build_multiturn_windows(turns, window=5, stride=2)
        file_sft = 0
        file_skip_q = 0
        file_skip_d = 0

        for window_turns in windows:
            # Get the final AI response for quality scoring
            last_ai = window_turns[-1]['content']

            # Quality gate: skip hedgy/bobblehead responses
            hedges = sum(1 for p in HEDGE_PHRASES if p in last_ai.lower())
            bobble = sum(1 for p in BOBBLEHEAD if p in last_ai.lower())
            if hedges >= 4 or bobble >= 3:
                skipped_quality += 1
                file_skip_q += 1
                continue

            # Quality floor: skip very short responses
            if len(last_ai.strip()) < 100:
                skipped_quality += 1
                file_skip_q += 1
                continue

            # Near-dedup check on final response
            h = simhash(last_ai)
            is_dup = any(hash_distance(h, existing) < 8 for existing in seen_hashes[-500:])
            if is_dup:
                skipped_dedup += 1
                file_skip_d += 1
                continue
            seen_hashes.append(h)

            # Pick system prompt
            context = ' '.join(t['content'] for t in window_turns)
            system = base_system if base_system else route_system(context, last_ai)

            # Format and write
            record = format_multiturn_sft(window_turns, system)
            if record:
                sft_f.write(json.dumps(record, ensure_ascii=False) + '\n')
                file_sft += 1
                total_windows += 1

        print(f'  SFT windows: {file_sft} | skipped quality: {file_skip_q} | skipped dedup: {file_skip_d}')

    # RAG notes
    print('\n=== Building RAG Notes ===')
    for fname, directory, outfile in RAG_FILES:
        path = os.path.join(directory, fname)
        if not os.path.exists(path):
            print(f'  MISSING: {fname[:60]}')
            continue
        text = ''
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages[:20]:
                    t = page.extract_text()
                    if t: text += t + '\n\n'
            dest = os.path.join(NOTES_G, outfile)
            with open(dest, 'w') as f:
                f.write(f'# {fname[:80]}\n\n{clean_text(text)[:80000]}')
            print(f'  -> {outfile}')
        except Exception as e:
            print(f'  ERR {outfile}: {e}')

    # CSVs
    print('\n=== Merging CSVs ===')
    total_rows, unique_rows = merge_csvs()
    print(f'  {total_rows:,} rows, {unique_rows:,} unique -> classifier_taxonomy.md')

print(f'\n{"="*60}')
print(f'Total turns parsed:     {total_turns_parsed:,}')
print(f'Multi-turn SFT windows: {total_windows:,}')
print(f'DPO pairs:              {total_dpo:,}')
print(f'Skipped (quality):      {skipped_quality:,}')
print(f'Skipped (near-dedup):   {skipped_dedup:,}')
print(f'\nOutputs:')
print(f'  {OUT_SFT}')
print(f'  {OUT_DPO}')
print(f'  {NOTES_G}/')

# ── AUTO-RUN CLEANER ──────────────────────────────────────────────────────────
print('\n\nAuto-running clean_dataset.py...')
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-W', 'ignore', os.path.join(BASE, 'clean_dataset.py')],
    capture_output=False
)
