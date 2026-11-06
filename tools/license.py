#!/usr/bin/env python3
"""Court Studio license — one key = one PC. Key teacher deta hai.

  python3 tools/license.py activate CS-XXXX-XXXX-XXXX     # pehli dafa (is PC se jud jati hai)
  python3 tools/license.py status

Key ke baghair library search aur studio ke tools nahi chalte. Doosre PC pe wahi key = "doosra PC registered hai".
Naya PC liya → teacher se "reset" karwao, phir yahan activate.
Saved in ~/.court-studio/license.json (sirf is PC pe). Internet har ~12 ghante check, 3 din offline chal jata hai.
"""
import hashlib, json, os, platform, subprocess, sys, time, urllib.error, urllib.request, uuid

SERVER = os.environ.get('COURT_LICENSE_SERVER', 'https://court-studio-license.REPLACE.workers.dev')
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
    elif a[:1] == ['status']:
        d = _load(); print('key:', d.get('key', '—'), '| this PC:', 'yes' if d.get('device') == device_id() else 'no',
                           '| last ok:', time.ctime(d['ok_at']) if d.get('ok_at') else '—'); require(); print('✅ license ok')
    else: sys.exit(__doc__)
