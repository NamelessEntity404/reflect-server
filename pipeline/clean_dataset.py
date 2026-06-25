"""
Reflect — Dataset Cleaning Pipeline
Runs AFTER build_dataset.py produces master_sft.jsonl + master_dpo.jsonl

Three-pass deduplication and clustering:
  Pass 1: MinHash LSH   — exact + near-duplicate removal at scale (Jaccard similarity)
  Pass 2: Embedding cosine clustering — semantic duplicate removal using MiniLM embeddings
  Pass 3: Quality re-scoring — final quality filter on what survives

Also runs on ALL PDF text (not just extracted pairs) to identify:
  - Which document regions are semantically unique (mine harder)
  - Which regions are duplicated across files (skip)
  - Cluster labels for each document section

Run: python pipeline/clean_dataset.py
"""

import json, os, re, sys, hashlib, time
import numpy as np

BASE = os.path.dirname(__file__)
SFT_IN  = os.path.join(BASE, 'master_sft.jsonl')
DPO_IN  = os.path.join(BASE, 'master_dpo.jsonl')
SFT_OUT = os.path.join(BASE, 'clean_sft.jsonl')
DPO_OUT = os.path.join(BASE, 'clean_dpo.jsonl')
CLUSTER_REPORT = os.path.join(BASE, '..', 'notes', 'general', 'cluster_report.md')

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'

# ── Text extraction helpers ───────────────────────────────────────────────────

def get_text_field(record):
    """Extract the assistant response text from an SFT record."""
    text = record.get('text', '')
    # Pull out just the assistant response — last <|eot_id|> block
    parts = text.split('<|start_header_id|>assistant<|end_header_id|>')
    if len(parts) > 1:
        return parts[-1].replace('<|eot_id|>', '').strip()
    return text

def get_prompt_field(record):
    """Extract the last user prompt from an SFT record."""
    text = record.get('text', '')
    parts = text.split('<|start_header_id|>user<|end_header_id|>')
    if len(parts) > 1:
        last_user = parts[-1].split('<|start_header_id|>')[0]
        return last_user.replace('<|eot_id|>', '').strip()
    return ''

def shingles(text, k=5):
    """k-word shingles for MinHash."""
    words = re.findall(r'\w+', text.lower())
    return set(' '.join(words[i:i+k]) for i in range(len(words)-k+1))

def ngram_shingles(text, n=3):
    """Character n-grams for MinHash."""
    text = re.sub(r'\s+', ' ', text.lower())
    return set(text[i:i+n] for i in range(len(text)-n+1))

# ── PASS 1: MinHash LSH ───────────────────────────────────────────────────────

def pass1_minhash_lsh(records, threshold=0.7, num_perm=128):
    """
    MinHash LSH deduplication.
    Removes records whose assistant response is >= threshold Jaccard similar to any seen record.
    threshold=0.7 means 70% shingle overlap = duplicate.
    """
    print(f'\n=== PASS 1: MinHash LSH (threshold={threshold}, num_perm={num_perm}) ===')
    try:
        from datasketch import MinHash, MinHashLSH
    except ImportError:
        print('  datasketch not installed — skipping MinHash pass')
        return records, 0

    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    kept = []
    removed = 0

    for i, rec in enumerate(records):
        text = get_text_field(rec)
        if len(text) < 50:
            kept.append(rec)
            continue

        m = MinHash(num_perm=num_perm)
        for shingle in ngram_shingles(text, n=4):
            m.update(shingle.encode('utf8'))

        key = f'rec_{i}'
        try:
            results = lsh.query(m)
            if results:
                removed += 1
                continue
            lsh.insert(key, m)
            kept.append(rec)
        except Exception:
            kept.append(rec)

        if i % 1000 == 0 and i > 0:
            print(f'  {i:,} processed | {removed:,} removed | {len(kept):,} kept')

    print(f'  DONE: {len(records):,} -> {len(kept):,} (removed {removed:,} near-dupes)')
    return kept, removed

# ── PASS 2: Embedding Cosine Clustering ──────────────────────────────────────

def pass2_embedding_cluster(records, sim_threshold=0.92, batch_size=256):
    """
    Embed each assistant response using MiniLM.
    Cluster by cosine similarity.
    Keep only one representative per cluster.
    sim_threshold=0.92 means 92%+ cosine similarity = semantic duplicate.
    """
    print(f'\n=== PASS 2: Embedding Cosine Clustering (threshold={sim_threshold}) ===')
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print('  sentence-transformers not installed — skipping embedding pass')
        return records, 0

    print('  Loading MiniLM model...')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    texts = [get_text_field(r) for r in records]
    print(f'  Encoding {len(texts):,} records in batches of {batch_size}...')

    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embs = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        embeddings.append(embs)
        if i % 2000 == 0 and i > 0:
            print(f'  Encoded {i:,}/{len(texts):,}')

    embeddings = np.vstack(embeddings)
    print(f'  Embeddings shape: {embeddings.shape}')

    # Greedy clustering: for each record, check if it's too similar to any kept record
    kept_indices = []
    kept_embeddings = []
    removed = 0

    for i in range(len(embeddings)):
        if not kept_embeddings:
            kept_indices.append(i)
            kept_embeddings.append(embeddings[i])
            continue

        # Compare against kept embeddings in batches
        kept_arr = np.array(kept_embeddings[-2000:])  # only check recent 2000 for speed
        sims = cosine_similarity([embeddings[i]], kept_arr)[0]
        if sims.max() >= sim_threshold:
            removed += 1
        else:
            kept_indices.append(i)
            kept_embeddings.append(embeddings[i])

        if i % 1000 == 0 and i > 0:
            print(f'  {i:,} processed | {removed:,} semantic dupes removed')

    kept = [records[i] for i in kept_indices]
    print(f'  DONE: {len(records):,} -> {len(kept):,} (removed {removed:,} semantic dupes)')
    return kept, removed, embeddings, kept_indices

# ── PASS 3: Quality Re-score ──────────────────────────────────────────────────

HEDGE_PHRASES = [
    "it sounds like","it seems like","both of you","both sides","couples therapy",
    "have you considered their","their perspective","i can't verify","without more information",
    "there could be many","i'm not able to diagnose","that must be hard",
    "i want to be careful","i cannot determine","you may want to speak with",
    "it depends","in summary","generally speaking","let's explore","both parties",
    "i hear you","great question","i appreciate you sharing","it's important to note",
    "there are many factors","i'd recommend speaking","mental health professional",
]

DIRECT_SIGNALS = [
    'darvo','gaslighting','narcissist','coercive','cluster b','manipulation','betrayal',
    'classifier','trust score','metadata','fingerprint','suppression','algorithm',
    'this is textbook','this is documented','the pattern here','this is a',
    'CLAIM:','CAUSE:','This would be wrong','Next.*observe',
    'what you are describing','what you\'re describing',
    'commit','mechanism','directly','precisely','forensic',
]

def pass3_quality(records, min_score=30):
    """Final quality filter. Remove anything below min_score."""
    print(f'\n=== PASS 3: Quality Re-score (min={min_score}) ===')
    kept = []
    removed = 0

    for rec in records:
        text = get_text_field(rec)
        low = text.lower()

        score = 50
        hedges = sum(1 for p in HEDGE_PHRASES if p in low)
        score -= hedges * 6

        words = len(text.split())
        if words < 30:  score -= 30
        if words > 100: score += 10
        if words > 300: score += 10
        if words > 600: score += 5

        direct = sum(1 for s in DIRECT_SIGNALS if s.lower() in low)
        score += min(direct * 4, 25)

        if re.search(r'CLAIM:|CAUSE:|This would be wrong|Next.*observe', text):
            score += 20

        if score >= min_score:
            rec['_quality'] = score
            kept.append(rec)
        else:
            removed += 1

    print(f'  DONE: {len(records):,} -> {len(kept):,} (removed {removed:,} low-quality)')
    avg = sum(r.get('_quality', 50) for r in kept) / max(len(kept), 1)
    print(f'  Average quality score: {avg:.1f}')
    return kept, removed

# ── PDF-level clustering for mining report ────────────────────────────────────

def cluster_pdf_corpus():
    """
    Read all PDF text files from /tmp/full_texts/ (if they exist),
    embed each 500-word chunk, cluster, and produce a report of:
    - Which chunks are unique (mine harder)
    - Which chunks are duplicated across files (skip)
    """
    print('\n=== PDF Corpus Clustering ===')
    txt_dir = '/tmp/full_texts'
    if not os.path.exists(txt_dir):
        print('  /tmp/full_texts not found — run full text extraction first')
        return

    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import MiniBatchKMeans
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print('  sentence-transformers/sklearn not installed')
        return

    # Load all text files
    chunks = []  # (filename, chunk_text)
    for fname in os.listdir(txt_dir):
        if not fname.endswith('.txt'): continue
        with open(os.path.join(txt_dir, fname)) as f:
            text = f.read()
        words = text.split()
        # Split into 500-word chunks
        for i in range(0, len(words), 500):
            chunk = ' '.join(words[i:i+500])
            if len(chunk) > 200:
                chunks.append((fname, chunk))

    if not chunks:
        print('  No text chunks found')
        return

    print(f'  Total chunks: {len(chunks):,} from {len(set(c[0] for c in chunks))} files')

    model = SentenceTransformer('all-MiniLM-L6-v2')
    print('  Encoding chunks...')
    texts = [c[1] for c in chunks]
    embs = model.encode(texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)

    # K-means clustering
    n_clusters = min(50, len(chunks) // 10)
    print(f'  Clustering into {n_clusters} topic clusters...')
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    labels = km.fit_predict(embs)

    # Build cluster report
    from collections import defaultdict, Counter
    cluster_files = defaultdict(list)
    cluster_samples = defaultdict(list)
    for i, (fname, chunk) in enumerate(chunks):
        cluster_files[labels[i]].append(fname.replace('.txt','')[:50])
        if len(cluster_samples[labels[i]]) < 2:
            cluster_samples[labels[i]].append(chunk[:200])

    # Identify cross-file clusters (duplicated content) vs single-file clusters (unique)
    report_lines = ['# PDF Corpus Cluster Report\n']
    report_lines.append(f'Total chunks: {len(chunks):,}\n')
    report_lines.append(f'Total clusters: {n_clusters}\n\n')

    cross_file_clusters = []
    unique_clusters = []
    for cid in range(n_clusters):
        files_in_cluster = cluster_files[cid]
        unique_files = list(set(files_in_cluster))
        if len(unique_files) > 2:
            cross_file_clusters.append((cid, unique_files, cluster_samples[cid]))
        else:
            unique_clusters.append((cid, unique_files, cluster_samples[cid]))

    report_lines.append(f'## Cross-file clusters (duplicated content — lower mining priority)\n')
    report_lines.append(f'Count: {len(cross_file_clusters)}\n\n')
    for cid, files, samples in sorted(cross_file_clusters, key=lambda x: -len(x[1])):
        report_lines.append(f'**Cluster {cid}** ({len(files)} files)\n')
        report_lines.append(f'Files: {", ".join(set(files))[:200]}\n')
        report_lines.append(f'Sample: {samples[0][:150]}\n\n')

    report_lines.append(f'\n## Single-file clusters (unique content — HIGH mining priority)\n')
    report_lines.append(f'Count: {len(unique_clusters)}\n\n')
    for cid, files, samples in unique_clusters:
        report_lines.append(f'**Cluster {cid}** ({files[0] if files else "?"})\n')
        report_lines.append(f'Sample: {samples[0][:150] if samples else ""}\n\n')

    with open(CLUSTER_REPORT, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f'  Cluster report -> {CLUSTER_REPORT}')
    print(f'  Unique clusters (mine harder): {len(unique_clusters)}')
    print(f'  Cross-file clusters (duplicated): {len(cross_file_clusters)}')

# ── MAIN ─────────────────────────────────────────────────────────────────────

print('\n=== Reflect Dataset Cleaner ===\n')

# Load SFT records
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
    print(f'Loaded SFT: {len(sft_records):,} records from {SFT_IN}')
else:
    print(f'SFT file not found: {SFT_IN}')

# Load DPO records
dpo_records = []
if os.path.exists(DPO_IN):
    with open(DPO_IN) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if 'chosen' in r or 'rejected' in r:
                        dpo_records.append(r)
                except: pass
    print(f'Loaded DPO: {len(dpo_records):,} records from {DPO_IN}')

# ── SFT cleaning pipeline ──────────────────────────────────────────────────────
if sft_records:
    # Pass 1: MinHash LSH
    sft_p1, removed_p1 = pass1_minhash_lsh(sft_records, threshold=0.75, num_perm=128)

    # Pass 2: Embedding cosine clustering
    result = pass2_embedding_cluster(sft_p1, sim_threshold=0.92, batch_size=256)
    if len(result) == 4:
        sft_p2, removed_p2, embeddings, kept_indices = result
    else:
        sft_p2, removed_p2 = result
        embeddings, kept_indices = None, None

    # Pass 3: Quality filter
    sft_final, removed_p3 = pass3_quality(sft_p2, min_score=25)

    # Write clean SFT
    with open(SFT_OUT, 'w') as f:
        for r in sft_final:
            r.pop('_quality', None)
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f'\nSFT pipeline complete:')
    print(f'  Input:          {len(sft_records):,}')
    print(f'  After MinHash:  {len(sft_p1):,} (-{removed_p1:,})')
    print(f'  After Embedding:{len(sft_p2):,} (-{removed_p2:,})')
    print(f'  After Quality:  {len(sft_final):,} (-{removed_p3:,})')
    print(f'  -> {SFT_OUT}')

# ── DPO cleaning ───────────────────────────────────────────────────────────────
if dpo_records:
    print(f'\n=== DPO Cleaning ===')
    # MinHash on chosen responses
    # Wrap in text format for MinHash
    wrapped = [{'text': r.get('chosen', r.get('rejected', ''))} for r in dpo_records]
    cleaned_wrapped, removed_dpo = pass1_minhash_lsh(wrapped, threshold=0.80, num_perm=64)
    # Map back
    kept_dpo = [dpo_records[i] for i in range(len(dpo_records)) if i < len(cleaned_wrapped)]

    with open(DPO_OUT, 'w') as f:
        for r in kept_dpo:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f'  DPO: {len(dpo_records):,} -> {len(kept_dpo):,} (removed {removed_dpo:,})')
    print(f'  -> {DPO_OUT}')

# ── PDF corpus clustering ──────────────────────────────────────────────────────
cluster_pdf_corpus()

print('\n=== DONE ===')
print(f'Clean SFT: {SFT_OUT}')
print(f'Clean DPO: {DPO_OUT}')
print(f'Cluster report: {CLUSTER_REPORT}')

# ── AUTO-RUN BEHAVIORAL SIGNALS ───────────────────────────────────────────────
print('\n\nAuto-running behavioral_signals.py...')
import subprocess, sys, os
result = subprocess.run(
    [sys.executable, '-W', 'ignore', os.path.join(os.path.dirname(__file__), 'behavioral_signals.py')],
    capture_output=False
)
