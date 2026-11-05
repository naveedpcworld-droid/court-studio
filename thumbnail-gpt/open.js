#!/usr/bin/env node
// ============================================================
//  THUMBNAIL TOOL (ChatGPT) — browser holder
//
//  Ye TOOL ka APNA Chrome window khud kholta hai (Playwright, persistent profile) aur
//  chatgpt.com par le jata hai. User ko apna normal Chrome NAHI kholna — window khud
//  khulti hai aur zinda rehti hai. CDP port par bhi hoti hai taake Claude usi khuli
//  window se connect kar ke thumbnail bana sake.
//
//  Setup ke liye Flow wali tarah koi "project link" NAHI chahiye — bas is khuli window
//  mein ek dafa apni ChatGPT (Google/email) se LOGIN karo, "done" likho. Bas.
//
//  Chalao (background):  node open.js      Band:  kill <pid>  ya window band karo.
// ============================================================
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const ROOT = __dirname;
const cfg = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'config.json'), 'utf8')); } catch { return {}; } })();
const PORT = cfg.port || 9334;
const START_URL = (cfg.startUrl || 'https://chatgpt.com').trim();

const BASE_ARGS = ['--no-first-run', '--password-store=basic', '--no-default-browser-check',
  '--disable-blink-features=AutomationControlled', '--window-size=1280,860', '--window-position=80,80'];

(async () => {
  const dir = path.join(ROOT, 'browser', 'chatgpt');
  fs.mkdirSync(dir, { recursive: true });
  for (const f of ['SingletonLock', 'SingletonCookie', 'SingletonSocket', 'lockfile'])
    fs.rmSync(path.join(dir, f), { force: true });

  const ctx = await chromium.launchPersistentContext(dir, {
    headless: false, channel: 'chrome', viewport: null, acceptDownloads: true,
    ignoreDefaultArgs: ['--enable-automation'],
    args: [...BASE_ARGS, `--remote-debugging-port=${PORT}`],
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(START_URL, { waitUntil: 'domcontentloaded', timeout: 90000 }).catch(() => {});
  fs.writeFileSync(path.join(ROOT, '.cgpt.port'), String(PORT));

  console.log(`  [chatgpt] tool ka apna Chrome khul gaya → ${START_URL}   (profile browser/chatgpt, CDP :${PORT})`);
  console.log('\n  >>> IS KHULI WINDOW MEIN apni ChatGPT se LOGIN karein (apna normal Chrome mat kholein).');
  console.log('  >>> Login ke baad chat mein "done" likh dein — bas, tool ready.');
  console.log('  >>> (ChatGPT account mein image generation on hona chahiye.)\n');
  await new Promise(res => ctx.on('close', res));
  console.log('  window band — bye.');
  process.exit(0);
})().catch(e => { console.error('  [X]', e.message); process.exit(1); });
