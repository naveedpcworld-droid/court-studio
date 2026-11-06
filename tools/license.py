#!/usr/bin/env python3
"""Court Studio license — one key = one PC. Key teacher deta hai.

  python3 tools/license.py activate CS-XXXX-XXXX-XXXX     # pehli dafa (is PC se jud jati hai)
  python3 tools/license.py status
  python3 tools/license.py library      # library (links + transcripts) dobara download / update

Key ke baghair library search aur studio ke tools nahi chalte. Doosre PC pe wahi key = "doosra PC registered hai".
Naya PC liya → teacher se "reset" karwao, phir yahan activate.
Saved in ~/.court-studio/license.json (sirf is PC pe). Internet har ~12 ghante check, 3 din offline chal jata hai.
"""
import hashlib, json, os, platform, subprocess, sys, time, urllib.error, urllib.request, uuid

SERVER = os.environ.get('COURT_LICENSE_SERVER', 'https://court-studio-license.naveedpcworld.workers.dev')
HOME = os.path.join(os.path.expanduser('~'), '.court-studio'); FILE = os.path.join(HOME, 'license.json')
RECHECK = 12 * 3600; OFFLINE_GRACE = 3 * 86400


def _machine_id():
    s = platform.system()
    try:
        if s == 'Darwin':
            out = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], capture_output=True, text=True).stdout
            for ln in out.splitlines():
                if 'IOPlatformUUID' in ln: return ln.split('"')[-2]
        elif s == 'Windows':
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography', 0, winreg.KEY_READ | 0x0100)
            return winreg.QueryValueEx(k, 'MachineGuid')[0]
        else:
            for p in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
                if os.path.exists(p): return open(p).read().strip()
    except Exception:
        pass
    return f'{uuid.getnode():x}'


def device_id():
    return hashlib.sha256(f'court-studio|{_machine_id()}|{platform.system()}'.encode()).hexdigest()[:40]


def _load():
    try: return json.load(open(FILE))
    except Exception: return {}


def _save(d):
    os.makedirs(HOME, exist_ok=True); json.dump(d, open(FILE, 'w'), indent=1)


def _call(path, key):
    body = json.dumps({'key': key, 'device': device_id(), 'host': platform.node()[:60]}).encode()
    req = urllib.request.Request(SERVER + path, data=body, method='POST',
                                 headers={'content-type': 'application/json', 'user-agent': 'court-studio/1'})
    try:
        return json.load(urllib.request.urlopen(req, timeout=20))
    except urllib.error.HTTPError as e:
        try: return json.load(e)
        except Exception: return {'ok': False, 'error': f'server error {e.code}'}


def activate(key):
    r = _call('/activate', key.strip().upper())
    if not r.get('ok'): sys.exit('❌ ' + r.get('error', 'activation failed'))
    _save({'key': key.strip().upper(), 'device': device_id(), 'ok_at': time.time(), 'name': r.get('name', '')})
    print('✅ activated on this PC' + (f" ({r['name']})" if r.get('name') else '') + '. Ab sab tools chalenge.')
    sync_library()


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _post_raw(path, payload):
    req = urllib.request.Request(SERVER + path, data=json.dumps(payload).encode(), method='POST',
                                 headers={'content-type': 'application/json', 'user-agent': 'court-studio/1'})
    return urllib.request.urlopen(req, timeout=120)


def sync_library(force=False):
    """download links + transcripts library from the teacher's server (only with a valid key on this PC)."""
    d = _load()
    if not d.get('key'): sys.exit('🔑 Pehle license activate karo.')
    who = {'key': d['key'], 'device': device_id()}
    try:
        man = json.load(_post_raw('/library', dict(who, file='manifest.json')))
    except urllib.error.HTTPError as e:
        sys.exit(f'❌ library download refused ({e.code}). License check karo: python3 tools/license.py status')
    vf = os.path.join(ROOT, 'library', '.version')
    have = open(vf).read().strip() if os.path.exists(vf) else ''
    todo = [f for f in man['files'] if force or have != man['version'] or not os.path.exists(os.path.join(ROOT, f['path']))]
    if not todo: return
    total = sum(f['size'] for f in todo); done = 0
    print(f'📥 library download: {len(todo)} files, {total / 1e6:.0f} MB (sirf links + transcripts, ek dafa) ...', flush=True)
    for f in todo:
        dst = os.path.join(ROOT, f['path']); os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        h = hashlib.sha256(); tmp = dst + '.part'
        for attempt in range(4):
            try:
                with _post_raw('/library', dict(who, file=f['obj'])) as r, open(tmp, 'wb') as o:
                    while True:
                        b = r.read(1 << 20)
                        if not b: break
                        o.write(b); h.update(b)
                break
            except Exception as e:
                h = hashlib.sha256(); time.sleep(3 * (attempt + 1))
                if attempt == 3: sys.exit(f'❌ download failed: {f["path"]} ({e})')
        if h.hexdigest() != f['sha256']: sys.exit(f'❌ corrupt download: {f["path"]} — dobara chalao')
        os.replace(tmp, dst); done += f['size']
        if f.get('unpack'):
            import tarfile
            with tarfile.open(dst) as t:
                try: t.extractall(ROOT, filter='data')
                except TypeError: t.extractall(ROOT)
            os.remove(dst)
        print(f'   {done * 100 // total:3d}%  {f["path"]}', flush=True)
    open(vf, 'w').write(man['version'])
    print('✅ library ready.')


def require():
    """call at the start of every tool. Exits with a clear message if there is no valid key for THIS PC."""
    if 'REPLACE' in SERVER: return                       # license server not deployed yet -> no check
    d = _load()
    if not d.get('key'):
        sys.exit('🔑 License key chahiye. Teacher se key lo, phir:\n   python3 tools/license.py activate CS-XXXX-XXXX-XXXX\n'
                 '(Claude se bhi keh sakte ho: "meri license key ye hai: ...")')
    if d.get('device') != device_id():
        sys.exit('🔑 Ye license kisi aur PC ka hai. Is PC pe activate karo: python3 tools/license.py activate <KEY>')
    if time.time() - d.get('ok_at', 0) < RECHECK: return
    try:
        r = _call('/check', d['key'])
    except Exception:                                   # no internet -> short grace period
        if time.time() - d.get('ok_at', 0) < OFFLINE_GRACE: return
        sys.exit('🔑 License check ke liye internet chahiye (3 din se offline).')
    if not r.get('ok'):
        sys.exit('❌ ' + r.get('error', 'license refused'))
    d['ok_at'] = time.time(); _save(d)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'activate': activate(a[1])
    elif a[:1] == ['library']: require(); sync_library(force='--force' in a)
    elif a[:1] == ['status']:
        d = _load(); print('key:', d.get('key', '—'), '| this PC:', 'yes' if d.get('device') == device_id() else 'no',
                           '| last ok:', time.ctime(d['ok_at']) if d.get('ok_at') else '—'); require(); print('✅ license ok')
    else: sys.exit(__doc__)
