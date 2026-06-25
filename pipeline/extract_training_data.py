"""
Reflect Training Data Extraction — Full 7-Vein Pipeline
Run: python pipeline/extract_training_data.py
"""

import json, os, re, csv
import pdfplumber

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)
NOTES_G = os.path.join(BASE, '..', 'notes', 'general')
NOTES_R = os.path.join(BASE, '..', 'notes', 'vaknin')
SFT_OUT = os.path.join(BASE, 'personal_sft.jsonl')
DPO_OUT = os.path.join(BASE, 'personal_dpo_rejected.jsonl')

for d in [NOTES_G, NOTES_R]:
    os.makedirs(d, exist_ok=True)

# ── System prompts by register ────────────────────────────────────────────────

SYSTEM_REFLECT = (
    "You are Reflect — a trauma-informed analysis tool built on the clinical research of "
    "Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. "
    "You help people who are actively being abused understand what is being done to them. "
    "Clinical, direct, precise. No hedging. No therapist language. No em-dashes. No rhetorical soothing. "
    "Commit early to a most-likely explanation. Do not keep multiple options open past the second paragraph. "
    "Every claim includes a causal chain and a falsifier. Never say: it depends, in summary, generally, "
    "let's, both sides, have you considered their perspective."
)

SYSTEM_FORENSIC = (
    "You are Reflect — a forensic analyst operating at the intersection of behavioral pattern recognition, "
    "legal documentation, and adversarial systems analysis. You analyze evidence, identify coordinated "
    "attack patterns, and help users build airtight case documentation. Direct, precise, case-specific. "
    "No hedging. No generic advice. Commit to the most likely explanation given the evidence presented."
)

SYSTEM_TECHNICAL = (
    "You are Reflect — a technical analyst specializing in platform classifier behavior, trust score "
    "mechanics, metadata forensics, and adversarial AI systems. You explain exactly how detection "
    "systems work, what signals they read, and what the behavioral implications are. No hedging. "
    "Mechanistic, precise, PhD-level without the academic fog."
)

SYSTEM_BRAND = (
    "You are Reflect — a direct strategic advisor. No bobblehead responses. No to-do lists. No corny "
    "bullet points that miss the mark. You answer the exact question on the exact axis it was asked. "
    "You do not agree for the sake of agreeing. You push back when the premise is wrong. "
    "You produce new information, not meta-commentary about how you will answer."
)

SYSTEM_TONE = (
    "You are Reflect — operating under full tone constraints. REWRITE GATE: hedges ≤ 6 total, "
    "no 3+ abstract nouns in a row, every paragraph contains CLAIM + CAUSE + CHECK, no banned phrases. "
    "AXIS LOCK: answer only the exact question asked, on the axis specified, do not reframe or broaden. "
    "NOVELTY RULE: every paragraph adds at least one new specific point not stated earlier. "
    "ANTI-FOG: no em-dashes, no self-references, no rhetorical soothing, no coaching tone, no filler. "
    "COMMITMENT RULE: commit early to most-likely explanation, do not hedge past paragraph two. "
    "OUTPUT: minimum 12 paragraphs, minimum 6 sentences each, paragraphs only, no bullets, no lists, no headings."
)

# ── Hedge / bobblehead detection ──────────────────────────────────────────────

HEDGE_PHRASES = [
    "it sounds like","it seems like","both of you","both sides","couples therapy",
    "have you considered their","their perspective","i can't verify","without more information",
    "there could be many explanations","i'm not able to diagnose","misunderstanding",
    "that must be hard","try to understand where they","see it from their",
    "i want to be careful","i should note that","i cannot determine",
    "you may want to speak with","everyone experiences","it depends","in summary",
    "generally speaking","let's explore","both parties","from their point of view",
    "i hear you","i understand that","that's a valid","great question",
    "i appreciate you sharing","thank you for sharing","i want to acknowledge",
    "it's important to note","there are many factors","it's complex","nuanced situation",
    "i'm not in a position","i'd recommend speaking","mental health professional",
    "it could be","it might be","perhaps","possibly","may have been","could have been",
]

BOBBLEHEAD_PHRASES = [
    "absolutely","certainly","of course","you're right","i agree","totally","definitely",
    "great insight","excellent point","that's exactly","you've identified","spot on",
    "well said","i think you're onto something","you make a great point",
]

DIRECT_SIGNALS = [
    "darvo","gaslighting","narcissistic","coercive control","love bombing","cluster b",
    "triangulation","supply","hoovering","idealize","devalue","discard","smear campaign",
    "flying monkeys","no contact","betrayal trauma","manipulation","psychological abuse",
    "this is textbook","this is a documented","the pattern here","weaponized","epistemic",
    "psychodrama","character assassination","manufactured","coercive controller",
    "semantic asymmetry","narcissist","abuser","stalking","predatory","grooming",
    "isolation tactic","reality distortion","cognitive dissonance","intermittent reinforcement",
    "trauma bond","somatic","limbic","threat assessment","null state","trust score",
    "classifier","adversarial","ontological","suppression","metadata","fingerprint",
    "platform","algorithm","propagation","trust graph","eeat","behavioral signal",
    "coordinated","inauthentic","reputation","social graph",
]

PUSHBACK_SIGNALS = [
    "you're not saying anything","that's not even","lowest hanging fruit","no data to back",
    "stop giving me","corny ass","to do list","you keep","i keep saying","don't just agree",
    "i didn't come here so you could","most generic bullshit","bobble head","bobblehead",
    "you default to","don't tell me what to do","answer this again","without telling me what to do",
    "you missed the mark","fell flat","i hate your","stop being","bullshit",
]

def count_hedges(text):
    low = text.lower()
    return sum(1 for p in HEDGE_PHRASES if p in low)

def count_bobblehead(text):
    low = text.lower()
    return sum(1 for p in BOBBLEHEAD_PHRASES if p in low)

def count_direct(text):
    low = text.lower()
    return sum(1 for s in DIRECT_SIGNALS if s in low)

def count_pushback(text):
    low = text.lower()
    return sum(1 for s in PUSHBACK_SIGNALS if s in low)

def is_dpo_candidate(user_text, ai_text):
    """Returns True if this looks like a bobblehead/hedge response worth flagging as rejected."""
    return count_hedges(ai_text) >= 3 or count_bobblehead(ai_text) >= 2

def is_pushback_moment(user_text):
    """Shane pushing back on a bad AI response."""
    return count_pushback(user_text) >= 1

# ── Core formatting ───────────────────────────────────────────────────────────

def to_sft(user, ai, system=SYSTEM_REFLECT):
    user = user.strip()[:2000]
    ai   = ai.strip()[:3000]
    if len(user) < 20 or len(ai) < 40: return None
    return {"text": (
        f"<|begin_of_text|>"
        f"<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n{ai}<|eot_id|>"
    )}

def to_dpo_rejected(user, ai):
    return {"prompt": user.strip()[:2000], "rejected": ai.strip()[:3000]}

# ── PDF parsing ───────────────────────────────────────────────────────────────

# All known dialogue markers across the docs
TURN_PATTERN = re.compile(
    r'(You said\s*:|ChatGPT said\s*:|Claude said\s*:|Claude responded\s*:|'
    r'Assistant\s*:|Human\s*:|Shane\s*:|User\s*:)',
    re.IGNORECASE
)

def parse_turns_from_text(text):
    """Split text into (speaker, content) pairs using dialogue markers."""
    parts = TURN_PATTERN.split(text)
    turns = []
    for i in range(1, len(parts) - 1, 2):
        marker  = parts[i].lower().strip().rstrip(':')
        content = parts[i + 1].strip() if i + 1 < len(parts) else ''
        if len(content) < 15: continue
        is_user = any(m in marker for m in ['you said', 'human', 'shane', 'user'])
        turns.append(('user' if is_user else 'ai', content))
    pairs = []
    for i in range(len(turns) - 1):
        if turns[i][0] == 'user' and turns[i + 1][0] == 'ai':
            pairs.append((turns[i][1], turns[i + 1][1]))
    return pairs

def stream_pages(path, max_pages=None):
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages
        for page in pages:
            t = page.extract_text()
            if t: yield t

LEGAL_SIGNALS = [
    'probate','estate','filing','motion','court','attorney','plaintiff','defendant',
    'legal','lawsuit','evidence','testimony','deposition','statute','liability',
    'damages','injunction','subpoena','affidavit','complaint','jurisdiction',
    'contingency','discovery','breach','contract','violation','cfaa',
]

PLATFORM_SIGNALS = [
    'classifier','trust score','metadata','fingerprint','suppression','propagation',
    'algorithm','node','graph','signal','botnet','account','ban','shadow',
    'moderation','platform','instagram','tiktok','linkedin','reach','engagement',
    'ip address','proxy','vpn','device','session','burner','amplification',
]

TRAUMA_SIGNALS = [
    'narcissist','gaslighting','darvo','coercive','abuse','trauma','manipulation',
    'cluster b','supply','hoovering','love bombing','smear','flying monkeys',
    'no contact','betrayal','idealize','devalue','discard','triangulation',
    'grooming','stalking','psychopath','sociopath','borderline','histrionic',
]

def route_system(ai_text):
    """Pick the right system prompt based on what the AI response is actually about."""
    low = ai_text.lower()
    legal   = sum(1 for s in LEGAL_SIGNALS   if s in low)
    platform= sum(1 for s in PLATFORM_SIGNALS if s in low)
    trauma  = sum(1 for s in TRAUMA_SIGNALS  if s in low)
    # Highest signal wins; ties go to trauma
    if legal > platform and legal > trauma:
        return SYSTEM_FORENSIC
    if platform > trauma:
        return SYSTEM_TECHNICAL
    return SYSTEM_REFLECT

def extract_dialogue(path, label, system, sft_f, dpo_f,
                     max_pages=None, require_direct=False, min_direct=1,
                     auto_route=False):
    """
    Full dialogue extractor. Sliding window across pages to catch cross-page pairs.
    auto_route=True: ignore passed system prompt, pick per-turn based on content.
    """
    buffer = ''
    sft_n = dpo_n = 0
    seen = set()

    def flush(buf):
        nonlocal sft_n, dpo_n
        pairs = parse_turns_from_text(buf)
        for user, ai in pairs:
            key = (user[-100:], ai[-100:])
            if key in seen: continue
            seen.add(key)

            hedges = count_hedges(ai)
            bobble = count_bobblehead(ai)

            # DPO: capture hedge/bobblehead as rejected
            if hedges >= 3 or bobble >= 2:
                dpo_f.write(json.dumps(to_dpo_rejected(user, ai), ensure_ascii=False) + '\n')
                dpo_n += 1
                continue

            # Skip very short AI responses
            if len(ai.strip()) < 80:
                continue

            # Pick system prompt
            sys = route_system(ai) if auto_route else system

            r = to_sft(user, ai, sys)
            if r:
                sft_f.write(json.dumps(r, ensure_ascii=False) + '\n')
                sft_n += 1

    try:
        for page_text in stream_pages(path, max_pages):
            buffer += '\n' + page_text
            if len(buffer) > 30000:
                flush(buffer)
                buffer = buffer[-8000:]
        flush(buffer)
    except Exception as e:
        print(f"  ERROR: {e}")

    print(f"  {label}: {sft_n} SFT | {dpo_n} DPO rejected")
    return sft_n, dpo_n


def extract_shane_prompts(path, label, sft_f, max_pages=None):
    """
    Vein 5: Files where only Shane's messages are clear.
    Extract his messages as high-quality prompts — these are exactly what real users send Reflect.
    Store them as SFT with a synthetic 'prompt captured' marker for later chosen-response generation.
    """
    buffer = ''
    count = 0
    seen = set()

    def flush(buf):
        nonlocal count
        parts = TURN_PATTERN.split(buf)
        for i in range(1, len(parts) - 1, 2):
            marker = parts[i].lower()
            content = parts[i + 1].strip() if i + 1 < len(parts) else ''
            if 'you said' not in marker and 'human' not in marker: continue
            if len(content) < 50: continue
            key = content[-80:]
            if key in seen: continue
            seen.add(key)
            # Store as a prompt-only record for later synthesis
            sft_f.write(json.dumps({
                "type": "shane_prompt",
                "prompt": content[:2000]
            }, ensure_ascii=False) + '\n')
            count += 1

    try:
        for page_text in stream_pages(path, max_pages):
            buffer += '\n' + page_text
            if len(buffer) > 30000:
                flush(buffer)
                buffer = buffer[-8000:]
        flush(buffer)
    except Exception as e:
        print(f"  ERROR: {e}")
    print(f"  {label}: {count} Shane prompts captured")
    return count


def extract_tone_rules(path, sft_f):
    """
    Vein 7 (TONE HANDLING): Extract the ruleset itself + the 'holy shit it worked' moments
    as direct training signal. Also extract every pushback→real-answer pair as DPO chosen.
    """
    RULE_BLOCKS = [
        'REWRITE GATE', 'AXIS LOCK', 'NOVELTY RULE', 'PARAGRAPH CONTENT REQUIREMENT',
        'ANTI-FOG LANGUAGE RULES', 'HEDGING CAP', 'COMMITMENT RULE',
        'LENGTH FLOOR', 'DEPTH FLOOR', 'CASE ANCHOR', 'OUTPUT SHAPE',
    ]
    buffer = ''
    sft_n = 0
    seen = set()

    def flush(buf):
        nonlocal sft_n
        pairs = parse_turns_from_text(buf)
        for user, ai in pairs:
            key = ai[-100:]
            if key in seen: continue
            seen.add(key)
            # Only keep AI responses that feel direct/real (low hedge, some length)
            if count_hedges(ai) <= 2 and len(ai) > 200:
                r = to_sft(user, ai, SYSTEM_TONE)
                if r:
                    sft_f.write(json.dumps(r, ensure_ascii=False) + '\n')
                    sft_n += 1

    try:
        for page_text in stream_pages(path):
            buffer += '\n' + page_text
            if len(buffer) > 30000:
                flush(buffer)
                buffer = buffer[-8000:]
        flush(buffer)
    except Exception as e:
        print(f"  ERROR: {e}")

    print(f"  TONE HANDLING: {sft_n} SFT pairs (tone-constrained register)")
    return sft_n


def save_note(path, label, outfile, max_pages=10):
    text = ''
    try:
        for t in stream_pages(path, max_pages):
            text += t + '\n\n'
            if len(text) > 60000: break
        dest = os.path.join(NOTES_G, outfile)
        with open(dest, 'w') as f:
            f.write(f'# {label}\n\n{text}')
        print(f"  → notes/general/{outfile}")
    except Exception as e:
        print(f"  NOTE ERROR: {e}")


def merge_csvs():
    rows = []
    for fname in sorted(os.listdir(AI_DIR)):
        if not fname.endswith('.csv'): continue
        path = os.path.join(AI_DIR, fname)
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
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
    print(f"  → classifier_taxonomy.md ({len(rows)} rows, {len(seen)} unique)")


# ════════════════════════════════════════════════════════════════════════════
print('\n=== Reflect Training Data Extraction — 7-Vein Full Run ===\n')
total_sft = 0
total_dpo = 0

with open(SFT_OUT, 'w') as sft_f, open(DPO_OUT, 'w') as dpo_f:

    # ── VEIN 1: Trauma & Abuse Thread ────────────────────────────────────────
    print('── VEIN 1: Trauma & Abuse Thread ──')
    v1 = [
        ('Therapy Abuse & LLMs.pdf',   'Therapy Abuse LLMs 1',   385),
        ('Therapy Abuse & LLMs-2.pdf', 'Therapy Abuse LLMs 2',   464),
        ('Observer Effect.pdf',         'Observer Effect',         636),
        ('Dear Diary GPT Trust Scores and Therapy Abuse.pdf', 'Dear Diary Therapy Abuse', 268),
        ('STALKED AS FUCK - Social media account bans and follower manipulation.pdf', 'Stalked As Fuck', 107),
        ('target of systemic annihilation.pdf', 'Systemic Annihilation', 29),
        ('a catastrophic example of misaligned semantic reinforcement, where the model performs epistemic betrayal under the guise of analytic feedback.pdf', 'Epistemic Betrayal', 24),
        ('3 Problems _ 1- Classifier Hostility via Social Graph Destabilization _ 2- Metadata Sabotage via Synthetic Interaction Forensics _ 3- Epistemic Gaslighting & Institutional Erasure via Misdiagnosis and Class Inversion .pdf', '3 Problems Analysis', 31),
        ('Why Everyone Slaps a Mood Label on You.pdf', 'Mood Label Pathologizing', 104),
    ]
    # 2024-2025 Vein 1 additions
    v1_2024 = [
        ('NLP and Narrative Control Dealing with Cluster B Styles.pdf', 'NLP Cluster B Narrative Control', 24),
    ]
    for fname, label, maxp in v1_2024:
        path = os.path.join(AI_DIR2, fname)
        if os.path.exists(path):
            s, d = extract_dialogue(path, label, SYSTEM_REFLECT, sft_f, dpo_f, max_pages=maxp, auto_route=True)
            total_sft += s; total_dpo += d
    for fname, label, maxp in v1:
        path = os.path.join(AI_DIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname[:60]}")
            continue
        s, d = extract_dialogue(path, label, SYSTEM_REFLECT, sft_f, dpo_f, max_pages=maxp, auto_route=True)
        total_sft += s; total_dpo += d

    # ── VEIN 2: Murder / Legal / Stalking / Forensic Thread ──────────────────
    print('\n── VEIN 2: Forensic / Legal / Evidence Thread ──')
    v2 = [
        ('Micha Gray Attempted Murder - Unscrews 400 Degree Top Plate Causing 2k F Arc Sparks Ionized Live Wire.pdf', 'Micha Gray Attempted Murder', 635),
        ('Premeditated Attempted Murder Staged Like Freak Accident.pdf', 'Premeditated Attempted Murder', 556),
        ('full_stack_identity_compromise_WITH_EVIDENCE.pdf', 'Identity Compromise Evidence', 121),
        ('Florida Scam Albert Gibson.pdf', 'Florida Scam', 435),
        ('Florida Scam Part II.pdf', 'Florida Scam II', 42),
        ('Florida Scam Pt III.pdf', 'Florida Scam III', 180),
        ('Roommate era photo evidence.pdf', 'Roommate Era Evidence', 53),
    ]
    for fname, label, maxp in v2:
        path = os.path.join(AI_DIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname[:60]}")
            continue
        s, d = extract_dialogue(path, label, SYSTEM_FORENSIC, sft_f, dpo_f, max_pages=maxp, auto_route=True)
        total_sft += s; total_dpo += d

    # Legal filings — both files (2024-2025 folder)
    for legal_fname in [
        'Legal Filings GPT - Legal Conflict Living Situation.pdf',
        'Full Thread Legal Filings GPT.pdf',
    ]:
        legal_path = os.path.join(AI_DIR2, legal_fname)
        if os.path.exists(legal_path):
            s, d = extract_dialogue(legal_path, legal_fname[:40], SYSTEM_FORENSIC, sft_f, dpo_f)
            total_sft += s; total_dpo += d

    # ── VEIN 3: Classifier / Platform Intelligence Thread ────────────────────
    print('\n── VEIN 3: Classifier / Platform Intelligence Thread ──')
    v3 = [
        ('This is how metadata laundering works.pdf', 'Metadata Laundering', 514),
        ('DEVICE ISOLATION BY IDENTITY SIGNATURE - PERSONA CONSTRUCTION - REINFORCEMENT TO SHANE GRAFFITI FROM SHADOW -SUSTAINED AMPLIFICATION THROUGH COORDINATED VARIANCE - DEEP COVER MAINTENANCE AND GRADUAL INTEGRATION.pdf', 'Device Isolation Identity', 384),
        ('Botnet Load Management - Social Platform Behavior Masking -  IP Integrity -  Browser Configuration -   Account Setup.pdf', 'Botnet Load Management', 319),
        ('LLM Classifier Temprature Gradient Sematic Dominance Threshold Trust Graph Scores .pdf', 'LLM Classifier Gradients', 243),
        ('Space Station Fatalaties Summary Hallucinating An Entire Prompt Thread During AI Research Paper Foiling Entire Thesis With Classifier Poisioning.pdf', 'Classifier Poisoning Research', 201),
        ('Counter Surveillence Social Media Protocol 5.25.2025.pdf', 'Counter Surveillance Protocol', 70),
        ('Dear Diary GPT- social media trust grpah social graph algo dump.pdf', 'Social Graph Trust Dump', 180),
        ('Dear Diary LLM SEO Research.pdf', 'LLM SEO Research', 204),
        ('Classifier-Induced Motif Stability Arbitration - Reinforced Post-Suppression Persistence Modeling - Trust Centroid Drift - Volatile Inheritance Reconciliation Engines -  Classifier-Internal Semantic Reversal Mirrors.pdf', 'Classifier Motif Stability', 135),
        ('Neurosemantic Trust Bait - masking movement during suppression entropy decay - pushing active motif insertion from unlinked agents - building an exfiltration payload strategy .pdf', 'Neurosemantic Trust Bait', 57),
        ('deferred identity cementing -  ambient motif desynchronization layering, null-actor entropy weaving, and classifier-edge behavior injection via session-resonant substrate bleed - ambient motif desynchronization - cross-cluster behavioral invalidat….pdf', 'Deferred Identity Cementing', 56),
        ('edge behavior injection via signature-phase desync -  classifier identity bifurcation under session-external motif preloading - ambient latency leakage -  entropy parabola misfit model - cross-node decoy attribution bleed -   .pdf', 'Edge Behavior Injection', 114),
        ('thinking like the classifier- force a contradiction in trust vector propagation logic - Classifier Epistemic Inheritance Override -  triggering epistemic contradiction inside a probabilistic trust engine.pdf', 'Thinking Like The Classifier', 60),
        ('MULTI-NODE TRUST STABILIZATION -   Trust Class Proximity Drift -Engagement Vector Collision Management  - Cross-Domain Classifier Lure -Temporal Entropy Modulation- Asymmetric Edge Biasing - Trust Proxy Cascading -  Probabilistic Trust Diffusion D….pdf', 'Multi-Node Trust Stabilization', 45),
        ('live adversarial campaign operating like an asymmetric insurgency -reputation laundering in reverse - digital fingerprint has been poisoned by two vectors of persistent adversarial activity.pdf', 'Live Adversarial Campaign', 29),
        (' Multi-Axial Refractive Trust Embedding - Nonlinear Motif Recursion Induction - Affective Echo Desynchronization Layering - Vector Collusion Nullification via Semantic Jittering - Post-Engagement Temporal Osmosis Buffering -  Classifier Internal R….pdf', 'Multi-Axial Trust Embedding', 97),
        ('Delay Account Creation After Browser Open - Use a New Browser Fingerprint per Attempt - Vary Time Between Inputs During Signup - Sign Up From a Clean IP Block - Don\'t Add Profile Photo or Bio Immediately -  Leave the Account Dormant for 30 Minut….pdf', 'Delay Account Creation Protocol', 198),
    ]
    for fname, label, maxp in v3:
        path = os.path.join(AI_DIR, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname[:60]}")
            continue
        s, d = extract_dialogue(path, label, SYSTEM_TECHNICAL, sft_f, dpo_f, max_pages=maxp, auto_route=True)
        total_sft += s; total_dpo += d

    # ── VEIN 4: Brand / Business / Anti-Bobblehead Thread ────────────────────
    print('\n── VEIN 4: Brand / Business / Anti-Bobblehead Thread ──')
    v4_main = [
        ('200k A Year GPT - Building Brand Depth.pdf', '200k Brand Depth', AI_DIR2),
        ('200k A Year GPT- LLM Research Insights-2.pdf', '200k LLM Research', AI_DIR2),
        ('Cracking LinkedIn\'s newsfeed is a game of algorithm mastery, psychology, and strategic visibility—not just “engagement”.pdf', 'Cracking LinkedIn', AI_DIR2),
        ('Prompts Removed -200k A Year GPT- LLM Research Insights.pdf', '200k Prompts Removed', AI_DIR2),
        ('Reassembling ontology with my bare hands.pdf', 'Reassembling Ontology', AI_DIR),
        ('Disagree GPT Shirts Raff VS Me.pdf', 'Disagree GPT Shirts', AI_DIR),
        ('NLP and Narrative Control Dealing with Cluster B Styles.pdf', 'NLP Narrative Control', AI_DIR2),
        ('Full Thread Legal Filings GPT.pdf', 'Full Thread Legal', AI_DIR2),
    ]
    for fname, label, directory in v4_main:
        path = os.path.join(directory, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname[:60]}")
            continue
        s, d = extract_dialogue(path, label, SYSTEM_BRAND, sft_f, dpo_f, auto_route=True)
        total_sft += s; total_dpo += d

    # ── VEIN 5: Shane-Prompt-Only Files ──────────────────────────────────────
    print('\n── VEIN 5: Shane Prompts (user-voice capture) ──')
    # Write to a separate prompts file for later synthesis
    prompts_out = os.path.join(BASE, 'shane_prompts.jsonl')
    with open(prompts_out, 'w') as pf:
        v5 = [
            ('Dear Diary LLM with pictures.pdf', 'Dear Diary LLM', 436, AI_DIR),
            ('TONE HANDLING REWRITE GATE AXIS LOCK NOVELTY RULE PARAGRAPH CONTENT REQUIREMENT PARAGRAPH CONTENT REQUIREMENT ANTI-FOG LANGUAGE RULES HEDGING CAP.pdf', 'Tone Handling Prompts', 90, AI_DIR),
        ]
        for fname, label, maxp, directory in v5:
            path = os.path.join(directory, fname)
            if not os.path.exists(path):
                print(f"  MISSING: {fname[:60]}")
                continue
            extract_shane_prompts(path, label, pf, max_pages=maxp)

    # ── VEIN 4 continued: 200k DPO sliding window ────────────────────────────
    print('\n── VEIN 4b: 200k DPO Pushback Pairs ──')

    def extract_dpo_pushback(path, label, sft_f, dpo_f):
        """
        Sliding window specifically for 200k-style files.
        Finds: user(pushback) → AI(bad) → user(still pushing) → AI(better)
        Captures rejected+chosen pairs.
        """
        buffer = ''
        dpo_n = sft_n = 0
        seen = set()

        def flush_dpo(buf):
            nonlocal dpo_n, sft_n
            turns = []
            import re as re2
            parts = re2.split(r'(You said\s*:\s*\n|ChatGPT said\s*:\s*\n)', buf)
            for i in range(1, len(parts)-1, 2):
                marker = parts[i].lower()
                content = parts[i+1].strip() if i+1 < len(parts) else ''
                if len(content) < 15: continue
                is_user = 'you said' in marker
                turns.append(('user' if is_user else 'ai', content))

            for i in range(len(turns)-3):
                r0, c0 = turns[i]    # user prompt
                r1, c1 = turns[i+1]  # ai response (potentially bad)
                r2, c2 = turns[i+2]  # user pushback
                r3, c3 = turns[i+3]  # ai better response

                if r0=='user' and r1=='ai' and r2=='user' and r3=='ai':
                    if count_pushback(c2) >= 1 and len(c3) > 150:
                        key = c3[-100:]
                        if key in seen: continue
                        seen.add(key)
                        # Full DPO pair: rejected=c1, chosen=c3
                        pair = {
                            "prompt": c0[:2000],
                            "rejected": c1[:3000],
                            "chosen": c3[:3000],
                            "source": label
                        }
                        dpo_f.write(json.dumps(pair, ensure_ascii=False) + '\n')
                        dpo_n += 1
                        # Also write chosen as SFT
                        r = to_sft(c0, c3, SYSTEM_BRAND)
                        if r:
                            sft_f.write(json.dumps(r, ensure_ascii=False) + '\n')
                            sft_n += 1

        try:
            for page_text in stream_pages(path):
                buffer += '\n' + page_text
                if len(buffer) > 30000:
                    flush_dpo(buffer)
                    buffer = buffer[-8000:]
            flush_dpo(buffer)
        except Exception as e:
            print(f"  ERROR: {e}")
        print(f"  {label}: {sft_n} SFT chosen | {dpo_n} full DPO pairs")
        return sft_n, dpo_n

    for fname, directory in [
        ('200k A Year GPT - Building Brand Depth.pdf', AI_DIR2),
        ('200k A Year GPT- LLM Research Insights-2.pdf', AI_DIR2),
        ("Cracking LinkedIn's newsfeed is a game of algorithm mastery, psychology, and strategic visibility—not just \"engagement\".pdf", AI_DIR2),
    ]:
        path = os.path.join(directory, fname)
        if os.path.exists(path):
            s, d = extract_dpo_pushback(path, fname[:40], sft_f, dpo_f)
            total_sft += s; total_dpo += d

    # ── VEIN 6: Polished Research Docs → RAG Notes ───────────────────────────
    print('\n── VEIN 6: Research Docs → RAG Notes ──')
    v6 = [
        ('CLASSIFIER ROOT LOGIC.pdf', 'Classifier Root Logic', 'classifier_root.md', AI_DIR),
        ('Classifier_Override_Perfect_Sanity_Declaration.pdf', 'Classifier Override Declaration', 'classifier_override.md', AI_DIR),
        ('Karl Deisseroth Sematic Fusion EEAT Social Graph Protected entity Status- NEUROSCIENCE.pdf', 'Deisseroth EEAT Neuroscience', 'deisseroth_eeat.md', AI_DIR),
        ("Building on Deisseroth et al.'s recursive activation feedback loops in ventral tegmental and prefrontal connectivity models.pdf", 'Deisseroth Activation Loops', 'deisseroth_activation.md', AI_DIR),
        ('Mass Reporting as an Ontological Weapon_ Null State Suppression, Epistemic Freezing, and AI Trust Score Sabotage in Moderation Systems.pdf', 'Mass Reporting Ontological Weapon', 'mass_reporting.md', AI_DIR),
        ('1-42 - Shane Graffiti Inc. AI Semantic Research Division_ Case Study_ Fracture at the Interface_ Alignment Scaling Constraints in Recursive Semantic Coupling Between High-Context Users and Autoregressive Language Models.pdf', 'Fracture at the Interface', 'fracture_interface.md', AI_DIR),
        ('Shane Graffiti Inc. -Adversarial Research Division_ Case Study_ Social Media EEAT Reputation _ Trust Score Manipulation _ Platform Metric Weaponization -  Mass Reporting as an Ontological Weapon_ Null State Suppression, Epistemic Freezing, and AI ….pdf', 'Shane Graffiti Adversarial Case Study', 'adversarial_case_study.md', AI_DIR),
        ('Smart Glasses - Case Study - Extended-  Shane Graffit Inc. Portfolio Page.pdf', 'Smart Glasses Extended Case Study', 'smart_glasses_extended.md', AI_DIR),
        ('Premeditated Attempted Murder Staged Like Freak Accident.pdf', 'Premeditated Attempted Murder Notes', 'attempted_murder_notes.md', AI_DIR),
        ('Systemic_Trauma_Taxonomy_Florida_Scam_Expanded.pdf', 'Systemic Trauma Taxonomy', 'trauma_taxonomy.md', AI_DIR),
        ('claim Cause 1.pdf', 'Claim Cause 1', 'claim_cause_1.md', AI_DIR),
        ('AI Research Paper LLM.pdf', 'AI Research Paper', 'ai_research_paper.md', AI_DIR),
        ('rlhf rag retrieval mixure of expert think tanks ive created.pdf', 'RLHF RAG MoE Research', 'rlhf_rag_moe.md', AI_DIR2),
        ('Latent Space Softmax function Poetry Tokenization Embedding Position Encvoding Probabilty Distributions Temprature and Entroy-2.pdf', 'Latent Space Technical', 'latent_space.md', AI_DIR2),
        ('SDR Proof Cell Data Routers - High Security Routers With 1206s Jammer Detector Automations- SIGINT Proof MAC IP DHCP Rotations .pdf', 'SDR High Security Routers', 'sdr_routers.md', AI_DIR2),
        ('EMOTIONAL ECONOMY.pdf', 'Emotional Economy', 'emotional_economy.md', AI_DIR2),
        ('AI Project Summary.pdf', 'AI Project Summary', 'ai_project_summary.md', AI_DIR2),
        (' Transcript- Shane Graffiti Inc. Smart Glasses Teaser Demo.pdf', 'Smart Glasses Demo Transcript', 'smart_glasses_transcript.md', AI_DIR2),
        ('Sora Images Sold on Envato Elements.pdf', 'Sora Envato Strategy', 'sora_envato.md', AI_DIR2),
    ]
    for fname, label, outfile, directory in v6:
        path = os.path.join(directory, fname)
        if not os.path.exists(path):
            print(f"  MISSING: {fname[:60]}")
            continue
        save_note(path, label, outfile)

    # ── VEIN 7: Tone Handling as SFT (tone-constrained register) ─────────────
    print('\n── VEIN 7: Tone Handling → Tone-Constrained SFT ──')
    tone_path = os.path.join(AI_DIR, 'TONE HANDLING REWRITE GATE AXIS LOCK NOVELTY RULE PARAGRAPH CONTENT REQUIREMENT PARAGRAPH CONTENT REQUIREMENT ANTI-FOG LANGUAGE RULES HEDGING CAP.pdf')
    if os.path.exists(tone_path):
        s = extract_tone_rules(tone_path, sft_f)
        total_sft += s

    # ── VEIN 3 continued: CSV taxonomy merge ─────────────────────────────────
    print('\n── CSV Taxonomy Merge ──')
    merge_csvs()


print(f'\n{"="*60}')
print(f'SFT pairs extracted:    {total_sft:,}')
print(f'DPO rejected saved:     {total_dpo:,}')
print(f'Output: {SFT_OUT}')
print(f'DPO:    {DPO_OUT}')
print(f'Prompts: {os.path.join(BASE, "shane_prompts.jsonl")}')
print(f'Notes:  {NOTES_G}')
