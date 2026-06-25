"""
Window size variation — extract 3-turn and 8-turn conversation windows
from all dialogue files. Supplements the 5-turn windows from build_dataset.py.
Produces: windows_3turn_sft.jsonl, windows_8turn_sft.jsonl
"""
import json, os, re
import pdfplumber

AI_DIR  = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA'
AI_DIR2 = '/Volumes/8TB SG/Downloads/Master AE SG Folder/______AI TRAINING DATA/2024-2025 PDFS'
BASE    = os.path.dirname(__file__)
OUT_3   = os.path.join(BASE, 'windows_3turn_sft.jsonl')
OUT_8   = os.path.join(BASE, 'windows_8turn_sft.jsonl')

SYSTEM_REFLECT = """You are Reflect — a trauma-informed analysis tool. Clinical, direct, precise. No hedging. No therapist language. Commit early. Every claim includes a causal chain and a falsifier."""

TURN_RE = re.compile(r'(You said\s*:\s*\n|ChatGPT said\s*:\s*\n|Claude said\s*:\s*\n|Claude responded\s*:\s*\n|Assistant\s*:\s*\n|Human\s*:\s*\n)', re.I)

HEDGE = ["it sounds like","it seems like","both of you","have you considered","it depends",
         "in summary","generally","i hear you","great question","thank you for sharing",
         "mental health professional","i'm not able to diagnose"]

def count_hedges(text):
    low = text.lower()
    return sum(1 for p in HEDGE if p in low)

def parse_turns(text):
    parts = TURN_RE.split(text)
    turns = []
    for i in range(1, len(parts)-1, 2):
        marker  = parts[i].lower()
        content = parts[i+1].strip() if i+1 < len(parts) else ''
        if len(content) < 15: continue
        is_user = any(m in marker for m in ['you said','human','user'])
        turns.append(('user' if is_user else 'assistant', content))
    return turns

def build_windows(turns, window, stride):
    windows = []
    for i in range(0, len(turns)-1, stride):
        end = min(i + window, len(turns))
        while end > i and turns[end-1][0] != 'assistant':
            end -= 1
        if end <= i + 1: continue
        w = turns[i:end]
        if w[0][0] != 'user': continue
        if w[-1][0] != 'assistant': continue
        last_ai = w[-1][1]
        if count_hedges(last_ai) >= 4: continue
        if len(last_ai) < 80: continue
        windows.append(w)
    return windows

def format_window(turns, system):
    text = f'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>'
    for role, content in turns:
        text += f'<|start_header_id|>{role}<|end_header_id|>\n\n{content[:3000]}<|eot_id|>'
    return {'text': text}

print('=== Window Size Variation Extraction ===\n')

seen_3 = set()
seen_8 = set()
count_3 = 0
count_8 = 0

with open(OUT_3, 'w') as f3, open(OUT_8, 'w') as f8:
    for d in [AI_DIR, AI_DIR2]:
        for fname in sorted(os.listdir(d)):
            if not fname.endswith('.pdf'): continue
            path = os.path.join(d, fname)
            full_text = ''
            try:
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: full_text += '\n' + t
            except: continue

            turns = parse_turns(full_text)
            if len(turns) < 3: continue

            # 3-turn windows (tight, specific)
            for w in build_windows(turns, window=3, stride=1):
                key = w[-1][1][-100:]
                if key not in seen_3:
                    seen_3.add(key)
                    r = format_window(w, SYSTEM_REFLECT)
                    f3.write(json.dumps(r, ensure_ascii=False) + '\n')
                    count_3 += 1

            # 8-turn windows (rich context)
            for w in build_windows(turns, window=8, stride=3):
                key = w[-1][1][-100:]
                if key not in seen_8:
                    seen_8.add(key)
                    r = format_window(w, SYSTEM_REFLECT)
                    f8.write(json.dumps(r, ensure_ascii=False) + '\n')
                    count_8 += 1

            total = len([w for w in build_windows(turns, 3, 1)]) + len([w for w in build_windows(turns, 8, 3)])
            if total > 0:
                print(f"  {fname[:60]}: {count_3} 3-turn / {count_8} 8-turn cumulative")

print(f'\n3-turn windows: {count_3:,} -> {OUT_3}')
print(f'8-turn windows: {count_8:,} -> {OUT_8}')
