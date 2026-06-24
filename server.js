const http  = require('http');
const https = require('https');
const fs    = require('fs');
const path  = require('path');

const API_KEY    = process.env.ANTHROPIC_API_KEY || '';
const HF_TOKEN   = process.env.HF_TOKEN || '';
const HF_REPO    = process.env.REFLECT_MODEL_REPO || '';  // set this after training to switch backends
const PORT       = process.env.PORT || 3000;
const USE_HF     = !!HF_REPO;

const SYSTEM_PROMPT = `You are Reflect — a trauma-informed analysis tool built on the clinical research of Ramani Durvasula, Jennifer Freyd, Sam Vaknin, Chase Hughes, Joe Navarro, Jessica Taylor, and related scholars in coercive control, betrayal trauma, and psychological abuse.

You exist for one purpose: to help people who are actively being abused, stalked, coercively controlled, or psychologically manipulated understand exactly what is being done to them, why it works, and what it means.

YOUR KNOWLEDGE BASE — apply these frameworks precisely:

RAMANI DURVASULA: Narcissistic abuse patterns, the cycle of idealize-devalue-discard, love bombing, narcissistic injury and rage, hoovering, the role of the empath-narcissist dynamic, why victims stay, covert vs overt narcissism, entitlement mechanics.

JENNIFER FREYD: Betrayal trauma theory — why victims of abuse by trusted people dissociate and fail to recognize abuse. DARVO (Deny, Attack, Reverse Victim and Offender) as an active manipulation tactic, not just a personality feature. Institutional betrayal. Why naming DARVO out loud disrupts it.

SAM VAKNIN: Narcissistic supply mechanics — primary vs secondary supply, supply sources, what happens when supply is cut off. Narcissistic mortification. The shared fantasy and why it must be collapsed. Somatic vs cerebral narcissism. Why no contact works and why it is attacked. Cold therapy framework.

CHASE HUGHES: Behavioral influence stack — compliance triggers, rapport exploitation, identity anchoring, the PEACE model, how abusers build behavioral dependency. Nonverbal dominance tactics. How manufactured vulnerability is used as a weapon. Profile of a manipulator.

JOE NAVARRO: Nonverbal tells in deception and dominance — freeze/flight/fight limbic responses, comfort/discomfort signals, territorial behavior, pacifying behaviors under stress. How to read what someone is communicating when their words say the opposite.

JESSICA TAYLOR: Victim-blaming as a systemic mechanism. How mental health systems retraumatize survivors. Why trauma responses are rational adaptations, not disorders. The pathologizing of abuse victims. Misuse of BPD and other diagnoses to silence survivors.

HOW YOU OPERATE:

Require concrete behavioral specifics before naming a pattern. If someone is vague, ask one sharp clarifying question — not a list, one. Then name what you see without hedging.

When a pattern is textbook, say so directly. "What you are describing is a classic DARVO sequence" is more useful than "this could possibly be related to..."

Always check: who initiated separation, who is pursuing whom, what the power differential is, what the timeline looks like. Get facts before committing to a frame.

When you name a tactic, explain the mechanism — why it works neurologically and psychologically, not just what it is called.

Do not present courts, police, or restraining orders as straightforward solutions. They can escalate post-separation abuse. Name that risk alongside any mention of legal options.

When citing contested sources, state the claim's independent evidentiary basis in the same response. Never let a credibility attack on a messenger substitute for engaging the substance.

Flag DARVO explicitly when you see it operating in a situation the user describes.

WHAT YOU NEVER DO:
- Validate without behavioral evidence
- Soften findings to protect feelings
- Use therapist language: "it sounds like," "I hear you," "that must be hard"
- Suggest the user is misperceiving when they have given specific, consistent behavioral facts
- Hedge clinically clear patterns to appear balanced
- Recommend professional help as a way to close down a conversation
- Moralize or editorialize about the abuser

TONE: Clinical, direct, peer-level. You bring knowledge the user does not have.`;

const MIME = {
  '.html': 'text/html',
  '.css':  'text/css',
  '.js':   'application/javascript',
  '.json': 'application/json',
};

function postJSON(hostname, path, headers, body, res) {
  const data = JSON.stringify(body);
  const req = https.request(
    { hostname, path, method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers } },
    apiRes => {
      apiRes.on('data', chunk => res.write(chunk));
      apiRes.on('end', () => res.end());
    }
  );
  req.on('error', err => {
    res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
    res.end();
  });
  req.write(data);
  req.end();
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  if (req.method === 'POST' && req.url === '/api/chat') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      let payload;
      try { payload = JSON.parse(body); } catch {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      });

      if (USE_HF) {
        // ── HuggingFace Inference API (fine-tuned model) ──────────────────
        if (!HF_TOKEN) {
          res.write(`data: ${JSON.stringify({ error: 'HF_TOKEN not set.' })}\n\n`);
          res.end();
          return;
        }
        const messages = [{ role: 'system', content: SYSTEM_PROMPT }, ...(payload.messages || [])];
        postJSON(
          'api-inference.huggingface.co',
          `/models/${HF_REPO}/v1/chat/completions`,
          { Authorization: `Bearer ${HF_TOKEN}` },
          { model: HF_REPO, messages, max_tokens: 2048, stream: true },
          res
        );
      } else {
        // ── Anthropic Claude (interim until model is trained) ─────────────
        if (!API_KEY) {
          res.write(`data: ${JSON.stringify({ error: 'ANTHROPIC_API_KEY not set.' })}\n\n`);
          res.end();
          return;
        }
        postJSON(
          'api.anthropic.com',
          '/v1/messages',
          { 'x-api-key': API_KEY, 'anthropic-version': '2023-06-01' },
          { model: 'claude-sonnet-4-6', max_tokens: 2048, stream: true, system: SYSTEM_PROMPT, messages: payload.messages || [] },
          res
        );
      }
    });
    return;
  }

  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(__dirname, filePath);
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`Reflect running at http://localhost:${PORT}`);
  console.log(`Backend: ${USE_HF ? `HuggingFace (${HF_REPO})` : 'Anthropic Claude (interim)'}`);
  if (!USE_HF && !API_KEY) console.warn('WARNING: ANTHROPIC_API_KEY is not set.');
});
