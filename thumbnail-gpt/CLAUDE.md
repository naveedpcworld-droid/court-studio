# @thumbnail-gpt — ChatGPT se chat mein thumbnail (Claude ke liye technical spec)

> 👋 **PEHLI DAFA SETUP (ye clean copy).** ⚠️ Ye tool apna ALAG Playwright Chrome **khud**
> kholta hai. User se **KABHI** "apna Chrome kholo" mat kaho. Flow ke ulta, yahan koi project
> link nahi — sirf **login**. Tarteeb: `npm install` → `node open.js` (Chrome khud khulta hai,
> chatgpt.com) → user usi window mein ChatGPT login kare → user `done` likhe → setup complete.

> Ye **Flow wale tool (`@thumbnail`) se bilkul alag** hai. Mix mat karo. Yahan trigger
> **`@thumbnail-gpt`**, profile `browser/chatgpt`, CDP **:9334** (Flow :9333 se alag).

Jab bhi user **`@thumbnail-gpt`** mention kare, isi tool ko use karo. Naya script mat likho —
`thumb.js` hi driver hai. Kaam hamesha **aik hi khuli ChatGPT window** mein (CDP se drive).

## HARD RULES
1. Surface = **ChatGPT** (chatgpt.com). Composer mein **LAZMI "+" → "Create image"** (image-mode on),
   aur **har prompt mein "16:9"** (ChatGPT ka koi aspect/2K option nahi — prompt hi zariya; **2K/upscale mat karo**).
2. Reference/character image(s): **"+" → "Add photos & files"** se attach (`--ref`, jitni bhi — 1/2/3, student ki marzi).
3. Ban-ne ke baad **khud judge karo**; ghalat (arrow/spelling/fonts/typography) ho to usi chat
   mein correction do (`--change`) — jab tak theek na ho. Ghalat thumbnail kabhi mat do.
4. Ek profile, ek Chrome. `browser/` + `config.json` personal — kabhi share mat karo.

## Chalao
```bash
node open.js                    # holder — tool ka apna Chrome (chatgpt.com), CDP :<port>
node thumb.js "PROMPT"          # 16:9 → out/thumb_<ts>.png + out/thumb_<ts>_2k.jpg
node thumb.js "PROMPT" --ref a.jpg --ref b.jpg   # 1–3+ reference/character images
node thumb.js "PROMPT" --out /path/to/video/folder
node thumb.js "PROMPT" --no-upscale
node thumb.js --change "correction text"
```
Holder check/start: `pgrep -f open.js || (cd <is folder> && node open.js &)`.
Har `SAVED <path>` stdout par — wahi file user ko `SendUserFile` se bhejo.

## Reference / character images
`--ref` (jitni baar bhi). thumb.js ChatGPT composer ka `input[type=file]` par setInputFiles
(multiple) karta hai; na mile to `+`/clip daba kar reveal. Auto na ho to interactively attach.

## Download (no 2K)
- Auto-save `out/thumb_<ts>.png` (jaisi ChatGPT deta hai — koi 2K/upscale/crop NAHI).
- `--out <dir>` → video wale folder mein bhi original copy.
- 16:9 sirf prompt ke through (ChatGPT aksar square deta hai; koi aspect control nahi).

## Kaise chalta hai (wiring — DOM badle to yehi manually karo; ChatGPT ka DOM aksar badalta hai)
- Holder `open.js`: persistent context `browser/chatgpt`, headed, channel chrome,
  `--remote-debugging-port=<port>`, chatgpt.com par.
- Driver: `connectOverCDP('http://127.0.0.1:<port>')` → chatgpt.com wala page.
- **Prompt box:** `#prompt-textarea` (contenteditable) — fallback koi visible contenteditable/textarea.
- **Reference:** composer ka `input[type=file]` par setInputFiles (multiple). Warna `+`/clip.
- **Send:** `[data-testid="send-button"]` — fallback aria-label *Send*, warna Enter.
- **Result image:** naya `<img>` jiska src `oaiusercontent` (ya `blob:`) aur naturalWidth ≥ 512.
  Bhejne se pehle maujood srcs yaad rakho, phir naya aane ka intezaar (~5 min). page-context
  `fetch(src)`→blob→base64 se save (session cookies use hote hain).
- **Correction:** usi chat ke composer mein correction likho + send. Naya image save.

## Files
`open.js` holder (apna Chrome kholta hai) · `thumb.js` driver · `config.json` (port; local) ·
`config.example.json` · `README.md` (student setup) · `refs/` · `out/` · `browser/chatgpt` (login, private).
