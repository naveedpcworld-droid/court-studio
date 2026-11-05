# Templates — kaise kaam karte hain / naya kaise banayein

Har template = `templates/Txx-name/` folder: `template.json` + `bg.jpg` (1920x1080) + `preview.jpg` + `sample.mp4`.
Structure `tools/layouts.py` ki **layout family** se aata hai; har family 1 / 2 / 3+ cameras ke liye alag
jagah deti hai, aur narration ke waqt (mode `vo`) layout badal bhi sakti hai.

| layout | kya karta hai |
|---|---|
| `strip` | 2 cameras side-by-side (+ 3rd as PiP). 1 camera = ek bara frame. Frame style: `lines` / `outer` / `box` / `none` |
| `news` | footage box + right CASE FILE panel (`info` fields) + bottom title ticker; 2nd camera = PiP |
| `spotlight` | 1 bari camera + right column mein 3 tak choti |
| `fullbleed` | edge-to-edge; 2 cameras = do full-height halves |
| `cinema` | 2.39:1 letterbox, captions bottom bar mein |
| `bigpip` | camera 1 full screen, camera 2 (aur 3) bare PiP |
| `gallery` | 6 tak saari tiles barabar grid mein, name tags |
| `versus` | do halves, colored name plates + VS badge |

## template.json fields
```json
{
 "name": "...", "best_for": "...", "layout": "strip",
 "bg": "bg.jpg",
 "frame": {"style": "outer", "color": "#D4AF37", "thickness": 6},   // strip only
 "divider": {"color": "#D4AF37"}, "cam_w": 880, "gap": 8, "shadow": false,
 "accent": "#E8B21E",                 // borders/panels in news/spotlight/bigpip/gallery/fullbleed
 "force_cover": true,                 // always fill slots (crop) instead of blurred fill
 "vo_style": "bw" | "focus" | null,   // narration: black&white / one camera full-screen zoom-in
 "vo_focus_tile": 1, "vo_tag": "COMMENTARY", "cold_tag": "COMING UP...",
 "name_tags": true, "tag_size": 28, "tag_color": "#FFD000", "text_font": "Arial Black",
 "caption": {"style": "karaoke" | "box" | "pop", "position": "on" | "below" | "above",
             "font": "Arial Black", "size": 56, "color": "#FFFFFF", "highlight": "#FFE600",
             "outline": "#000000", "outline_w": 4, "shadow": 3, "upper": true, "max_words": 4,
             "box_color": "#000000", "box_pad": 14}
}
```
Caption styles: **karaoke** = line, bolne wala word highlight · **box** = line ke peeche solid box ·
**pop** = ek waqt mein ek bara word (bounce ke saath).

Naya template (student): `python3 tools/new_template.py "name" --from T02 --set key=value ... [--bg pic.jpg] --project <p>`
→ `templates/S01-name/` + `preview.jpg` ban jata hai (S = student; git pull se kabhi nahi takrata, gitignored).
Claude: student jo kahe ("captions neeche", "lal frame", "apni photo background") use `--set` fields mein badlo,
preview khud dekho, student ko dikhao. Built-in T/B templates kabhi edit mat karo.
Bilkul naya structure chahiye to `tools/layouts.py` mein nayi family function likho aur `FAMILIES` mein add karo.
