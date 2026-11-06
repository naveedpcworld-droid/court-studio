# Updates — apni marzi (optional)

Library (10,981 recordings ke links + transcripts) license key ke saath teacher ke server se aati hai.
Original repo khud kabhi update nahi hota — **koi automatic cheez original GitHub pe nahi chalti.**
Naye court videos chahiye ya nahi, ye tumhara faisla hai. 3 tareeqe:

## 1. Update nahi chahiye
Kuch mat karo. Clone karo aur use karo — library poori kaam karti hai.

## 2. Apne computer pe update (sab se aasan)
Jab dil chahe, Claude se kaho *"library update karo"*, ya khud:
```bash
python3 tools/update.py            # desk/channels.yml ke sab channels check, naye videos + transcripts
python3 tools/update.py --max-new 20
```
- Sirf tumhare folder mein `desk/data/` badalta hai. `tools/find_case.py` naye videos foran dikhata hai (tier `NEW`).
- Apne ghar ke internet se chalta hai (YouTube GitHub servers ko kabhi kabhi block karta hai, ghar ko nahi).
- Naya channel add karna ho: `desk/channels.yml` mein ek entry (format wahin likha hai).

## 3. Apni GitHub pe automatic — band hai
Library ab public GitHub pe nahi rakhi jati (sirf license key wale download kar sakte hain), is liye GitHub
Actions wala auto-update hata diya gaya hai. Updates sirf apne computer pe (upar wala tareeqa 2).

## Library khud (links + transcripts)
Repo mein library nahi hoti. License activate karte hi khud download hoti hai (~160 MB, ek dafa).
Teacher nayi library daale to: `python3 tools/license.py library` (sirf nayi files aati hain).

## Naye templates / fixes (teacher ki taraf se)
Jab original repo mein naye templates (T15, B06...) ya fixes aayein, apne folder mein:
```bash
git pull
```
ya Claude se kaho *"court-studio update karo"*. Ye bhi tumhari marzi hai — na karo to purana version chalta rahega.
Tumhare apne templates (`S01-...`), projects aur `config.env` git pull se kabhi nahi badalte.
Agar tumne T/B template ki file khud badli thi aur pull conflict de → Claude se kaho "conflict theek karo",
ya behtar: apna badla hua version `new_template.py` se S-template bana lo.

## Apna template banana
```bash
cd studio
python3 tools/new_template.py "red court" --from T02 --set accent=#E53935 caption.position=below caption.style=box --bg meri_photo.jpg --project <project>
```
Ya bas Claude se kaho: *"T02 jaisa template banao lekin lal frame aur captions neeche"*. Naam khud `S01-red-court`
banta hai, `preview.jpg` banta hai — dekho, pasand aaye to `--template S01` se use karo. Fields ki list: `studio/docs/TEMPLATES.md`.
