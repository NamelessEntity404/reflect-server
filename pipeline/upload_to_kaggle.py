"""
Upload EVERYTHING to Kaggle dataset: baddata404/reflect-personal-training

Uploads:
  - All JSONL training files (SFT, DPO, prompts, all versions)
  - All RAG notes (.md files)
  - All full PDF text extractions (.txt files)
  - The classifier taxonomy CSV (212k rows)
  - The full_chat.txt conversation context
  - Behavioral signal report, cluster report, provenance

Run: python pipeline/upload_to_kaggle.py
Requires: kaggle CLI installed and ~/.kaggle/kaggle.json present
"""

import os, shutil, json, subprocess, glob

BASE     = os.path.dirname(__file__)
REPO     = os.path.join(BASE, '..')
STAGING  = '/tmp/kaggle_upload'
DATASET  = 'baddatalogin/reflect-personal-training'

shutil.rmtree(STAGING, ignore_errors=True)
os.makedirs(STAGING, exist_ok=True)

def copy(src, dest_name=None):
    if not os.path.exists(src):
        print(f'  SKIP (missing): {src}')
        return False
    size = os.path.getsize(src)
    if size == 0:
        print(f'  SKIP (empty): {os.path.basename(src)}')
        return False
    dest = os.path.join(STAGING, dest_name or os.path.basename(src))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    print(f'  OK  {os.path.basename(dest)} ({size/1024/1024:.1f}MB)')
    return True

print('\n=== Staging all files for Kaggle upload ===\n')

# ── 1. ALL JSONL training files ───────────────────────────────────────────────
print('── JSONL Training Files ──')
jsonl_files = glob.glob(os.path.join(BASE, '*.jsonl'))
for f in sorted(jsonl_files):
    copy(f)

# ── 2. ALL RAG notes ──────────────────────────────────────────────────────────
print('\n── RAG Notes ──')
notes_dir = os.path.join(REPO, 'notes', 'general')
notes_out  = os.path.join(STAGING, 'notes')
os.makedirs(notes_out, exist_ok=True)
for f in sorted(glob.glob(os.path.join(notes_dir, '*.md'))):
    copy(f, os.path.join('notes', os.path.basename(f)))

# ── 3. ALL full PDF text extractions ─────────────────────────────────────────
print('\n── Full PDF Text Extractions ──')
texts_out = os.path.join(STAGING, 'pdf_texts')
os.makedirs(texts_out, exist_ok=True)
txt_dir = '/tmp/full_texts'
if os.path.exists(txt_dir):
    for f in sorted(glob.glob(os.path.join(txt_dir, '*.txt'))):
        copy(f, os.path.join('pdf_texts', os.path.basename(f)))
else:
    print('  /tmp/full_texts not found — run full text extraction first')

# ── 4. Classifier taxonomy CSV ────────────────────────────────────────────────
print('\n── Classifier Taxonomy ──')
classifier_md = os.path.join(notes_dir, 'classifier_taxonomy.md')
copy(classifier_md, 'notes/classifier_taxonomy.md')

# ── 5. full_chat.txt ──────────────────────────────────────────────────────────
print('\n── Conversation Context ──')
copy(os.path.expanduser('~/Desktop/full_chat.txt'))

# ── 6. Behavioral / cluster / provenance reports ─────────────────────────────
print('\n── Reports ──')
report_files = [
    os.path.join(notes_dir, 'behavioral_signal_report.md'),
    os.path.join(notes_dir, 'cluster_report.md'),
    os.path.join(notes_dir, 'provenance_report.json'),
]
for f in report_files:
    copy(f, os.path.join('notes', os.path.basename(f)))

# ── 7. Pipeline scripts themselves (for reproducibility) ─────────────────────
print('\n── Pipeline Scripts ──')
scripts_out = os.path.join(STAGING, 'pipeline')
os.makedirs(scripts_out, exist_ok=True)
for f in glob.glob(os.path.join(BASE, '*.py')):
    copy(f, os.path.join('pipeline', os.path.basename(f)))
# Kaggle notebook
copy(os.path.join(BASE, 'reflect_train_kaggle.ipynb'),
     os.path.join('pipeline', 'reflect_train_kaggle.ipynb'))

# ── 8. Write dataset-metadata.json ───────────────────────────────────────────
print('\n── Writing dataset-metadata.json ──')
metadata = {
    "title": "Reflect Personal Training — Full Corpus",
    "id": DATASET,
    "licenses": [{"name": "other"}],
    "keywords": [
        "nlp", "fine-tuning", "llama", "mental-health", "trauma",
        "abuse", "coercive-control", "classifier", "platform-intelligence",
        "behavioral-signals", "dpo", "sft", "rag"
    ],
    "subtitle": (
        "Full training corpus for Reflect — trauma-informed LLM. "
        "Includes multi-turn SFT, DPO pairs, behavioral signal tags, "
        "semantic dedup via MinHash LSH + MiniLM embeddings, "
        "RAG notes, full PDF text extractions, classifier taxonomy (212k rows), "
        "and provenance tracking across ~90 source documents."
    ),
    "description": (
        "All training data, cleaned data, RAG notes, full PDF text extractions, "
        "behavioral signal reports, cluster reports, and pipeline scripts for "
        "fine-tuning LLaMA 3 8B as Reflect — a trauma-informed analysis tool "
        "built on the clinical research of Durvasula, Freyd, Vaknin, Hughes, "
        "Navarro, and Taylor."
    )
}
with open(os.path.join(STAGING, 'dataset-metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=2)
print('  OK  dataset-metadata.json')

# ── Summary ───────────────────────────────────────────────────────────────────
all_files = []
for root, dirs, files in os.walk(STAGING):
    for fname in files:
        fpath = os.path.join(root, fname)
        all_files.append((fpath, os.path.getsize(fpath)))

total_mb = sum(s for _, s in all_files) / 1024 / 1024
print(f'\nStaged {len(all_files)} files, {total_mb:.0f}MB total')
print(f'Location: {STAGING}')

# ── Upload ────────────────────────────────────────────────────────────────────
print(f'\n=== Uploading to Kaggle: {DATASET} ===')

# Check if dataset exists
check = subprocess.run(
    ['python3', '-m', 'kaggle', 'datasets', 'status', DATASET],
    capture_output=True, text=True
)

if check.returncode == 0:
    print('Dataset exists — creating new version...')
    result = subprocess.run(
        ['python3', '-m', 'kaggle', 'datasets', 'version',
         '-p', STAGING,
         '-m', 'Full corpus update: multi-turn SFT, behavioral signals, MinHash+embedding dedup, all PDF texts, RAG notes, provenance',
         '--dir-mode', 'zip'],
        capture_output=False
    )
else:
    print('Creating new dataset...')
    result = subprocess.run(
        ['python3', '-m', 'kaggle', 'datasets', 'create',
         '-p', STAGING,
         '--dir-mode', 'zip'],
        capture_output=False
    )

if result.returncode == 0:
    print(f'\nDone. Dataset at: https://www.kaggle.com/datasets/{DATASET}')
else:
    print(f'\nUpload failed (exit {result.returncode})')
    print('Files are staged at:', STAGING)
    print('You can upload manually: kaggle datasets version -p', STAGING, '-m "update"')
