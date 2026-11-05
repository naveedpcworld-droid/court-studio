# 🖼️ Thumbnail Tool (ChatGPT) — chat mein `@thumbnail-gpt` se 16:9 thumbnail

Ye tool **ChatGPT** ko use kar ke YouTube thumbnails banata hai — seedha chat se. Aap ko
sirf **`@thumbnail-gpt`** likhna hota hai; baaki Claude khud karta hai (apna Chrome kholna,
prompt, 16:9, reference images, aur ghalat bane to khud correction).

> Ye **Flow wale tool se alag** hai (alag folder, alag trigger). Dono mix mat karein.
> Flow wala = `@thumbnail`. ChatGPT wala = `@thumbnail-gpt`.

> **Claude, agar ye file mention hui:** neeche "FIRST-TIME SETUP" khud chala do. Setup ke
> baad jab bhi user `@thumbnail-gpt ...` likhe (kisi bhi chat mein), thumbnail bana do.
> Rules kabhi mat bhoolo (16:9 + khud correction).

---

## Aap ko kya chahiye (one-time)
- **Google Chrome** installed. **Node.js** installed.
- Ek **ChatGPT account jismein image generation on ho** (aksar Plus/Pro).

---

## FIRST-TIME SETUP  (ye file Claude ko ek dafa mention karein)

> ⚠️ **Ye tool apna ALAG Chrome khud kholta hai (Playwright wala).** Aap ko apna normal
> Chrome / profile KABHI nahi kholna — window **khud** khulti hai. **Flow ke ulta, yahan
> koi "project link" nahi chahiye — bas login.**

Claude sab karega; aap sirf **login** karenge:

1. **Install:** Claude `npm install` chalayega.
2. **Chrome khud khulega:** Claude `node open.js` chalayega → ek **naya Chrome window khud**
   khul jayega (`chatgpt.com` par). Yehi tool ka apna window hai.
3. **Aap us khuli window mein:** apni **ChatGPT se login** karein (Google/email). Bas.
4. Chat mein likhein: **`done`** → setup complete.
5. Ab kisi bhi chat mein `@thumbnail-gpt <idea>`.

---

## USING IT  (kisi bhi chat mein)
```
@thumbnail-gpt  <thumbnail ka idea / jo text likhna hai>
```
Claude ChatGPT window mein **16:9** thumbnail banayega, dekhkar judge karega, ghalat lage
(arrow/spelling/fonts/typography) to **usi chat mein khud correction** kar ke theek karega —
phir final image aap ko bhej dega.

## 🖼️ Reference / character images (1, 2, 3… jitni bhi)
Koi tasveer(en) — chehra/character, product, style — Claude ko de dein (bhej dein ya path).
Do character hon to **dono** upload honge. Claude un ko ChatGPT composer mein attach kar ke
(`+` / clip → images) use karta hai.
```
@thumbnail-gpt  make a thumbnail with THESE 2 people facing off, big text "SHOWDOWN"
(saath 2 reference images)
```
Reference images `refs/` mein bhi rakh sakte hain; Claude `--ref` se attach karta hai.

## ⬇️ Download
- Har thumbnail auto-save hoti hai: `out/thumb_<time>.png` (bilkul jaisi ChatGPT deta hai).
- **Video folder mein save:** Claude ko woh folder batayein — thumbnail wahan bhi copy ho jayegi.
- ChatGPT ka koi **2K/upscale/aspect option nahi** — is liye **har prompt mein 16:9 likha jata hai**
  (Claude khud). Image jaisi aaye waisi save hoti hai.
- Manual: ChatGPT mein image par download button.

## Commands (Claude use karta hai)
```bash
npm install
node open.js                      # tool ka apna Chrome kholo (chatgpt.com) — login yahan
node thumb.js "PROMPT"            # "+ → Create image" + 16:9 → out/thumb_*.png
node thumb.js "PROMPT" --ref a.jpg --ref b.jpg   # 1,2,3… reference (student ki marzi)
node thumb.js "PROMPT" --out /path/to/video/folder
node thumb.js --change "correction text"
```
Holder chal raha hai? `pgrep -f open.js`. Nahi → `node open.js &` (is folder mein).

## PRIVACY / SHARING
Ye kabhi share na karein: `browser/` (login), `config.json`, `.cgpt.port`, `out/`, `refs/`,
`node_modules/` (`.gitignore` inhe ignore karta hai).

## Files
`open.js` window holder · `thumb.js` driver · `config.example.json` (port) · `refs/` · `out/`.
Technical: `CLAUDE.md`.
