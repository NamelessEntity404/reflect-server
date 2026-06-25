# Reflect Training Pipeline

## Order of operations

### Step 1 — Download HuggingFace datasets
```bash
pip install -r pipeline/requirements.txt
python pipeline/1_download_datasets.py
```
Downloads and merges:
- `Amod/mental_health_counseling_conversations` — 3,512 real therapist Q&A pairs
- `fadodr/mental_health_therapy` — 12,258 therapy dialogue pairs (SFT-ready)
- `ShenLab/MentalChat16K` — 16,084 counseling conversations
- `mpingale/mental-health-chat-dataset` — 2,780 CounselChat licensed therapist pairs
- `Psychotherapy-LLM/PsyCoPref` — 36,653 preference pairs (used in step 5)

Output: `pipeline/raw_hf_combined.jsonl`

---

### Step 2 — Build your domain corpus
Populate the notes folders with your research on each author:
```
notes/durvasula/    — narcissistic abuse, idealize-devalue-discard, love bombing, hoovering
notes/freyd/        — DARVO, betrayal trauma, institutional betrayal
notes/vaknin/       — supply mechanics, shared fantasy, mortification, no contact
notes/hughes/       — behavioral influence stack, compliance triggers, PEACE model
notes/navarro/      — nonverbal tells, limbic responses, deception reads
notes/taylor/       — victim-blaming, misdiagnosis, systemic retraumatization
notes/general/      — coercive control, IPV research, post-separation abuse, trauma bonding
```
Any `.md` or `.txt` file works. Paste book excerpts, paper summaries, your own notes.

Then run:
```bash
python pipeline/2_build_domain_corpus.py
```
Output: `pipeline/domain_pairs.jsonl`

---

### Step 3 — Merge and clean
```bash
python pipeline/3_merge_and_clean.py
```
Deduplicates everything, filters short/low-quality records, formats to LLaMA 3 chat template.

Output: `pipeline/train.jsonl`, `pipeline/eval.jsonl`

---

### Step 4 — Fine-tune LLaMA 3 8B with QLoRA
Requires:
- HuggingFace account with LLaMA 3 access (request at huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- GPU with 16GB+ VRAM (RunPod, Lambda, Colab A100, or local)
- `HF_TOKEN` env var

```bash
HF_TOKEN=hf_xxx python pipeline/4_finetune_sft.py
```
Output: `./reflect-llama3-sft/`

---

### Step 5 — DPO alignment pass
Tunes tone using PsyCoPref preference pairs — this is what makes it sound right, not just say the right things.

```bash
HF_TOKEN=hf_xxx python pipeline/5_dpo_align.py
```
Output: `./reflect-llama3-dpo/`

---

### Step 6 — Push to HuggingFace Hub + switch Railway backend
```bash
HF_TOKEN=hf_xxx HF_REPO=yourusername/reflect-llama3 python pipeline/6_push_and_serve.py
```

Then on Railway, add env var:
```
REFLECT_MODEL_REPO=yourusername/reflect-llama3
```

The server automatically switches from Claude to your trained model. No other changes needed.

---

## Current state
- Server runs Claude with full system prompt as interim brain while training happens
- Once REFLECT_MODEL_REPO is set on Railway, it switches to your fine-tuned LLaMA 3
- RAG layer (notes_mcp_server.py) sits on top of either backend
