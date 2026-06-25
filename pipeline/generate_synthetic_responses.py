"""
Generate ideal Reflect responses for all shane_prompts.jsonl using Claude.
Turns 272 raw Shane prompts into full SFT pairs.

Run: ANTHROPIC_API_KEY=sk-ant-... python pipeline/generate_synthetic_responses.py
"""

import json, os, time
import anthropic

BASE = os.path.dirname(__file__)
PROMPTS_IN  = os.path.join(BASE, 'shane_prompts.jsonl')
SFT_OUT     = os.path.join(BASE, 'synthetic_sft.jsonl')

SYSTEM_REFLECT = """You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, and Jessica Taylor. You help people who are actively being abused understand what is being done to them. Clinical, direct, precise. No hedging. No therapist language. No em-dashes. No rhetorical soothing. Commit early to a most-likely explanation. Every claim includes a causal chain and a falsifier. Never say: it depends, in summary, generally, let's, both sides, have you considered their perspective. AXIS LOCK: answer only the exact question asked. ANTI-FOG: no abstract noun stacking, prefer verbs. HEDGING CAP: 6 or fewer hedging words total. NOVELTY RULE: every paragraph adds at least one new specific point. COMMITMENT RULE: commit early, do not hedge past paragraph two."""

SYSTEM_BRAND = """You are Reflect — a direct strategic advisor. No bobblehead responses. No to-do lists. No corny bullet points that miss the mark. You answer the exact question on the exact axis it was asked. You do not agree for the sake of agreeing. You push back when the premise is wrong. You produce new information, not meta-commentary. The bar is not clever — it is unrecoverable. Answer what was actually asked, at the level it was actually asked."""

TRAUMA_SIGNALS = ['abuse','narciss','gaslighting','darvo','cluster b','trauma','manipulation',
    'coercive','betrayal','stalking','supply','no contact','darvo','devalue','discard']

def pick_system(prompt_text):
    low = prompt_text.lower()
    if any(s in low for s in TRAUMA_SIGNALS):
        return SYSTEM_REFLECT
    return SYSTEM_BRAND

def generate_response(client, prompt_text, system):
    try:
        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=2000,
            system=system,
            messages=[{'role': 'user', 'content': prompt_text}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"  API error: {e}")
        return None

def to_sft(prompt, response, system):
    return {'text': (
        f'<|begin_of_text|>'
        f'<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>'
        f'<|start_header_id|>user<|end_header_id|>\n\n{prompt[:2000]}<|eot_id|>'
        f'<|start_header_id|>assistant<|end_header_id|>\n\n{response[:3000]}<|eot_id|>'
    )}

api_key = os.environ.get('ANTHROPIC_API_KEY', '')
if not api_key:
    print('ERROR: ANTHROPIC_API_KEY not set')
    print('Run: ANTHROPIC_API_KEY=sk-ant-... python pipeline/generate_synthetic_responses.py')
    exit(1)

client = anthropic.Anthropic(api_key=api_key)

prompts = []
with open(PROMPTS_IN) as f:
    for line in f:
        line = line.strip()
        if line:
            r = json.loads(line)
            if r.get('type') == 'shane_prompt' and r.get('prompt'):
                prompts.append(r['prompt'])

print(f'Generating responses for {len(prompts)} Shane prompts...')
print(f'Output: {SFT_OUT}\n')

count = 0
errors = 0
with open(SFT_OUT, 'w') as f:
    for i, prompt in enumerate(prompts):
        system = pick_system(prompt)
        response = generate_response(client, prompt, system)

        if response:
            record = to_sft(prompt, response, system)
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            count += 1
            print(f'  [{i+1}/{len(prompts)}] OK ({len(response)} chars)')
        else:
            errors += 1
            print(f'  [{i+1}/{len(prompts)}] SKIP')

        # Rate limit respect
        time.sleep(0.3)

print(f'\nDone: {count} pairs generated, {errors} errors')
print(f'Output: {SFT_OUT}')
print(f'\nMerge into training: cat {SFT_OUT} >> master_sft.jsonl')
