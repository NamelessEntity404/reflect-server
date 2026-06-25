"""
Step 4: Fine-tune LLaMA 3 8B Instruct with QLoRA + SFTTrainer.

This does full supervised fine-tuning on your merged training set.
Runs on a single GPU (16GB+ VRAM). For consumer GPUs use 4-bit quant.
For CPU-only: set USE_4BIT=False and expect it to be very slow.

Requirements:
  - HuggingFace account with LLaMA 3 access approved:
    https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct
  - HF_TOKEN env var set to your HuggingFace token
  - pip install -r pipeline/requirements.txt

Run:
  HF_TOKEN=hf_xxx python pipeline/4_finetune_sft.py

Output: ./reflect-llama3-sft/  (local checkpoint)
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

HF_TOKEN   = os.environ.get("HF_TOKEN", "")
BASE_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
OUT_DIR    = "./reflect-llama3-sft"
TRAIN_FILE = os.path.join(os.path.dirname(__file__), "train.jsonl")
EVAL_FILE  = os.path.join(os.path.dirname(__file__), "eval.jsonl")
USE_4BIT   = True  # set False if you have 40GB+ VRAM

# ── Quantization ────────────────────────────────────────────────────────────
bnb_config = BitsAndBytesConfig(
    load_in_4bit=USE_4BIT,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
) if USE_4BIT else None

# ── Model + Tokenizer ───────────────────────────────────────────────────────
print(f"Loading base model: {BASE_MODEL}")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, token=HF_TOKEN)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    token=HF_TOKEN,
    torch_dtype=torch.bfloat16 if not USE_4BIT else None,
)

if USE_4BIT:
    model = prepare_model_for_kbit_training(model)

# ── LoRA config ─────────────────────────────────────────────────────────────
# Targeting all attention + MLP projections for full-coverage fine-tuning
lora_config = LoraConfig(
    r=32,                          # rank — higher = more capacity, more VRAM
    lora_alpha=64,                 # scaling factor
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ── Dataset ─────────────────────────────────────────────────────────────────
train_ds = load_dataset("json", data_files=TRAIN_FILE, split="train")
eval_ds  = load_dataset("json", data_files=EVAL_FILE,  split="train")

# ── Training args ────────────────────────────────────────────────────────────
training_args = TrainingArguments(
    output_dir=OUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,     # effective batch size = 16
    gradient_checkpointing=True,
    optim="paged_adamw_32bit",
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    weight_decay=0.001,
    fp16=False,
    bf16=True,
    max_grad_norm=0.3,
    evaluation_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=100,
    save_total_limit=3,
    load_best_model_at_end=True,
    logging_steps=25,
    report_to="none",
    group_by_length=True,
)

# ── Trainer ──────────────────────────────────────────────────────────────────
trainer = SFTTrainer(
    model=model,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    args=training_args,
    tokenizer=tokenizer,
    dataset_text_field="text",
    max_seq_length=2048,
    packing=True,          # pack multiple short examples into one sequence
)

print("Starting SFT training...")
trainer.train()

print(f"Saving to {OUT_DIR}")
trainer.save_model(OUT_DIR)
tokenizer.save_pretrained(OUT_DIR)
print("Done.")
