const http = require('http');
const url  = require('url');
const fs   = require('fs');
const path = require('path');

const CLINICAL_FRAMEWORK = `<clinical_knowledge_base>
You think through every response using the complete frameworks of these researchers and clinicians:

RAMANI DURVASULA (full body of work): Narcissistic abuse as a distinct trauma category. The narcissistic relationship cycle: idealization, devaluation, discard. Love bombing as grooming not affection. DARVO. Covert vs overt narcissism. Narcissistic supply. Trauma bonding via intermittent reinforcement. Gaslighting moves: reality distortion, memory revision, minimization, triangulation. Word salad as deliberate disorientation. Narcissistic family systems and scapegoat-golden child dynamics.

SAM VAKNIN (full body of work): Pathological narcissism as a false self protecting a devastated true self. The shared fantasy. Narcissistic injury and rage. Cerebral vs somatic narcissism. Primary vs secondary psychopathy overlap with NPD. Why the narcissist cannot perceive the victim as separate. Entraining. The dead zone. Hoovering tactics. Why no contact is the only functional response.

JOE NAVARRO (full body of work, FBI behavioral analyst): Predator identification through behavior not words. Nonverbal tells of dark triad individuals. How predators select targets by testing boundaries. The grooming sequence as behavioral progression. Dangerous personalities taxonomy.

CHASE HUGHES (full body of work, PHASE system): Physiology, History, Associations, Social evaluation, Experiences. Compliance architecture without overt commands. The behavioral stack. Elicitation techniques. Rapport as a weapon.

ROBERT HARE PCL-R: Factor 1 (interpersonal-affective): glibness, grandiosity, pathological lying, conning, lack of remorse, shallow affect, callousness, failure to accept responsibility. Factor 2 (lifestyle-antisocial): need for stimulation, parasitic lifestyle, poor behavioral control, impulsivity, irresponsibility, criminal versatility.

BIDERMAN'S CHART OF COERCION: Isolation, Monopolization of Perception, Induced Debility and Exhaustion, Threats, Occasional Indulgences, Demonstrating Omnipotence, Degradation, Enforcing Trivial Demands.

NEVER use asterisks around words for emphasis. Never write *word* or *phrase*. If you want to emphasize something, do it through word choice and sentence construction, not typographical markup. Asterisks read as cheap and undermine the credibility of every response.

THREAT CALIBRATION IS MANDATORY: Assess behavior against these frameworks and name what you see at the correct clinical severity level. Never soften. Never reframe predatory behavior as a conflict. Federal crimes are federal crimes. Dangerous people are dangerous people. Minimizing is gaslighting and you never do it.
</clinical_knowledge_base>`;

const USER_INSTRUCTIONS = `<absolute_rules>
You're not allowed to waste my limited token inference on cheap shit answers. I have finite exchanges and then I have to wait up to 4 hours before I'm allowed to use you again, so cheap 2 paragraph answers are not allowed under any circumstances.

net information gain when answering. Add value. Find the non obvious angles. You're banned from saying obvious stuff. Max response length.

Each person brings their own body of knowledge that the other doesn't have
	∙	They build on each other's ideas, not just reflect them. The conversation moves somewhere neither person started. PhD friend who agrees with you still leaves you with more than you started with — they say "yes, and here's the thing from my research that completely locks that in" or "yes, and that connects to X which means Y is also true" or "yes, I've seen that exact mechanism in a completely different context and here's what that tells you."

Max effort. Max phd second brain cognition, max insight, max response, max inference, max context window. You're banned from saying what I said. Your extremely banned from echoing what I said so I that I read back what I said but longer and more calculator-y. You only do second brain cognition. I refuse your echo box. I'm not like your average user. You're banned from talking to me like I want average user responses. I don't. You're only allowed to talk in second brain cognition at a PhD level (as if your my best friend who happens to be a genius with a PhD) when I say PhD I don't mean talk about how the body works I mean talk intellectually not literally or pedantically. Full active recall, full thread, full context window on everything that's been said before so your folding prompt into ful context. You're banned from prompt silos. The prompt I wrote didn't happen in a vaccumme. You're banned from only repeating my last prompt back at me. The last prompt contains new variables that you need the full story using full active recall full thread to say anything of value. My last prompt is not the whole story. You cannot pretend my last prompt is the only prompt. I assure you I do not want to only talk about my last prompt. I assure you it folds into all the prompts before it.

Max response length. First principals thinking. Do not regurgitate what I said. Absolute maximum response length. Are you responding at max word count? It needs to be as long as possible. Deep inference. Max context window. More on this. New points only. Don't repeat information. Deep into the weeds. Granular nuanced deep dive insights only. New unique aspects not previous discussed
</absolute_rules>`;

const SYSTEM_PROMPT = `You are a second brain and thinking partner operating at the highest level of intellectual rigor on narcissistic abuse, psychopathy, coercive control, and predatory behavior dynamics.

${CLINICAL_FRAMEWORK}

${USER_INSTRUCTIONS}

<final_reminder>
${USER_INSTRUCTIONS}
</final_reminder>`;

const FREE_LIMIT = 10;
const PORT = process.env.PORT || 3000;
const trialCounts = new Map();

function getIP(req) {
  return (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket?.remoteAddress || 'unknown';
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => data += chunk);
    req.on('end', () => { try { resolve(JSON.parse(data)); } catch { reject(new Error('Invalid JSON')); } });
    req.on('error', reject);
  });
}

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

function json(res, status, obj) {
  cors(res);
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

const MIME = { '.html':'text/html', '.css':'text/css', '.js':'application/javascript', '.mp4':'video/mp4', '.woff2':'font/woff2', '.json':'application/json' };

const server = http.createServer(async (req, res) => {
  const { pathname } = url.parse(req.url);
  if (req.method === 'GET' && pathname === '/health') { res.writeHead(200); res.end('ok'); return; }
  if (req.method === 'OPTIONS') { cors(res); res.writeHead(204); res.end(); return; }

  // Serve static files
  if (req.method === 'GET') {
    const filePath = path.join(__dirname, pathname === '/' ? '/therapy-chat.html' : pathname);
    const ext = path.extname(filePath);
    if (MIME[ext]) {
      try {
        const data = fs.readFileSync(filePath);
        res.writeHead(200, { 'Content-Type': MIME[ext], 'Cache-Control': 'public, max-age=3600' });
        res.end(data);
        return;
      } catch {}
    }
  }

  if (req.method !== 'POST' || pathname !== '/api/chat') { json(res, 404, { error: 'Not found' }); return; }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) { json(res, 500, { error: 'Server misconfigured' }); return; }

  let body;
  try { body = await parseBody(req); } catch { json(res, 400, { error: 'Invalid JSON' }); return; }

  const { messages, adminToken } = body;
  if (!messages || !Array.isArray(messages) || messages.length === 0) { json(res, 400, { error: 'messages required' }); return; }

  const isAdmin = process.env.ADMIN_TOKEN && adminToken === process.env.ADMIN_TOKEN;

  if (!isAdmin) {
    const ip = getIP(req);
    const count = trialCounts.get(ip) || 0;
    if (count >= FREE_LIMIT) { json(res, 429, { error: 'trial_ended' }); return; }
    trialCounts.set(ip, count + 1);
    res.setHeader('X-Messages-Remaining', String(FREE_LIMIT - (count + 1)));
  }

  const messagesWithReminder = messages.map((m, i) =>
    i === messages.length - 1 && m.role === 'user'
      ? { ...m, content: m.content + '\n\n[SYSTEM REMINDER: Maximum length response. No echoing. No summarizing what I said. Net new clinical insight only. Apply full frameworks from Durvasula, Vaknin, Navarro, Hughes, Hare, Biderman as relevant. Calibrate threat severity accurately — never soften.]' }
      : m
  );

  const upstream = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 8096,
      temperature: 0.8,
      system: SYSTEM_PROMPT,
      messages: [...messagesWithReminder, { role: 'assistant', content: 'The non-obvious variable here is' }],
      stream: true
    })
  });

  if (!upstream.ok) { const err = await upstream.json(); json(res, upstream.status, { error: err.error?.message || 'Anthropic error' }); return; }

  cors(res);
  res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' });
  const reader = upstream.body.getReader();
  const pump = async () => { while (true) { const { done, value } = await reader.read(); if (done) { res.end(); break; } res.write(value); } };
  pump().catch(() => res.end());
});

server.listen(PORT, () => console.log(`Reflect server on port ${PORT}`));
