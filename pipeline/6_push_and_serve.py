"""
Step 6: Push the trained model to HuggingFace Hub and update the
Railway server to serve it via HF Inference API.

Run after step 5:
  HF_TOKEN=hf_xxx HF_REPO=yourusername/reflect-llama3 python pipeline/6_push_and_serve.py

Then set REFLECT_MODEL_REPO env var on Railway to your repo name.
"""

import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

HF_TOKEN  = os.environ.get("HF_TOKEN", "")
HF_REPO   = os.environ.get("HF_REPO", "")   # e.g. "shanegraffiti/reflect-llama3"
DPO_DIR   = "./reflect-llama3-dpo"
BASE_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"

if not HF_TOKEN or not HF_REPO:
    raise SystemExit("Set HF_TOKEN and HF_REPO env vars before running.")

print(f"Merging LoRA weights into base model...")
tokenizer = AutoTokenizer.from_pretrained(DPO_DIR)
base = AutoModelForCausalLM.from_pretrained(BASE_MODEL, token=HF_TOKEN, device_map="cpu")
model = PeftModel.from_pretrained(base, DPO_DIR)
model = model.merge_and_unload()

print(f"Pushing to HuggingFace Hub: {HF_REPO}")
model.push_to_hub(HF_REPO, token=HF_TOKEN, private=True)
tokenizer.push_to_hub(HF_REPO, token=HF_TOKEN, private=True)

print(f"""
Done. Your model is at: https://huggingface.co/{HF_REPO}

Next steps:
1. On Railway, add these env vars:
     HF_TOKEN={HF_TOKEN[:8]}...
     REFLECT_MODEL_REPO={HF_REPO}

2. The server will automatically switch from Claude to your model
   when REFLECT_MODEL_REPO is set.

3. Or enable HuggingFace Inference Endpoints for the repo for
   dedicated GPU serving.
""")
