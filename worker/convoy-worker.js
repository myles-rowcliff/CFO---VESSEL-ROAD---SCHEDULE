/*
 * CFO convoy manifests – save service (Cloudflare Worker)
 *
 * The website sends convoy manifests here with a passcode. This service checks the passcode and saves
 * the change to the GitHub repo with its own token, so the people entering convoys don't need a GitHub
 * account. It also sets the day's "Actual by truck (L)" in sva.json from the manifests (by ETA Kiunga).
 *
 * Settings (Cloudflare dashboard → the worker → Settings → Variables and secrets):
 *   GITHUB_TOKEN    secret – fine-grained token, this repo only, Contents: read and write
 *   PASSCODES       secret – one or more passcodes separated by commas, e.g. "aiambak-ops,night-shift"
 *   ALLOWED_ORIGIN  text   – the website address, e.g. https://myles-rowcliff.github.io
 *   REPO            text   – owner/repo, e.g. myles-rowcliff/CFO---VESSEL-ROAD---SCHEDULE
 *
 * Nothing secret is in this file; it is safe in a public repo.
 */

const BRANCH = 'main';
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const cors = (env, req) => {
  const o = req.headers.get('Origin') || '';
  const allowed = (env.ALLOWED_ORIGIN || '').split(',').map((s) => s.trim()).filter(Boolean);
  return {
    'Access-Control-Allow-Origin': allowed.includes(o) ? o : allowed[0] || '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
};
const json = (env, req, body, status = 200) => new Response(JSON.stringify(body), {status, headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(env, req)}});

const b64enc = (str) => { const b = new TextEncoder().encode(str); let s = ''; b.forEach((c) => { s += String.fromCharCode(c); }); return btoa(s); };
const b64dec = (b64) => new TextDecoder().decode(Uint8Array.from(atob(b64.replace(/\n/g, '')), (c) => c.charCodeAt(0)));

const gh = (env, path, init = {}) => fetch(`https://api.github.com/repos/${env.REPO}/contents/${path}`, {
  ...init,
  headers: {Authorization: 'Bearer ' + env.GITHUB_TOKEN, Accept: 'application/vnd.github+json', 'User-Agent': 'cfo-convoy-worker', ...(init.headers || {})},
});
const ghGet = async (env, path) => {
  const r = await gh(env, path + '?ref=' + BRANCH);
  if (!r.ok) throw new Error('GitHub read ' + path + ': ' + r.status);
  const j = await r.json();
  return {sha: j.sha, text: b64dec(j.content)};
};
const ghPut = async (env, path, text, sha, message) => {
  const r = await gh(env, path, {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message, content: b64enc(text), sha, branch: BRANCH})});
  if (!r.ok) throw Object.assign(new Error('GitHub save ' + path + ': ' + r.status), {status: r.status});
};

// date helpers on plain local times (no time zones: everything in the schedule is PNG time)
const etaKey = (c) => {
  const [y, m, d] = String(c.date).split('-').map(Number);
  const [hh, mm] = String(c.time || '05:00').split(':').map(Number);
  const t = new Date(Date.UTC(y, m - 1, d, hh + 7, mm || 0));
  return t.toISOString().slice(0, 10);
};
const litres = (c) => (c.trucks || []).reduce((a, t) => a + (Number(t.litres) || 0), 0);
const sumByEta = (list) => { const m = new Map(); list.forEach((c) => { const k = etaKey(c); m.set(k, (m.get(k) || 0) + litres(c)); }); return m; };
const shortDate = (k) => { const [, m, d] = k.split('-').map(Number); return d + ' ' + MON[m - 1]; };

// keep only the fields a manifest has, so nothing else can be written to the repo
const cleanConvoy = (c) => {
  if (!c || typeof c !== 'object') throw new Error('No convoy');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(c.date || '')) throw new Error('Bad departure date');
  if (!/^\d{2}:\d{2}$/.test(c.time || '')) throw new Error('Bad departure time');
  const trucks = (Array.isArray(c.trucks) ? c.trucks : []).slice(0, 60).map((t) => ({
    truck: String((t && t.truck) || '').slice(0, 40),
    tanker: String((t && t.tanker) || '').slice(0, 40),
    litres: t && t.litres !== '' && t.litres != null && !isNaN(Number(t.litres)) ? Math.max(0, Math.min(100000, Math.round(Number(t.litres)))) : '',
  }));
  return {id: String(c.id || '').slice(0, 40) || ('c' + Date.now().toString(36)), date: c.date, time: c.time, ref: String(c.ref || '').slice(0, 60), trucks};
};

const apply = (list, body) => {
  if (body.action === 'upsert') { const c = cleanConvoy(body.convoy); const k = list.findIndex((x) => x.id === c.id); if (k >= 0) list[k] = c; else list.push(c); return {list, label: (k >= 0 ? 'updated' : 'added') + ': ' + (c.ref || c.id) + ' (' + shortDate(c.date) + ')'}; }
  if (body.action === 'delete') { const id = String(body.id || ''); const c = list.find((x) => x.id === id); return {list: list.filter((x) => x.id !== id), label: 'deleted: ' + ((c && c.ref) || id)}; }
  if (body.action === 'add_many') { const add = (Array.isArray(body.convoys) ? body.convoys : []).slice(0, 50).map(cleanConvoy).filter((c) => !list.some((x) => x.id === c.id)); return {list: list.concat(add), label: 'moved from browser: ' + add.map((c) => c.ref).join(', ')}; }
  throw new Error('Unknown action');
};

const okPass = (env, p) => (env.PASSCODES || '').split(',').map((s) => s.trim()).filter(Boolean).includes(String(p || '').trim());

async function save(env, body) {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const f = await ghGet(env, 'docs/data/convoys.json');
      const j = JSON.parse(f.text); const before = (j.convoys || []).slice();
      const {list, label} = apply(before.slice(), body);
      const msg = 'Convoy manifest ' + label + (body.who ? ' – ' + String(body.who).slice(0, 40) : '');
      j.convoys = list;
      await ghPut(env, 'docs/data/convoys.json', JSON.stringify(j, null, 1), f.sha, msg);
      const oldS = sumByEta(before), newS = sumByEta(list);
      const days = [...new Set([...oldS.keys(), ...newS.keys()])].filter((k) => (oldS.get(k) || 0) !== (newS.get(k) || 0)).sort();
      const actuals = {};
      if (days.length) {
        const g = await ghGet(env, 'docs/data/sva.json'); const sv = JSON.parse(g.text); const R = sv.value.rows;
        Object.keys(R).forEach((k) => { if (k === '1' || !days.includes(R[k][0])) return; const d = R[k][0], nv = newS.get(d) || 0; if (nv > 0) R[k][4] = nv; else if (R[k][4] === (oldS.get(d) || 0)) R[k][4] = null; actuals[d] = R[k][4]; });
        const out = JSON.stringify(sv);
        await ghPut(env, 'docs/data/sva.json', out, g.sha, msg + ' – truck actuals');
        try { const h = await ghGet(env, 'data/d_sva.json'); await ghPut(env, 'data/d_sva.json', out, h.sha, msg + ' – truck actuals (copy)'); } catch (e) { /* copy is optional */ }
        const last = Object.keys(R).filter((k) => k !== '1' && (R[k][3] != null || R[k][4] != null)).map((k) => R[k][0]).sort().pop();
        if (last) { try { const m = await ghGet(env, 'docs/data/meta.json'); const mj = JSON.parse(m.text); const nn = 'Actuals to ' + shortDate(last); if (mj.note !== nn) { mj.note = nn; await ghPut(env, 'docs/data/meta.json', JSON.stringify(mj), m.sha, msg + ' – meta'); } } catch (e) { /* optional */ } }
      }
      return {ok: true, convoys: list, days, actuals};
    } catch (e) {
      if (attempt === 0 && (e.status === 409 || e.status === 422)) continue;  // someone saved at the same moment – try once more
      throw e;
    }
  }
}

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, {headers: cors(env, req)});
    const url = new URL(req.url);
    try {
      if (req.method === 'GET' && url.pathname === '/data') {  // latest copies straight from the repo (the public site can lag a few minutes)
        const name = url.searchParams.get('name');
        if (!['convoys', 'sva'].includes(name)) return json(env, req, {error: 'Not found'}, 404);
        const f = await ghGet(env, 'docs/data/' + name + '.json');
        return new Response(f.text, {headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors(env, req)}});
      }
      if (req.method === 'POST' && url.pathname === '/check') {
        const body = await req.json().catch(() => ({}));
        if (!okPass(env, body.passcode)) { await new Promise((r) => setTimeout(r, 800)); return json(env, req, {ok: false, error: 'Wrong passcode'}, 401); }
        return json(env, req, {ok: true});
      }
      if (req.method === 'POST' && url.pathname === '/save') {
        const body = await req.json().catch(() => ({}));
        if (!okPass(env, body.passcode)) { await new Promise((r) => setTimeout(r, 800)); return json(env, req, {ok: false, error: 'Wrong passcode'}, 401); }
        return json(env, req, await save(env, body));
      }
      return json(env, req, {error: 'Not found'}, 404);
    } catch (e) {
      return json(env, req, {ok: false, error: String((e && e.message) || e)}, 500);
    }
  },
};
