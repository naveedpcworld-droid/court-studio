# Setup (ek dafa) — Claude ye checks khud chalaye

```bash
python3 --version                    # 3.9+
ffmpeg -hide_banner -filters | grep -E " ass "      # 'ass' filter hona chahiye (libass)
yt-dlp --version
python3 -c "import faster_whisper, numpy, PIL; print('ok')"
edge-tts --version                   # 7.3 ya naya
```

Jo missing ho:

**Mac**
```bash
brew install ffmpeg yt-dlp
pip3 install -U faster-whisper edge-tts pillow numpy
```
**Windows** (PowerShell)
```bash
winget install Gyan.FFmpeg
winget install yt-dlp.yt-dlp
pip install -U faster-whisper edge-tts pillow numpy
```

Notes
- edge-tts purana ho to voice HTTP 403 deta hai → `pip3 install -U edge-tts`.
- Pehli transcription par whisper model (~500MB) download hota hai.
- Mac pe render hardware encoder (videotoolbox) se fast hai; Windows/Linux pe libx264.
- Fonts: Arial Black + Impact (Mac/Windows dono mein hote hain).
- YouTube "Sign in to confirm you're not a bot" / 429 de to thori der baad, ya `yt-dlp --cookies-from-browser chrome`.
