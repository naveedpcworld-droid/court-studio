#!/usr/bin/env node
// ============================================================
//  THUMBNAIL TOOL (ChatGPT) — driver (Claude isay call karta hai)
//
//  Usi khuli ChatGPT window se (CDP) thumbnail banata hai. Naya Chrome nahi kholta.
//
//    node thumb.js "prompt"                         # 16:9 khud prompt mein lag jata hai
//    node thumb.js "prompt" --ref a.jpg --ref b.jpg # 1–3+ reference/character images
//    node thumb.js "prompt" --out /video/folder     # original + 2K wahan bhi save
//    node thumb.js "prompt" --no-upscale            # 2K skip
//    node thumb.js --change "correction text"       # ban-ne ke baad, usi chat mein
//
//  Output: out/thumb_<ts>.png + out/thumb_<ts>_2k.jpg (16:9). stdout: "SAVED <path>".
//
//  NOTE: ChatGPT ka DOM badalta rehta hai. Selectors best-effort hain; atke to Claude
//  live (read_page/screenshot) dekh kar wahi kaam manually kare.
// ============================================================
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const ROOT = __dirname;
const cfg = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8')); } catch { return {}; } })();
const PORT = cfg.port || 9334;

const args = process.argv.slice(2);
let prompt = '', change = '', outDir = '', grab = false, promptFile = '', prefix = 'thumb';
let keepRatio = false, newChat = false;
const refs = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--ref') refs.push(args[++i]);
  else if (a === '--change') change = args[++i];
  else if (a === '--out') outDir = args[++i];
  else if (a === '--prompt-file') promptFile = args[++i];
  else if (a === '--prefix') prefix = args[++i];
  else if (a === '--keep-ratio') keepRatio = true;   // photo enhancement: source aspect ratio hi rakho
  else if (a === '--new-chat') newChat = true;       // har image apni nayi chat mein
  else if (a === '--grab') grab = true;
  else if (!a.startsWith('--')) prompt = a;
}
if (promptFile) prompt = fs.readFileSync(promptFile, 'utf8');

// HAR prompt mein 16:9 mention LAZMI (ChatGPT ka koi 2K/aspect option nahi — prompt hi zariya).
// --keep-ratio (photo enhancement) mein koi ratio line NAHI lagti — source ka ratio barqarar rehta hai.
function withRatio(p) {
  if (keepRatio) return p;
  if (/16:9/.test(p)) return p;
  return `${p.replace(/\s*$/, '')} — 16:9 wide landscape YouTube thumbnail composition.`;
}

async function getPage(ctx) {
  let page = ctx.pages().find(p => p.url().includes('chatgpt.com') || p.url().includes('chat.openai.com'));
  if (!page) { page = ctx.pages()[0] || await ctx.newPage(); await page.goto('https://chatgpt.com', { waitUntil: 'domcontentloaded' }).catch(() => {}); }
  await page.bringToFront();
  return page;
}

// sirf VISIBLE composer lo (ChatGPT DOM mein chhupe contenteditable/textarea bhi hote hain)
async function promptBox(page) {
  const sels = ['#prompt-textarea', 'div[contenteditable="true"]', 'textarea'];
  for (const s of sels) {
    for (const el of await page.$$(s)) {
      if (await el.isVisible().catch(() => false)) return el;
    }
  }
  return null;
}

// composer ka "+" ("Add files and more") menu kholo
async function openPlus(page) {
  const plus = page.getByRole('button', { name: /Add files and more/i });
  if (await plus.count().catch(() => 0)) { await plus.first().click().catch(() => {}); await page.waitForTimeout(800); return true; }
  return false;
}

// LAZMI: image mode on. Fresh chat par main area ka "Create an image or sticker" chip
// sabse reliable hai (composer ke andar "Create image" chip ban jata hai). Sidebar ke
// "Create image" recents par click karna KHATARNAK hai (purani chat khul jati hai) —
// is liye sirf main area / composer scope karte hain.
async function enableCreateImage(page) {
  await dismissPopups(page);
  const on = async () => /\bCreate image\b/.test((await composerState(page)).text);
  if (await on()) { console.error('  create-image mode: ON'); return true; }

  const main = page.locator('main').first();
  const chip = main.getByText(/Create an image or sticker/i);
  if (await chip.count().catch(() => 0)) {
    await chip.first().click().catch(() => {});
    await page.waitForTimeout(1400);
  }
  if (await on()) { console.error('  create-image mode: ON'); return true; }

  // fallback: composer ka "+" → menu ke andar "Create image"
  const plus = page.getByRole('button', { name: /Add files and more/i });
  if (await plus.count().catch(() => 0)) {
    await plus.first().click().catch(() => {});
    await page.waitForTimeout(900);
    const box = await page.getByText(/Add photos & files/i).first().boundingBox().catch(() => null);
    if (box) {
      await page.evaluate((b) => {
        const cands = [...document.querySelectorAll('div,button')]
          .filter(e => e.innerText && e.innerText.split('\n').some(l => l.trim() === 'Create image'));
        const el = cands.filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.x >= b.x - 40 && r.y >= b.y; })
          .sort((a, c) => a.getBoundingClientRect().height - c.getBoundingClientRect().height)[0];
        if (el) el.click();
      }, box).catch(() => {});
      await page.waitForTimeout(1400);
    }
  }
  const ok = await on();
  console.error(ok ? '  create-image mode: ON' : '  ERR: create-image mode ON nahi hua');
  return ok;
}

// onboarding/tour popups hata do (composer block karte hain)
async function dismissPopups(page) {
  for (const rx of [/^Got it$/i, /^Okay, got it$/i, /^Dismiss$/i, /^No thanks$/i, /^Maybe later$/i]) {
    const el = page.getByRole('button', { name: rx });
    if (await el.count().catch(() => 0)) { await el.first().click().catch(() => {}); await page.waitForTimeout(300); }
  }
}

// Composer (visible) ki state: image-mode chip + attached previews
async function composerState(page) {
  return page.evaluate(() => {
    const ce = [...document.querySelectorAll('div[contenteditable="true"], textarea')]
      .find(e => e.getBoundingClientRect().width > 0);
    const form = ce ? ce.closest('form') : document.querySelector('form');
    return {
      text: form ? form.innerText.replace(/\s+/g, ' ').trim() : '',
      imgs: form ? form.querySelectorAll('img').length : 0,
    };
  }).catch(() => ({ text: '', imgs: 0 }));
}

// LAZMI (ref ke liye): asli UI se attach — "+" → "Add photos & files" (filechooser).
// ChatGPT ke 4 hidden input[type=file] hote hain aur galat wale par setInputFiles kaam
// nahi karta (photo attach hi nahi hoti) — is liye UI path PRIMARY, input sirf fallback.
async function addPhotos(page, files) {
  const paths = files.map(f => path.resolve(f)).filter(f => fs.existsSync(f));
  if (!paths.length) return false;
  await dismissPopups(page);
  let ok = false;
  for (let attempt = 1; attempt <= 2 && !ok; attempt++) {
    const plus = page.getByRole('button', { name: /Add files and more/i });
    if (!await plus.count().catch(() => 0)) break;
    await plus.first().click().catch(() => {});
    await page.waitForTimeout(900);
    try {
      const [chooser] = await Promise.all([
        page.waitForEvent('filechooser', { timeout: 15000 }),
        page.getByText(/Add photos & files|Add photos|Upload from computer/i).first().click(),
      ]);
      await chooser.setFiles(paths);
      console.error(`  ${paths.length} reference image(s) "+ → Add photos & files" se attach ho rahi hain...`);
    } catch (e) {
      console.error('  file-chooser fail: ' + e.message.split('\n')[0]);
      await page.keyboard.press('Escape').catch(() => {});
    }
    await page.waitForTimeout(5000 + paths.length * 2000);
    ok = (await composerState(page)).imgs > 0;
    if (!ok) console.error('  attachment preview nahi mila — retry...');
  }
  if (!ok) {
    // fallback: image accept wale input par direct setInputFiles
    for (const inp of await page.$$('input[type=file]')) {
      const acc = (await inp.getAttribute('accept').catch(() => '')) || '';
      if (!/image/.test(acc)) continue;
      await inp.setInputFiles(paths).catch(() => {});
      await page.waitForTimeout(5000);
      if ((await composerState(page)).imgs > 0) { ok = true; break; }
    }
  }
  if (!ok) console.error('  NOTE: reference attach confirm NAHI hua');
  return ok;
}

async function clickSend(page) {
  for (const sel of ['[data-testid="send-button"]', 'button[aria-label*="Send" i]']) {
    const el = await page.$(sel); if (el) { const dis = await el.isDisabled().catch(() => false); if (!dis) { await el.click().catch(() => {}); return true; } }
  }
  // fallback: Enter (composer)
  await page.keyboard.press('Enter').catch(() => {});
  return true;
}

// estuary/content + blob = generated files. Backdrop/thumbs aur ref previews ko chhod do
// (chat list virtualized hai — DOM order par bharosa mat karo, sirf full-size main images).
const genImgs = () => `[...document.querySelectorAll('img')].filter(im=>!((im.className||'').toString().includes('TransparencyBackdrop'))&&(im.naturalWidth>=1000||im.naturalWidth===0)).map(im=>im.currentSrc||im.src).filter(s=>s&&(s.includes('backend-api/estuary/content')||s.includes('oaiusercontent')||s.startsWith('blob:'))).filter((s,i,a)=>a.indexOf(s)===i)`;

// ---- API path (DOM virtualized hai, is liye pointers backend se) ----
// Is chat ke generated image pointers (sediment://file_...). User ke attached refs chhod do.
async function listAssets(page) {
  const convId = (page.url().match(/\/c\/([0-9a-f-]{8,})/i) || [])[1];
  if (!convId) return [];
  const ptrs = await page.evaluate(async (convId) => {
    const s = await (await fetch('/api/auth/session')).json();
    if (!s.accessToken) return [];
    const c = await (await fetch('/backend-api/conversation/' + convId, { headers: { Authorization: 'Bearer ' + s.accessToken } })).json();
    const msgs = Object.values(c.mapping || {}).map(n => n.message).filter(Boolean)
      .filter(m => m.author && m.author.role !== 'user')
      .sort((a, b) => (a.create_time || 0) - (b.create_time || 0));
    const out = [];
    for (const m of msgs) for (const pt of (m.content && m.content.parts) || []) {
      if (pt && pt.content_type === 'image_asset_pointer' && pt.asset_pointer) out.push(pt.asset_pointer);
    }
    return out;
  }, convId).catch(() => []);
  return ptrs || [];
}

// pointer (sediment:// / file-service://) → data URL
async function assetDataUrl(page, pointer) {
  const id = String(pointer).replace(/^[a-z-]+:\/\//i, '');
  const r = await page.evaluate(async (id) => {
    const s = await (await fetch('/api/auth/session')).json();
    if (!s.accessToken) return { err: 'no token' };
    const j = await (await fetch('/backend-api/files/' + id + '/download', { headers: { Authorization: 'Bearer ' + s.accessToken } })).json();
    if (!j.download_url) return { err: JSON.stringify(j).slice(0, 200) };
    const bl = await (await fetch(j.download_url)).blob();
    return { dataUrl: await new Promise(res => { const f = new FileReader(); f.onload = () => res(f.result); f.readAsDataURL(bl); }) };
  }, id);
  if (!r || !r.dataUrl) throw new Error('asset download fail: ' + ((r && r.err) || 'unknown'));
  return r.dataUrl;
}

(async () => {
  const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  const ctx = b.contexts()[0];
  const page = await getPage(ctx);
  if (newChat) {
    // NOTE: sirf goto('/') kaafi NAHI — ChatGPT purani chat hi dikhata rehta hai.
    // Sidebar ka "New chat" dabana LAZMI hai, phir welcome screen ka intezaar.
    await page.goto('https://chatgpt.com/', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: 'New chat' }).first().click().catch(() => {});
    await page.waitForTimeout(2000);
    for (let i = 0; i < 15; i++) {
      const fresh = await page.getByText(/What.s on your mind today\?|How can I help|Good to see you/i).count().catch(() => 0);
      if (fresh) break;
      await page.waitForTimeout(700);
    }
    console.error('  new chat: ' + page.url());
  }

  // saare chatgpt tabs scan karo (kabhi image doosre tab/conversation mein hota hai)
  const scan = async () => {
    const out = [];
    for (const pg of ctx.pages()) {
      if (pg.isClosed() || !/chatgpt\.com|chat\.openai\.com/.test(pg.url())) continue;
      const arr = await pg.evaluate(`(${genImgs})`).catch(() => []);
      (arr || []).forEach(s => out.push(s));
    }
    return out;
  };

  // GRAB mode: naya prompt bheje baghair, is chat ki sabse nayi generated image save karo
  // (jab image ban chuki ho magar auto-detect fail ho jaye — ya user ki chat mein pehle se ho)
  let src = null;
  if (grab) {
    const assets = await listAssets(page);
    if (assets.length) {
      src = assets[assets.length - 1];
      console.error('  grabbing latest image (api): ' + src);
    } else {
      console.error('  api se asset nahi mila — DOM fallback');
      src = await page.evaluate(() => {
        const ok = s => s && (s.startsWith('blob:') || s.includes('oaiusercontent') || s.includes('estuary/content'));
        const imgs = [...document.querySelectorAll('img')]
          .filter(im => ok(im.currentSrc || im.src) && (im.naturalWidth >= 1000 || im.naturalWidth === 0))
          .filter(im => !(im.className || '').toString().includes('TransparencyBackdrop'));
        if (!imgs.length) return null;
        const vh = innerHeight, vw = innerWidth;
        const area = im => {
          const r = im.getBoundingClientRect();
          const w = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0));
          const h = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
          return w * h;
        };
        const scored = imgs.map(im => ({ im, a: area(im) })).sort((x, y) => y.a - x.a);
        const pick = (scored[0] && scored[0].a > 0 ? scored[0].im : imgs[imgs.length - 1]);
        return pick ? (pick.currentSrc || pick.src) : null;
      }).catch(() => null);
    }
    if (!src) { console.error('ERR: chat mein koi generated image nahi mili'); process.exit(2); }
    console.error('  grabbing latest image...');
  } else {
    // PHOTO ENHANCEMENT / NEW image: pehle create-image mode, phir reference photo.
    // (Reference attach karte waqt mode on rehta hai — order: mode → attach.)
    if (!change) {
      if (refs.length) {
        const modeOn = await enableCreateImage(page);
        if (!modeOn) { console.error('ERR: create-image mode on nahi hua — generation skipp'); await b.close(); process.exit(4); }
        const attached = await addPhotos(page, refs);
        if (!attached) { console.error('ERR: reference photo attach nahi hui — generation skipp'); await b.close(); process.exit(3); }
      } else {
        await enableCreateImage(page);
      }
    }

    const box = await promptBox(page);
    if (!box) { console.error('ERR: prompt box nahi mila (login hua hai?)'); process.exit(1); }
    await box.click();
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A').catch(() => {});
    await page.keyboard.press('Backspace').catch(() => {});
    const text = change ? change : withRatio(prompt);
    // lamba prompt (photo-enhancement briefs) keyboard.type se bohat slow/drop-prone hai —
    // 400+ chars par insertText (ek hi input event) use karo.
    if (text.length > 400) {
      await page.keyboard.insertText(text);
      await page.waitForTimeout(800);
    } else {
      await page.keyboard.type(text, { delay: 2 });
    }
    await page.waitForTimeout(400);
    console.error('  prompt chars: ' + text.length + ' | composer: ' + (await composerState(page)).text.slice(0, 60));

    // send se THEEK pehle snapshot (API pointers + DOM srcs dono)
    const beforeAssets = new Set(await listAssets(page));
    const beforeDom = new Set(await scan());
    await clickSend(page);
    console.error('generating... (image ~30–90s)');

    for (let i = 0; i < 160; i++) {   // ~8 min (ChatGPT free slow ho sakta hai)
      await page.waitForTimeout(3000);
      const freshAsset = (await listAssets(page)).find(a => !beforeAssets.has(a));
      if (freshAsset) { src = freshAsset; break; }
      const freshDom = (await scan()).find(s => !beforeDom.has(s));
      if (freshDom) { src = freshDom; break; }
      if (i % 5 === 4) {
        const bodyTxt = await page.evaluate(() => document.body.innerText).catch(() => '');
        const lim = bodyTxt.match(/[^\n]*(You.ve reached|image generations? (?:limit|left)|upgrade to Plus|try again (?:in|tomorrow))[^\n]*/i);
        if (lim) { console.error('ERR: ChatGPT limit — ' + lim[0].trim().slice(0, 160)); await b.close(); process.exit(5); }
      }
    }
    if (!src) { console.error('ERR: image nahi bani (timeout ya image-gen off)'); await b.close(); process.exit(2); }
  }

  const isPointer = /^[a-z-]+:\/\/(file-|file_)/i.test(src);
  const dataUrl = isPointer ? await assetDataUrl(page, src) : await page.evaluate(async (u) => {
    const r = await fetch(u); const bl = await r.blob();
    return await new Promise(res => { const f = new FileReader(); f.onload = () => res(f.result); f.readAsDataURL(bl); });
  }, src);
  const m = /^data:image\/([\w+.-]+);base64,(.*)$/s.exec(dataUrl);
  if (!m) { console.error('ERR: image decode fail'); process.exit(2); }
  const ext = m[1] === 'jpeg' ? 'jpg' : m[1];
  fs.mkdirSync(path.join(ROOT, 'out'), { recursive: true });
  const ts = Date.now();
  const orig = path.join(ROOT, 'out', `${prefix}_${ts}.${ext}`);
  fs.writeFileSync(orig, Buffer.from(m[2], 'base64'));
  console.log('SAVED ' + orig);

  if (outDir) {
    fs.mkdirSync(outDir, { recursive: true });
    const oCopy = path.join(outDir, path.basename(orig));
    fs.copyFileSync(orig, oCopy); console.log('SAVED ' + oCopy);
  }

  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
