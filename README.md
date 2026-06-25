# Second Brain — Local Setup

## Run locally in 60 seconds

**Requirements:** Node.js (any recent version). No npm install needed — zero dependencies.

### 1. Set your API key

Mac/Linux:
```
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Windows (Command Prompt):
```
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Start the server

```
node server.js
```

### 3. Open it

Go to http://localhost:3000 in your browser.

---

## Deploy to Railway (free)

1. Push this folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub
3. Add environment variable: `ANTHROPIC_API_KEY` = your key
4. Done — Railway gives you a live URL

Same exact code, no changes needed.

---

## Customizing the system prompt

Open `index.html` and find the `SYSTEM_PROMPT` constant near the bottom in the `<script>` block. Edit it however you want.
