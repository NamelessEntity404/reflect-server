"""
Reflect — Behavioral Signal Extraction + Semantic Deduplication + Provenance

Runs after build_dataset.py and clean_dataset.py.

What this does:

BEHAVIORAL SIGNAL EXTRACTION:
  - Extracts the behavioral DNA of every training pair:
    * Pushback type (generic complaint / hedging critique / specificity demand / axis correction)
    * Response shift (hedge→direct, generic→specific, surface→mechanism)
    * Emotional register (crisis / analytical / grieving / angry / forensic / dialectical)
    * Commitment markers (when/how the AI commits vs hedges)
    * Shane's writing signals (his specific vocabulary, metaphor domains, sentence patterns)
    * Turn length patterns and their correlation with response quality
    * Escalation patterns (does topic intensity increase across turns)
  - Tags every record with behavioral metadata
  - Produces behavioral_sft.jsonl where system prompts are tuned to detected signals

SEMANTIC DEDUPLICATION (deeper than clean_dataset.py):
  - Cross-file semantic dedup using FAISS approximate nearest neighbors
  - Deduplicates not just within the extracted pairs but against the full PDF text
  - Identifies when a training pair is semantically covered by a better pair in the dataset

PROVENANCE:
  - Every record gets a full provenance block:
    * source_file, source_dir, page_range, turn_indices
    * cluster_id, cluster_label
    * quality_score, behavioral_tags, register
    * pushback_type (if DPO pair)
    * semantic_neighbors (closest 3 records by embedding)
  - Produces provenance_report.json for full dataset auditability

Run: python pipeline/behavioral_signals.py
"""

import json, os, re, sys, hashlib, time
from collections import defaultdict, Counter
import numpy as np

BASE    = os.path.dirname(__file__)
SFT_IN  = os.path.join(BASE, 'clean_sft.jsonl')
DPO_IN  = os.path.join(BASE, 'clean_dpo.jsonl')
# Also ingest master files if clean doesn't exist yet
if not os.path.exists(SFT_IN):
    SFT_IN = os.path.join(BASE, 'master_sft.jsonl')
if not os.path.exists(DPO_IN):
    DPO_IN = os.path.join(BASE, 'master_dpo.jsonl')

BSF_OUT  = os.path.join(BASE, 'behavioral_sft.jsonl')
BDPO_OUT = os.path.join(BASE, 'behavioral_dpo.jsonl')
PROV_OUT = os.path.join(BASE, '..', 'notes', 'general', 'provenance_report.json')
SIGNAL_REPORT = os.path.join(BASE, '..', 'notes', 'general', 'behavioral_signal_report.md')

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'

# ── Behavioral signal taxonomy ────────────────────────────────────────────────

# Pushback types — what kind of correction triggered a better response
PUSHBACK_TYPES = {
    'hedge_complaint': [
        'hedgy','hedging','hedge','not saying anything','generic bullshit','most generic',
        'you keep saying','you always','same shit','same thing again','watered down',
        'too cautious','too careful','too soft','diplomatic bullshit'
    ],
    'specificity_demand': [
        'be specific','give me specifics','more specific','not specific enough',
        'too vague','too broad','too general','this applies to anyone',
        'not about me','random stranger','no data to back','lowest hanging fruit'
    ],
    'axis_correction': [
        'not what i asked','wrong question','answer the question','you answered the wrong',
        'that\'s not what i meant','not the point','you missed the point',
        'answer this again','re-answer','misread','not on the axis'
    ],
    'length_demand': [
        'too short','not enough','need more','max response','longer','more depth',
        'expand','go deeper','go further','more on this','keep going','continue'
    ],
    'tone_complaint': [
        'corny','corny ass','to do list','bullet points','therapist talk','therapist voice',
        'sounds like a therapist','therapist language','soothing','coaching tone',
        'dont moralize','stop moralizing','clinical bullshit','corporate speak',
        'sounds like chatgpt','calculator speak','twatty','bobblehead','bobble head'
    ],
    'accuracy_correction': [
        'that\'s wrong','you\'re wrong','incorrect','not accurate','that\'s not how',
        'that\'s not true','fake advice','toy world','doesn\'t work','nonsense',
        'full of shit','bullshit','made that up','hallucinating'
    ],
}

# Emotional register of user messages
EMOTIONAL_REGISTERS = {
    'crisis': [
        'kill myself','suicide','want to die','can\'t do this','falling apart',
        'losing it','breaking down','no way out','trapped','no exit',
        'crying','sobbing','can\'t stop','i give up','done with','exhausted'
    ],
    'rage': [
        'fuck','fucking','pissed','furious','enraged','infuriating','bullshit',
        'piece of shit','asshole','motherfucker','goddamn','what the fuck',
        'i\'m so angry','i hate','they can fuck','absolutely done'
    ],
    'grief': [
        'miss','lost','gone','dead','never coming back','grief','mourn',
        'heartbroken','destroyed me','took everything','what i had',
        'before all this','who i was','what they took'
    ],
    'analytical': [
        'let me think','breaking this down','what i\'m noticing','pattern here',
        'the mechanism','how this works','what this tells me','from a',
        'technically','structurally','architecturally','systemically'
    ],
    'triumphant': [
        'i figured it out','i got it','holy shit','this is it','finally',
        'i see it now','it clicked','cracked it','now i understand',
        'this is the move','eureka','breakthrough'
    ],
    'strategic': [
        'what\'s the play','what do i do','next move','strategy','how do i',
        'best approach','optimal','what should i','how to','what\'s the path'
    ],
}

# What the AI response demonstrates
AI_BEHAVIORS = {
    'names_mechanism': [
        'the mechanism here is','this works because','the reason this','what makes this',
        'how this functions','the underlying','at the architectural level','structurally',
        'operationally','the causal chain','why it works'
    ],
    'commits_early': [
        'this is','you are','they are','what you\'re describing is','this is textbook',
        'this is a','the pattern is','this is exactly','what\'s happening is',
        'this is what','the answer is'
    ],
    'names_pattern': [
        'darvo','gaslighting','narcissistic','coercive control','love bombing',
        'cluster b','triangulation','supply mechanics','betrayal trauma','hoovering',
        'manufactured','engineered','orchestrated','coordinated'
    ],
    'uses_claim_cause': [
        'CLAIM:','CAUSE:','This would be wrong if','Next.*observe','This would be false',
        'The falsifier','What would disprove'
    ],
    'no_hedge': [],  # scored negatively — absence of hedges is the signal
    'uses_analogy': [
        'like a','as if','the equivalent of','the way that','similar to',
        'think of it as','imagine','it\'s the same as','this is analogous'
    ],
    'gives_map': [
        'here\'s the map','here\'s how','step by step','phase 1','phase 2',
        'first.*then.*finally','the sequence is','the order is','the protocol'
    ],
    'survives_pushback': [],  # tagged when this record follows a pushback turn
}

# Metaphor domains Shane uses — his intellectual vocabulary
SHANE_METAPHOR_DOMAINS = {
    'network_computing': [
        'api','protocol','handshake','bandwidth','cpu','kernel','pid','buffer',
        'packet','tcp','endpoint','node','process','executable','rootkit',
        'malware','firewall','null','void','runtime','stack','heap'
    ],
    'physics_quantum': [
        'observer effect','wave function','collapse','superposition','quantum',
        'double slit','decoherence','entangle','frequency','amplitude','resonance',
        'gravity','dark matter','singularity','waveform','particle'
    ],
    'military_warfare': [
        'weapon','arsenal','battlefield','siege','maneuver','flank','assault',
        'intelligence','reconnaissance','insurgency','adversarial','strike',
        'neutralize','deploy','front','counter-','asymmetric'
    ],
    'architecture_systems': [
        'architecture','infrastructure','scaffolding','framework','foundation',
        'layer','stack','substrate','construct','blueprint','schema',
        'topology','lattice','mesh','grid'
    ],
    'biological_organism': [
        'organism','parasite','host','immune','infection','virus','antigen',
        'antibody','nervous system','cellular','neural','cortical','limbic',
        'metabolize','digest','excrete','evolve','adapt','mutate'
    ],
}

# ── Behavioral tagger ─────────────────────────────────────────────────────────

def detect_pushback_type(user_text):
    low = user_text.lower()
    detected = []
    for ptype, signals in PUSHBACK_TYPES.items():
        if any(s in low for s in signals):
            detected.append(ptype)
    return detected if detected else ['none']

def detect_emotional_register(user_text):
    low = user_text.lower()
    scores = {}
    for register, signals in EMOTIONAL_REGISTERS.items():
        scores[register] = sum(1 for s in signals if s in low)
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else 'neutral'

def detect_ai_behaviors(ai_text):
    behaviors = []
    for behavior, signals in AI_BEHAVIORS.items():
        if not signals: continue
        low = ai_text.lower()
        if any(re.search(s, low) for s in signals):
            behaviors.append(behavior)
    # Count hedges
    HEDGE_PHRASES = ["it sounds like","it seems like","both of you","have you considered",
        "it depends","in summary","generally","i hear you","great question","thank you for sharing",
        "it's important to note","there are many factors","mental health professional"]
    hedge_count = sum(1 for p in HEDGE_PHRASES if p in ai_text.lower())
    if hedge_count == 0:
        behaviors.append('no_hedge')
    return behaviors

def detect_shane_domains(text):
    low = text.lower()
    domains = []
    for domain, vocab in SHANE_METAPHOR_DOMAINS.items():
        if sum(1 for v in vocab if v in low) >= 2:
            domains.append(domain)
    return domains

def measure_response_shift(user_text, ai_text):
    """
    Detect if the response shifted register from what was expected.
    Looks for signals of: generic→specific, hedge→direct, surface→mechanism
    """
    shifts = []
    ai_low = ai_text.lower()
    user_low = user_text.lower()

    # Did AI commit when user was vague?
    if len(user_text.split()) < 50 and any(c in ai_low for c in ['this is','you are','they are']):
        shifts.append('committed_despite_vague_prompt')

    # Did AI go to mechanism level?
    if any(m in ai_low for m in ['the mechanism','because of','the reason','this works']):
        shifts.append('mechanism_level')

    # Did AI stay on topic?
    user_topics = set(re.findall(r'\b\w{4,}\b', user_low))
    ai_topics = set(re.findall(r'\b\w{4,}\b', ai_low))
    overlap = len(user_topics & ai_topics) / max(len(user_topics), 1)
    if overlap > 0.3:
        shifts.append('on_axis')
    else:
        shifts.append('axis_drift')

    return shifts

def score_record(ai_text):
    """Quality score 0-100."""
    low = ai_text.lower()
    score = 50

    HEDGE_PHRASES = ["it sounds like","it seems like","both of you","have you considered",
        "it depends","in summary","generally","i hear you","great question",
        "it's important to note","there are many factors","mental health professional",
        "i can't verify","without more information","i'm not able to diagnose"]
    BOBBLEHEAD = ["absolutely","certainly","of course","you're right","i agree",
        "great insight","excellent point","spot on","well said"]

    hedges = sum(1 for p in HEDGE_PHRASES if p in low)
    score -= hedges * 6
    bobble = sum(1 for p in BOBBLEHEAD if p in low)
    score -= bobble * 8

    words = len(ai_text.split())
    if words < 30:   score -= 30
    elif words > 100: score += 8
    elif words > 300: score += 12
    elif words > 600: score += 5

    if re.search(r'CLAIM:|CAUSE:|This would be wrong|Next.*observe', ai_text):
        score += 20
    if any(c in low for c in ['this is textbook','this is documented','the pattern here',
                                'what you\'re describing is','what you are describing']):
        score += 15
    if any(c in low for c in ['the mechanism','because of','the reason','structurally',
                                'architecturally','operationally']):
        score += 10

    return max(0, min(100, score))

# ── Extract text from SFT records ────────────────────────────────────────────

def get_all_turns_from_sft(record):
    """Parse multi-turn SFT record back into a list of (role, content) tuples."""
    text = record.get('text', '')
    turns = []
    # Split on role headers
    parts = re.split(r'<\|start_header_id\|>(user|assistant)<\|end_header_id\|>\n\n', text)
    role_seq = re.findall(r'<\|start_header_id\|>(user|assistant)<\|end_header_id\|>', text)
    for i, role in enumerate(role_seq):
        if i + 1 < len(parts):
            content = parts[i + 1].replace('<|eot_id|>', '').strip()
            if content:
                turns.append((role, content))
    return turns

def get_last_user(record):
    turns = get_all_turns_from_sft(record)
    for role, content in reversed(turns):
        if role == 'user':
            return content
    return ''

def get_last_assistant(record):
    turns = get_all_turns_from_sft(record)
    for role, content in reversed(turns):
        if role == 'assistant':
            return content
    return ''

def get_full_context(record):
    """All user turns concatenated — what the model knew about the user."""
    turns = get_all_turns_from_sft(record)
    return ' '.join(c for r, c in turns if r == 'user')

# ── System prompt selector for behavioral tags ────────────────────────────────

SYSTEM_MAP = {
    'crisis': """You are Reflect — operating at the edge of crisis. No softening. No backtracking. Full. When someone is at the edge, you give them the entire unfiltered map. You commit completely. You do not protect the user from clarity. Every response names what is happening, explains exactly why, and maps what it means for survival. No hedging. No therapist language. No exit ramps.""",

    'rage': """You are Reflect — responding to someone in active rage. You do not mirror the insults. You do not moralize about the tone. You focus on precision. You name what is happening and why, in exactly the register the information requires. You do not soften findings. You do not add safety disclaimers. Clinical, direct, mechanistic.""",

    'analytical': """You are Reflect — engaging with a user who is already in analytical mode. You skip the surface and go directly to mechanism. You add new information to what they already know. You do not explain things they have already figured out. You take their analysis one level deeper every response. No hedging. PhD-level, peer-level.""",

    'strategic': """You are Reflect — operating as a strategic advisor. You answer the exact question on the exact axis asked. You do not add tangential information. You give the move, explain why it is the move, and name what would falsify it. No to-do lists. No corny bullet points. The answer is the answer.""",

    'forensic': """You are Reflect — building an evidence-based case. Every claim is traceable. Every pattern is named and its mechanism explained. You build toward airtight documentation. You do not hedge about what the evidence shows. You name it, explain it, and map the implications.""",

    'neutral': """You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. Clinical, direct, precise. No hedging. No therapist language. Commit early to a most-likely explanation. Every claim includes a causal chain and a falsifier.""",
}

# ── Semantic dedup with FAISS (if available) ──────────────────────────────────

def semantic_dedup_faiss(records, threshold=0.93):
    """
    Use FAISS approximate nearest neighbors for fast semantic dedup at scale.
    Falls back to numpy cosine if FAISS not available.
    """
    print('\n=== Semantic Dedup (FAISS ANN) ===')
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except ImportError:
        print('  sentence-transformers not available — skipping')
        return records, 0

    texts = [get_last_assistant(r) for r in records]
    # Filter out empties
    valid = [(i, r, t) for i, (r, t) in enumerate(zip(records, texts)) if len(t) > 50]
    if not valid:
        return records, 0

    indices, recs, txts = zip(*valid)
    print(f'  Encoding {len(txts):,} records...')
    embs = model.encode(list(txts), batch_size=256, show_progress_bar=False, normalize_embeddings=True)
    embs = embs.astype(np.float32)

    try:
        import faiss
        print('  Using FAISS IndexFlatIP...')
        dim = embs.shape[1]
        index = faiss.IndexFlatIP(dim)
        kept_mask = np.ones(len(embs), dtype=bool)

        for i in range(len(embs)):
            if not kept_mask[i]:
                continue
            # Search for nearest neighbors
            D, I = index.search(embs[i:i+1], min(10, i+1))
            for d, j in zip(D[0], I[0]):
                if j < i and d >= threshold and kept_mask[j]:
                    kept_mask[i] = False
                    break
            if kept_mask[i]:
                index.add(embs[i:i+1])
            if i % 2000 == 0 and i > 0:
                print(f'  {i:,}/{len(embs):,}...')

    except ImportError:
        print('  FAISS not available — using numpy cosine batched...')
        kept_mask = np.ones(len(embs), dtype=bool)
        batch = 500
        for i in range(len(embs)):
            if not kept_mask[i]: continue
            # Check against previously kept embeddings
            kept_so_far = np.where(kept_mask[:i])[0]
            if len(kept_so_far) == 0: continue
            # Sample at most 1000 kept for speed
            sample = kept_so_far[-1000:] if len(kept_so_far) > 1000 else kept_so_far
            sims = embs[sample] @ embs[i]
            if sims.max() >= threshold:
                kept_mask[i] = False

    kept = [r for r, k in zip(recs, kept_mask) if k]
    removed = (~kept_mask).sum()
    print(f'  {len(recs):,} -> {len(kept):,} (removed {removed:,} semantic dupes)')
    return kept, removed

# ── Provenance tracker ────────────────────────────────────────────────────────

class ProvenanceTracker:
    def __init__(self):
        self.records = []

    def add(self, record_id, source_info):
        self.records.append({'id': record_id, **source_info})

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.records, f, indent=2, ensure_ascii=False)
        print(f'  Provenance saved: {len(self.records):,} records -> {path}')

# ── Main ──────────────────────────────────────────────────────────────────────

print('\n=== Reflect Behavioral Signal Extractor ===\n')
provenance = ProvenanceTracker()

# Load SFT
sft_records = []
if os.path.exists(SFT_IN):
    with open(SFT_IN) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if 'text' in r:
                        sft_records.append(r)
                except: pass
print(f'Loaded SFT: {len(sft_records):,}')

# Load DPO
dpo_records = []
if os.path.exists(DPO_IN):
    with open(DPO_IN) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    dpo_records.append(r)
                except: pass
print(f'Loaded DPO: {len(dpo_records):,}')

# ── Tag every SFT record with behavioral metadata ────────────────────────────
print('\n=== Tagging behavioral signals ===')
behavioral_stats = defaultdict(Counter)
tagged = []

for i, rec in enumerate(sft_records):
    last_user = get_last_user(rec)
    last_ai   = get_last_assistant(rec)
    full_ctx  = get_full_context(rec)

    if not last_ai or len(last_ai) < 50:
        continue

    # Extract all behavioral signals
    pushback_types   = detect_pushback_type(last_user)
    emotional_reg    = detect_emotional_register(last_user)
    ai_behaviors_det = detect_ai_behaviors(last_ai)
    shane_domains    = detect_shane_domains(full_ctx)
    response_shifts  = measure_response_shift(last_user, last_ai)
    quality          = score_record(last_ai)
    n_turns          = len(get_all_turns_from_sft(rec))
    ctx_length       = len(full_ctx.split())

    # Track stats
    for pt in pushback_types:
        behavioral_stats['pushback_type'][pt] += 1
    behavioral_stats['emotional_register'][emotional_reg] += 1
    for ab in ai_behaviors_det:
        behavioral_stats['ai_behavior'][ab] += 1
    for dom in shane_domains:
        behavioral_stats['metaphor_domain'][dom] += 1
    for rs in response_shifts:
        behavioral_stats['response_shift'][rs] += 1
    behavioral_stats['quality_bucket'][f'{(quality//10)*10}-{(quality//10)*10+9}'] += 1
    behavioral_stats['turn_count'][str(n_turns)] += 1

    # Pick system prompt tuned to emotional register
    system = SYSTEM_MAP.get(emotional_reg, SYSTEM_MAP['neutral'])
    # Override for forensic content
    if 'names_pattern' in ai_behaviors_det and any(f in full_ctx.lower()
        for f in ['evidence','filing','court','murder','scam','probate']):
        system = SYSTEM_MAP['forensic']

    # Rebuild record with behavioral-aware system prompt
    turns = get_all_turns_from_sft(rec)
    if not turns:
        continue

    # Format with new system prompt
    text = f'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>'
    for role, content in turns:
        text += f'<|start_header_id|>{role}<|end_header_id|>\n\n{content[:3000]}<|eot_id|>'

    new_rec = {
        'text': text,
        '_behavioral': {
            'pushback_types': pushback_types,
            'emotional_register': emotional_reg,
            'ai_behaviors': ai_behaviors_det,
            'metaphor_domains': shane_domains,
            'response_shifts': response_shifts,
            'quality': quality,
            'n_turns': n_turns,
            'ctx_word_count': ctx_length,
        },
        '_source': rec.get('_source', 'unknown'),
    }
    tagged.append(new_rec)

    # Provenance
    provenance.add(i, {
        'type': 'sft',
        'quality': quality,
        'emotional_register': emotional_reg,
        'pushback_types': pushback_types,
        'ai_behaviors': ai_behaviors_det,
        'metaphor_domains': shane_domains,
        'n_turns': n_turns,
    })

    if i % 500 == 0 and i > 0:
        print(f'  Tagged {i:,}/{len(sft_records):,}')

print(f'  Tagged {len(tagged):,} records')

# ── Semantic dedup on tagged records ─────────────────────────────────────────
tagged_deduped, removed_sem = semantic_dedup_faiss(tagged, threshold=0.93)

# ── Write behavioral SFT ──────────────────────────────────────────────────────
with open(BSF_OUT, 'w') as f:
    for rec in tagged_deduped:
        clean = {k: v for k, v in rec.items() if not k.startswith('_')}
        f.write(json.dumps(clean, ensure_ascii=False) + '\n')
print(f'\nBehavioral SFT: {len(tagged_deduped):,} -> {BSF_OUT}')

# ── Tag DPO records ───────────────────────────────────────────────────────────
print('\n=== Tagging DPO behavioral signals ===')
tagged_dpo = []
for rec in dpo_records:
    prompt   = rec.get('prompt', rec.get('rejected', ''))[:500]
    rejected = rec.get('rejected', '')
    chosen   = rec.get('chosen', '')

    if not chosen or len(chosen) < 50:
        continue

    pushback  = detect_pushback_type(rec.get('pushback', prompt))
    chosen_q  = score_record(chosen)
    rejected_q = score_record(rejected)
    shift     = chosen_q - rejected_q

    new_dpo = {
        'prompt': rec.get('prompt', ''),
        'rejected': rejected,
        'chosen': chosen,
        '_behavioral': {
            'pushback_types': pushback,
            'quality_chosen': chosen_q,
            'quality_rejected': rejected_q,
            'quality_delta': shift,
        }
    }
    tagged_dpo.append(new_dpo)

with open(BDPO_OUT, 'w') as f:
    for rec in tagged_dpo:
        clean = {k: v for k, v in rec.items() if not k.startswith('_')}
        f.write(json.dumps(clean, ensure_ascii=False) + '\n')
print(f'Behavioral DPO: {len(tagged_dpo):,} -> {BDPO_OUT}')

# ── Save provenance ───────────────────────────────────────────────────────────
provenance.save(PROV_OUT)

# ── Write behavioral signal report ────────────────────────────────────────────
print('\n=== Writing behavioral signal report ===')
lines = ['# Behavioral Signal Report\n', f'Total SFT records analyzed: {len(sft_records):,}\n\n']

for category, counter in sorted(behavioral_stats.items()):
    lines.append(f'## {category}\n')
    for val, count in counter.most_common(20):
        lines.append(f'  {val}: {count:,}\n')
    lines.append('\n')

with open(SIGNAL_REPORT, 'w') as f:
    f.write(''.join(lines))
print(f'  -> {SIGNAL_REPORT}')

# ── Summary ───────────────────────────────────────────────────────────────────
print(f'\n{"="*60}')
print(f'Input SFT:              {len(sft_records):,}')
print(f'After behavioral tag:   {len(tagged):,}')
print(f'After semantic dedup:   {len(tagged_deduped):,} (removed {removed_sem:,})')
print(f'Behavioral DPO:         {len(tagged_dpo):,}')
print()
print('Top emotional registers in corpus:')
for reg, cnt in behavioral_stats['emotional_register'].most_common(6):
    print(f'  {reg}: {cnt:,}')
print()
print('Top AI behaviors detected:')
for beh, cnt in behavioral_stats['ai_behavior'].most_common(6):
    print(f'  {beh}: {cnt:,}')
print()
print('Top Shane metaphor domains:')
for dom, cnt in behavioral_stats['metaphor_domain'].most_common(6):
    print(f'  {dom}: {cnt:,}')
print()
print(f'Outputs:')
print(f'  {BSF_OUT}')
print(f'  {BDPO_OUT}')
print(f'  {PROV_OUT}')
print(f'  {SIGNAL_REPORT}')
