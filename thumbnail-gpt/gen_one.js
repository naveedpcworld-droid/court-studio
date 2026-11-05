#!/usr/bin/env node
// ============================================================
//  gen_one.js — ONE image from a CLEAN ChatGPT chat with up to 3 refs.
//  Proven recipe: new chat → attach refs (direct file input) → explicit
//  "generate an image" prompt (GPT-4o auto-image, no mode toggle) → save.
//    node gen_one.js --ref a.png --ref b.png --out /abs/path.png "PROMPT"
//  stdout: "SAVED <path>"  |  "NOIMG <assistant reply>"  |  "ERR <msg>"
// ============================================================
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const cfg = (() => { try { return JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8')); } catch { return {}; } })();
const PORT = cfg.port || 9334;

const args = process.argv.slice(2);
let prompt = '', out = ''; const refs = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--ref') refs.push(args[++i]);
  else if (a === '--out') out = args[++i];
  else if (!a.startsWith('--')) prompt = a;
}
const paths = refs.map(f => path.resolve(f)).filter(f => fs.existsSync(f));

(async () => {
  const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  const ctx = b.contexts()[0];
  let page = ctx.pages().find(p => p.url().includes('chatgpt.com')) || ctx.pages()[0] || await ctx.newPage();
  // CLEAN new chat (clears any leftover composer state)
  await page.goto('https://chatgpt.com/?model=auto', { waitUntil: 'domcontentloaded' }).catch(() => {});
  await page.waitForTimeout(4000);
  for (const rx of [/^Got it$/i, /^Okay, got it$/i, /^Stay logged out$/i, /^Dismiss$/i]) {
    const e = page.getByRole('button', { name: rx }); if (await e.count().catch(() => 0)) await e.first().click().catch(() => {});
  }
  // wait (up to 40s) for a VISIBLE composer — ChatGPT also keeps hidden contenteditables in the DOM
  let box = null;
  for (let i = 0; i < 40 && !box; i++) {
    for (const sel of ['#prompt-textarea', 'div[contenteditable="true"]', 'textarea']) {
      for (const el of await page.$$(sel)) { if (await el.isVisible().catch(() => false)) { box = el; break; } }
      if (box) break;
    }
    if (!box) await page.waitForTimeout(1000);
  }
  if (!box) { console.log('ERR no prompt box'); await b.close(); process.exit(1); }
  // attach refs AFTER the composer exists (direct hidden file input), then wait for the upload previews
  if (paths.length) {
    // ChatGPT has several hidden inputs: "Take a photo" (camera, single) must NOT be used.
    // Prefer: multiple + image-only  >  multiple + image/video  >  multiple (any)  >  anything not the camera.
    const pick = async () => {
      const ins = [];
      for (const inp of await page.$$('input[type=file]')) {
        const acc = (await inp.getAttribute('accept').catch(() => '')) || '';
        const mul = await inp.evaluate(e => e.multiple).catch(() => false);
        const lab = ((await inp.getAttribute('aria-label').catch(() => '')) || '').toLowerCase();
        if (/take a photo|camera/.test(lab)) continue;
        const rank = mul && acc === 'image/*' ? 0 : mul && /image/.test(acc) ? 1 : mul ? 2 : 3;
        ins.push([rank, inp]);
      }
      ins.sort((x, y) => x[0] - y[0]); return ins.length ? ins[0][1] : null;
    };
    const thumbs = () => page.evaluate(`document.querySelectorAll('form img, [data-testid*="attachment"] img, img[src^="blob:"]').length`).catch(() => 0);
    let attached = false;
    for (let attempt = 0; attempt < 2 && !attached; attempt++) {
      const n0 = await thumbs();
      if (attempt === 0) {
        let tgt = null;
        for (let i = 0; i < 15 && !tgt; i++) { tgt = await pick(); if (!tgt) await page.waitForTimeout(1000); }
        if (tgt) await tgt.setInputFiles(paths).catch(e => console.error('attach err ' + e.message.slice(0, 60)));
      } else {                                     // fallback: real "+" menu -> "Add photos & files" -> file chooser
        const plus = page.getByRole('button', { name: /add files|attach|add photos/i }).first();
        await plus.click().catch(() => {}); await page.waitForTimeout(800);
        const [fc] = await Promise.all([
          page.waitForEvent('filechooser', { timeout: 8000 }).catch(() => null),
          page.getByText(/add photos|upload from computer|photos & files/i).first().click().catch(() => {}),
        ]);
        if (fc) await fc.setFiles(paths).catch(() => {});
      }
      for (let i = 0; i < 30; i++) { await page.waitForTimeout(1000); if ((await thumbs()) >= n0 + paths.length) { attached = true; break; } }
    }
    if (!attached) { console.log('ERR photos did not attach — not sending without them'); await b.close(); process.exit(1); }
    await page.waitForTimeout(3000 + paths.length * 1500);     // let the upload finish server-side
  }
  const full = /^please generate an image/i.test(prompt) ? prompt : 'Please generate an image for me. ' + prompt;
  await box.click(); await page.keyboard.type(full, { delay: 1 }); await page.waitForTimeout(600);
  // generated images: big <img> inside an ASSISTANT message (src may be estuary/oaiusercontent OR blob:)
  const gen = () => page.evaluate(`[...document.querySelectorAll('[data-message-author-role="assistant"] img, img[alt*="Generated" i]')]
      .filter(im => (im.naturalWidth || 0) >= 600).map(im => im.currentSrc || im.src)
      .concat([...document.querySelectorAll('img')].map(im => im.currentSrc || im.src).filter(s => /estuary|oaiusercontent/.test(s)))`).catch(() => []);
  const before = new Set(await gen());
  // send: the button stays disabled while images upload -> retry until the composer empties (= message sent)
  const composerText = () => box.evaluate(el => (el.value !== undefined ? el.value : el.textContent) || '').catch(() => '');
  for (let i = 0; i < 60; i++) {
    let clicked = false;
    for (const sel of ['[data-testid="send-button"]', '#composer-submit-button', 'button[aria-label*="Send" i]']) {
      const el = await page.$(sel);
      if (el && await el.isVisible().catch(() => false) && !(await el.isDisabled().catch(() => true))) { await el.click().catch(() => {}); clicked = true; break; }
    }
    if (!clicked && i > 20) { await box.click().catch(() => {}); await page.keyboard.press('Enter'); }
    await page.waitForTimeout(1500);
    if ((await composerText()).trim().length < 5) break;
  }
  if ((await composerText()).trim().length >= 5) { console.log('ERR could not send'); await b.close(); process.exit(1); }
  console.error('generating...');
  let src = null;
  for (let i = 0; i < 130; i++) { await page.waitForTimeout(3000); const now = await gen(); const fr = now.find(s => !before.has(s)); if (fr) { src = fr; break; } }
  if (!src) {
    const reply = await page.evaluate(() => { const m = [...document.querySelectorAll('[data-message-author-role="assistant"]')].pop(); return m ? (m.textContent || '').replace(/\s+/g, ' ').slice(0, 200) : ''; }).catch(() => '');
    console.log('NOIMG ' + reply); await b.close(); process.exit(2);
  }
  const du = await page.evaluate(async (u) => { const r = await fetch(u); const bl = await r.blob(); return await new Promise(res => { const f = new FileReader(); f.onload = () => res(f.result); f.readAsDataURL(bl); }); }, src);
  const m = /^data:image\/([\w+.-]+);base64,(.*)$/s.exec(du);
  if (!m) { console.log('ERR decode'); await b.close(); process.exit(2); }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, Buffer.from(m[2], 'base64'));
  console.log('SAVED ' + out);
  await b.close();
})().catch(e => { console.log('ERR ' + e.message); process.exit(1); });
