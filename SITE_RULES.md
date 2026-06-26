# Shane Graffiti Inc. — Site Rules & Architecture

## LIVE URL
Everything lives at one place: **https://reflect-server-production.up.railway.app**

| Page | URL |
|------|-----|
| Home | / |
| Work | /work.html |
| Research | /research.html |
| About | /about.html |
| Perspective Chat | /therapy-chat.html?admin=reflect2024 |
| Admin logs | /admin/logs?token=reflect2024 |
| Admin stats | /admin/stats?token=reflect2024 |

---

## SACRED — NEVER TOUCH THESE

### Work pages (page2-page16 + work.html)
- These have **WebGL scroll animation** — scroll plays a movie frame by frame
- 300 frames per video, loaded as ImageBitmap in GPU memory via scroll-player.js
- **DO NOT** touch the canvas, WebGL, or JS on any of these pages
- **DO NOT** change their background videos
- Frames live on Railway volume at /app/_frames/ (4500 files)

### Perspective Chat (therapy-chat.html)
- Sci-fi tunnel background (bg-reflect.mp4)
- Frosted glass cards (YOU = white, PERSPECTIVE = dark)
- Video pauses only when typing
- Admin bypass via ?admin=reflect2024
- **DO NOT** overwrite with old website version

---

## BACKGROUND VIDEO RULES

### The Rule
Every page has a **different** background video. No repeats within any section.

### Assignments

#### Master Pages
| Page | Video | Source |
|------|-------|--------|
| index.html | bg-home.mp4 | futuristic sci-fi tunnel motion |
| work.html | bg-work.mp4 | sci-fi game level environment ← SACRED |
| about.html | bg-about.mp4 | gangway futuristic building |
| research.html | bg-research.mp4 | 4k cyberpunk tunnel |
| therapy-chat.html | bg-reflect.mp4 | sci-fi tunnel loop ← SACRED |

#### About Section
| Page | Video | Source |
|------|-------|--------|
| bio.html | bg-bio.mp4 | neon lights sci-fi city |
| stack.html | bg-stack.mp4 | cyberpunk neon tunnel |
| why-this-matters.html | bg-why.mp4 | colorful nebula star field |
| reflect-build.html | bg-build.mp4 | dark crystal tunnel |
| reflect-training.html | bg-training.mp4 | glowing pathway tunnel |

#### Research Section (ALL DIFFERENT)
| Page | Video | Source |
|------|-------|--------|
| adversarial-research.html | bg-r1.mp4 | 4k fake shooter/racing |
| dialogue-swebench.html | bg-r2.mp4 | Underwater-2 |
| dlawbench.html | bg-r3.mp4 | flying through clouds |
| em-nesy.html | bg-r4.mp4 | underwater |
| frameworks.html | bg-p3.mp4 | scifi spaceship corridor |
| genai-industrial-cv.html | bg-p4.mp4 | futuristic tech tunnel |
| moral-indifference.html | bg-p5.mp4 | scifi outer space neon |
| smart-glasses.html | bg-p6.mp4 | dynamic neon tunnel loop |
| why-ai-doesnt-learn.html | bg-p7.mp4 | sci-fi tunnel loop |

#### Work Subpages (SACRED — WebGL scroll)
page2=bg-p2, page3=bg-p3, page4=bg-p4, page5=bg-p5, page6=bg-p6, page7=bg-p7,
page8=bg-p8, page9=bg-p9, page10=bg-p10, page11=bg-p11, page12=bg-p12,
page13=bg-p13, page14=bg-p14, page15=bg-p15, page16=bg-p16

---

## HOW TO ADD A NEW BACKGROUND VIDEO

1. Drop source video into `/Users/nicoleackerman/Desktop/website/_BACKGROUND VIDEOS/`
2. Run compress script:
```bash
ffmpeg -i "input.mov" -vf "scale=1280:-2,format=yuv420p" \
  -c:v libx264 -crf 26 -preset fast -an -movflags +faststart \
  /Users/nicoleackerman/Desktop/reflect-server/bg-NAME.mp4 -y
```
3. Add to HTML file after `<body>`:
```html
<video id="bg-video" autoplay muted loop playsinline preload="auto"
  style="position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;object-fit:cover;opacity:0.3;pointer-events:none;">
  <source src="bg-NAME.mp4" type="video/mp4">
</video>
```
4. Make sure body has `background: transparent` in CSS
5. Deploy: `cd /Users/nicoleackerman/Desktop/reflect-server && railway up --service reflect-server`

---

## THINGS THAT WILL BREAK EVERYTHING (DO NOT DO)

| ❌ Never Do This | Why |
|-----------------|-----|
| `cp /Users/nicoleackerman/Desktop/website/*.html /Users/nicoleackerman/Desktop/reflect-server/` | Overwrites therapy-chat.html with old version |
| Touch koi.js WebGL code | Laser grid comes back. It's dead. Keep it dead. |
| Add `id="gl"` canvas to master pages | Laser grid |
| Touch page2-page16 HTML or their WebGL | Breaks work scroll animation |
| Commit 350MB+ to git for railway up | Fails: payload too large |
| Use Git LFS with railway up CLI | LFS pointers upload, not actual files |
| Change `alpha:false` to `alpha:true` in WebGL contexts | Breaks rendering |

---

## HOW TO DEPLOY

```bash
cd /Users/nicoleackerman/Desktop/reflect-server
railway up --service reflect-server
```

## HOW TO PUSH TO GITHUB (BACKUP)

```bash
cd /Users/nicoleackerman/Desktop/reflect-server
git add -A && git commit -m "your message" && git push origin main

cd /Users/nicoleackerman/Desktop/website
git add *.html *.js *.css && git commit -m "your message" && git push origin fresh-main:main
```

---

## IF WORK PAGE FRAMES GO MISSING (Railway volume wipe)

Run this Python script to re-upload all frames:
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
print(f"{len(missing)} missing")
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

## KAGGLE TRAINING (when GPU quota resets daily)

1. Go to kaggle.com → notebook `notebookb2bd03cb1d`
2. Edit → Save Version → **Save & Run All**
3. Settings: GPU T4 x2, Internet ON
4. Dataset attached: `baddatalogin/reflect-personal-training`
5. After it finishes: model pushes to HuggingFace automatically
6. Then set `REFLECT_MODEL_REPO` in Railway Variables

---

## KEY ACCOUNTS

- Railway: alksmg88
- GitHub: alksmg88
- Kaggle: baddatalogin
- GitHub repos: alksmg88/reflect-server, alksmg88/website
- Railway URL: reflect-server-production.up.railway.app
