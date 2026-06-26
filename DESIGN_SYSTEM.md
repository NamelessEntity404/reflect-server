# Shane Graffiti Inc. — Complete Design System & Hard Rules
Last updated: 2026-06-26

---

## THE SITE

**Single URL for everything:** https://reflect-server-production.up.railway.app

| Page | URL | Background Video |
|------|-----|-----------------|
| Home | / | bg-home.mp4 |
| Work | /work.html | bg-work.mp4 |
| Research | /research.html | bg-research.mp4 |
| About | /about.html | bg-about.mp4 |
| Perspective Chat | /therapy-chat.html?admin=reflect2024 | bg-reflect.mp4 |
| Bio | /bio.html | bg-bio.mp4 |
| Stack | /stack.html | bg-stack.mp4 |
| Why This Matters | /why-this-matters.html | bg-why.mp4 |
| Building Perspective | /reflect-build.html | bg-build.mp4 |
| Training Corpus | /reflect-training.html | bg-training.mp4 |
| Adversarial Research | /adversarial-research.html | bg-r1.mp4 |
| Dialogue SWEBench | /dialogue-swebench.html | bg-r2.mp4 |
| DLawBench | /dlawbench.html | bg-p16.mp4 |
| EM-NeSy | /em-nesy.html | bg-r4.mp4 |
| Frameworks | /frameworks.html | bg-p13.mp4 |
| GenAI Industrial CV | /genai-industrial-cv.html | bg-p8.mp4 |
| Moral Indifference | /moral-indifference.html | bg-p14.mp4 |
| Smart Glasses | /smart-glasses.html | bg-p9.mp4 |
| Why AI Doesn't Learn | /why-ai-doesnt-learn.html | bg-r3.mp4 |
| Work pages | /page2.html through /page16.html | bg-p2.mp4 through bg-p16.mp4 |

---

## HARD RULES — NEVER VIOLATE THESE

### Background Videos
1. **Every page has a DIFFERENT background video** — no duplicates within any section
2. **#bg-video and video elements are NEVER touched by glass.css or any card CSS**
3. **Body and HTML backgrounds are NEVER touched by glass.css**
4. **Cards and videos NEVER affect each other's CSS**
5. **Video opacity stays at 0.3–0.4** — set in inline style on the video element
6. **HTML always has `background: #000 !important`** — prevents white browser background showing through
7. **Body always has `background: transparent`** — so video shows through

### Work Pages (SACRED — DO NOT TOUCH)
8. **page2.html through page16.html and work.html** — WebGL scroll animation is the entire point
9. **NEVER change the canvas, JS, or scroll animation on work pages**
10. **NEVER apply glass.css to `.work-card`** — those are thumbnail containers, not glass cards
11. **Work page frames live at /app/_frames/ on Railway volume** — 4500 JPEG files

### Perspective Chat (SACRED — DO NOT TOUCH)
12. **therapy-chat.html** — sci-fi tunnel bg, frosted glass message cards, Tinder Z-stack
13. **NEVER overwrite therapy-chat.html with the old website version** — it lives in reflect-server repo only
14. **Admin bypass:** `?admin=reflect2024` — unlimited messages for Shane

### Laser Grid (DEAD — NEVER RESURRECT)
15. **koi.js WebGL laser grid is DISABLED** — 1 line only, never re-enable
16. **Never add `id="gl"` canvas to master pages** — that's what made the laser grid
17. **Never re-enable WebGL on master pages** — videos replace all WebGL backgrounds

---

## GLASS CARD SYSTEM (glass.css)

All cards across all pages use the same glass rules from `/glass.css`.
This file is linked in every HTML page's `<head>`.

**The glass applies to these selectors:**
- `.about-card` (about page)
- `.paper-card` (research pages)
- `.card-shell` (subpages)
- `.pipe-step`, `.guardrail` (training/build pages)
- `.v-step`, `.key-metric`, `.finding` (research subpages)
- `.method-card`, `.eval-card`, `.result-card`, `.benchmark-card`

**Glass properties:**
- Background: `linear-gradient(158deg, rgba(28,30,25,0.58) 0%, rgba(12,13,10,0.65) 50%, rgba(22,24,19,0.60) 100%)`
- Blur: `backdrop-filter: blur(24px) saturate(160%)` — MAX 24px to prevent GPU overload
- Border: `0.5px solid rgba(255,255,255,0.14)`
- Border radius: `18px`
- Box shadow: outer depth + inner top highlight + inner bottom shadow
- `::before` specular sheen: diagonal light reflection across the glass

**Glass NEVER applies to:**
- `.work-card` — thumbnail containers
- `#bg-video`, `video` — background videos
- `body`, `html` — structural elements
- `section`, `div`, `main`, `nav` — layout elements

**To edit glass globally:** only edit `/Users/nicoleackerman/Desktop/reflect-server/glass.css`

---

## HOW TO DEPLOY

```bash
cd /Users/nicoleackerman/Desktop/reflect-server
railway up --service reflect-server
```

## HOW TO BACK UP (GitHub)

```bash
cd /Users/nicoleackerman/Desktop/reflect-server
git add -A && git commit -m "description" && git push origin main
```

---

## BACKGROUND VIDEO RULES

### Source videos live at:
`/Users/nicoleackerman/Desktop/website/_BACKGROUND VIDEOS/`

### Compressed videos live at:
`/Users/nicoleackerman/Desktop/reflect-server/bg-*.mp4`

### How to add a new video:
```bash
ffmpeg -i "source.mov" \
  -vf "scale=1280:-2,format=yuv420p" \
  -c:v libx264 -crf 26 -preset fast \
  -an -movflags +faststart \
  /Users/nicoleackerman/Desktop/reflect-server/bg-NEWNAME.mp4 -y
```
Then add to the HTML:
```html
<video id="bg-video" autoplay muted loop playsinline preload="auto"
  style="position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;object-fit:cover;opacity:0.3;pointer-events:none;">
  <source src="bg-NEWNAME.mp4?v=3" type="video/mp4">
</video>
```
And `html { background: #000 !important; }` and `body { background: transparent; }`.

---

## IF WORK PAGE FRAMES GO MISSING

The 4500 frame JPEGs live on Railway volume at `/app/_frames/`. If they go missing after a Railway crash, run:

```python
import os, requests, concurrent.futures
BASE = "https://reflect-server-production.up.railway.app"
TOKEN = "reflect2024"
FRAMES = "/Users/nicoleackerman/Desktop/website/_frames"
missing = []
for page in os.listdir(FRAMES):
    pd = os.path.join(FRAMES, page)
    if not os.path.isdir(pd): continue
    for f in os.listdir(pd):
        if not f.endswith('.jpg'): continue
        rel = page+'/'+f
        r = requests.head(f"{BASE}/_frames/{rel}", timeout=5)
        if r.status_code != 200:
            missing.append((rel, os.path.join(pd,f)))
def up(item):
    rel,fp = item
    data = open(fp,'rb').read()
    r = requests.post(f"{BASE}/admin/upload-frame?token={TOKEN}&path={rel}",
        data=data, headers={'Content-Type':'application/octet-stream'}, timeout=30)
    return r.status_code
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
    list(ex.map(up, missing))
print("done")
```

---

## KAGGLE TRAINING (run when GPU quota resets)

- Dataset: `baddatalogin/reflect-personal-training` (ready and uploaded)
- Notebook: `notebookb2bd03cb1d`
- Steps: Edit → **Save Version → Save & Run All** → GPU T4 x2, Internet ON
- 44 HuggingFace datasets in notebook cell-3, personal corpus weighted 3x
- After training: model pushes to HuggingFace automatically
- Then: Railway Variables → add `REFLECT_MODEL_REPO` → Perspective switches from Claude to trained model

---

## CONVERSATION LOGGING

Every Perspective chat conversation is logged to Railway:
- Full logs: `https://reflect-server-production.up.railway.app/admin/logs?token=reflect2024`
- Stats: `https://reflect-server-production.up.railway.app/admin/stats?token=reflect2024`
- Device fingerprint, scroll depth, dwell time, canvas fingerprint, GPU info all captured

---

## ACCOUNTS

| Service | Account |
|---------|---------|
| Railway | alksmg88 |
| GitHub | alksmg88 |
| Kaggle | baddatalogin |
| GitHub (server) | alksmg88/reflect-server |
| GitHub (website) | alksmg88/website |

---

## DESIGN BRAND COLORS

```css
--ink:   #F5F2E8  /* warm white — text */
--paper: #05060a  /* near black — base */
--acid:  #C8F000  /* yellow-green — accent */
--mid:   #A8A89A  /* warm gray — secondary text */
--rule:  rgba(200,240,0,0.12)  /* acid at 12% — dividers */
--mono:  'JetBrains Mono', monospace
```

## TYPOGRAPHY

- Display/Headers: Barlow Condensed, weight 900, uppercase
- Body: Inter
- Code/Labels: JetBrains Mono, 9-11px, letter-spacing 0.12-0.2em, uppercase

---

## WHAT KILLED WHAT (learn from history)

| What broke | What caused it | Never do this |
|------------|----------------|---------------|
| Laser grid everywhere | koi.js WebGL injected on all pages | Never re-enable koi.js |
| White overlay everywhere | `html, body { background: transparent }` made html transparent | Always set `html { background: #000 !important }` |
| Work page white | glass.css targeted `.work-card` with backdrop-filter | Never apply glass to .work-card |
| therapy-chat.html wiped | `cp /website/*.html /reflect-server/` overwrote it | NEVER mass-copy HTML files |
| Video stutter | 48px backdrop-filter blur on too many elements = GPU overload | Max 24px blur |
| Same video on all research pages | All subpages got `bg-research.mp4` when injected | Each subpage MUST have unique video |
| Frames lost on Railway | Railway volume ephemeral without proper mount | Use upload script if frames go missing |
| Railway 500 on push | 350MB+ in railway up CLI | Never commit large files, use HTTP upload endpoint |
