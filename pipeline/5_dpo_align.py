"""
Step 5: DPO (Direct Preference Optimization) alignment pass.

Takes the SFT checkpoint from step 4 and runs a preference learning pass
using PsyCoPref — 36K chosen/rejected response pairs rated on empathy,
safety, autonomy, clarity, and staging. This is what teaches the model
TONE — not just correct content, but the right delivery.

Run AFTER step 4 completes:
  HF_TOKEN=hf_xxx python pipeline/5_dpo_align.py

Output: ./reflect-llama3-dpo/
"""

import os
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, PeftModel
from trl import DPOTrainer, DPOConfig

HF_TOKEN   = os.environ.get("HF_TOKEN", "")
SFT_DIR    = "./reflect-llama3-sft"
OUT_DIR    = "./reflect-llama3-dpo"
USE_4BIT   = True

SYSTEM_PROMPT = (
    "You are Reflect — a trauma-informed analysis tool built on the clinical research of "
    "Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. "
    "You help people who are actively being abused understand what is being done to them. "
    "Clinical, direct, precise. No hedging."
)


def format_dpo_row(row):
    prompt = row.get("prompt") or row.get("question") or row.get("input") or ""
    chosen = row.get("chosen") or row.get("chosen_response") or ""
    rejected = row.get("rejected") or row.get("rejected_response") or ""
    if isinstance(chosen, list):
        chosen = " ".join(chosen)
    if isinstance(rejected, list):
        rejected = " ".join(rejected)

    def wrap(response):
        return (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n{response}<|eot_id|>"
        )

    return {
        "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "chosen": chosen,
        "rejected": rejected,
    }


# ── Load dataset ────────────────────────────────────────────────────────────
print("Loading PsyCoPref preference dataset...")
raw = load_dataset("Psychotherapy-LLM/PsyCoPref", split="train")
ds = raw.map(format_dpo_row, remove_columns=raw.column_names)
ds = ds.filter(lambda x: len(x["chosen"]) > 20 and len(x["rejected"]) > 20)
split = ds.train_test_split(test_size=0.05, seed=42)
train_ds = split["train"]
eval_ds  = split["test"]
print(f"  Train: {len(train_ds)}  Eval: {len(eval_ds)}")

# ── Load SFT checkpoint ─────────────────────────────────────────────────────
bnb_config = BitsAndBytesConfig(
    load_in_4bit=USE_4BIT,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
) if USE_4BIT else None

print(f"Loading SFT model from {SFT_DIR}...")
tokenizer = AutoTokenizer.from_pretrained(SFT_DIR)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    SFT_DIR,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

model_ref = AutoModelForCausalLM.from_pretrained(
    SFT_DIR,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# ── DPO LoRA ────────────────────────────────────────────────────────────────
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# ── Training ─────────────────────────────────────────────────────────────────
dpo_config = DPOConfig(
    output_dir=OUT_DIR,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=5e-5,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    bf16=True,
    evaluation_strategy="steps",
    eval_steps=200,
    save_steps=200,
    save_total_limit=2,
    logging_steps=50,
    beta=0.1,             # DPO temperature — lower = stronger preference signal
    max_length=2048,
    max_prompt_length=1024,
    report_to="none",
)

trainer = DPOTrainer(
    model=model,
    ref_model=model_ref,
    args=dpo_config,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    tokenizer=tokenizer,
    peft_config=peft_config,
)

print("Starting DPO alignment pass...")
trainer.train()

print(f"Saving to {OUT_DIR}")
trainer.save_model(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("Done.")
