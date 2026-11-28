''' Fetcher, live: bedetheque.com, the system browser and the built exe.
Starts from a copy of your browser profile; the real one is not touched.
If Cloudflare wants a click, a browser window opens: click the checkbox. '''
import ctypes
import json
import os
import socket
import subprocess
import threading
import time
from ctypes import wintypes

from testlib import check, finish
from fetcherlib import FETCHER_EXE, SERIES_URL, load_fetcher, temp_data_dir

WORK = temp_data_dir(copy_profile=True)
m = load_fetcher()
DATA = os.path.join(WORK, 'BedethequeScraper2')
u32 = ctypes.WinDLL('user32')


def browser_pids():
    '''PIDs of browser processes using this test's profile.'''
    out = subprocess.run(
        ['powershell', '-NoProfile', '-Command',
         "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*%s*' -and "
         "$_.ProcessId -ne $PID -and $_.Name -notlike 'python*' -and "
         "$_.Name -notlike 'Bedetheque*' } | "
         "ForEach-Object { $_.ProcessId }" % WORK],
        capture_output=True, text=True).stdout.split()
    return {int(p) for p in out}


def wait_until(pred, secs=15):
    end = time.time() + secs
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.2)
    return pred()


class ForegroundLog(object):
    '''Records the PIDs owning the foreground window while it runs.'''

    def __enter__(self):
        self.pids, self._stop = set(), False

        def poll():
            while not self._stop:
                owner = wintypes.DWORD()
                u32.GetWindowThreadProcessId(u32.GetForegroundWindow(), ctypes.byref(owner))
                self.pids.add(owner.value)
                time.sleep(0.02)
        self._t = threading.Thread(target=poll, daemon=True)
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop = True
        self._t.join()


print('--- a challenged page goes through the hidden browser')
d = m.Daemon()
with ForegroundLog() as fg:
    t0 = time.time()
    html = d.fetch(SERIES_URL)
    took = time.time() - t0
    pids = browser_pids()
check('page fetched (%.1f s)' % took, 'Une s' in html, True)
check('browser running', bool(pids), True)
check('browser window never had the foreground', fg.pids & pids, set())
port_file = os.path.join(DATA, 'browser_profile', 'DevToolsActivePort')
check('browser chose its DevTools port itself (S2)', os.path.isfile(port_file), True)

saved = json.load(open(os.path.join(DATA, 'clearance.json'), encoding='utf-8'))
check('only cf_clearance saved', (sorted(saved), saved['cookie']['name']),
      (['cookie', 'user_agent'], 'cf_clearance'))
check('next page by plain HTTP', 'Une s' in d.fetch(SERIES_URL), True)

print('--- a page script error keeps the browser (B6)')
b = d._browser
before = b._proc.pid
try:
    with b._lock:
        b._eval("throw new TypeError('Failed to fetch')")
except m.PageError:
    pass
check('same browser after a page error', b._alive() and b._proc.pid == before, True)
d.close()
check('close_browser ends every browser process', wait_until(lambda: not browser_pids()), True)

print('--- after a restart, only the saved cf_clearance is needed (B2)')
d = m.Daemon()
check('jar on start', sorted(c.name for c in d._jar), ['cf_clearance'])
check('page by plain HTTP, no browser', ('Une s' in d.fetch(SERIES_URL), d._browser._proc),
      (True, None))
d.close()

print('--- the built exe')
if not os.path.isfile(FETCHER_EXE):
    check('src/BedethequeFetcher.exe exists (run: python build_fetcher.py)', False)
    finish()
os.remove(os.path.join(DATA, 'clearance.json'))  # so the exe has to use the browser


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def send(port, obj, timeout=120):
    s = socket.create_connection(('127.0.0.1', port), timeout=timeout)
    s.sendall((json.dumps(obj) + '\n').encode())
    data = b''
    while not data.endswith(b'\n'):
        chunk = s.recv(65536)
        if not chunk:
            break
        data += chunk
    s.close()
    return json.loads(data) if data.strip() else None


def start_exe():
    port = free_port()
    proc = subprocess.Popen([FETCHER_EXE, '--port', str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    wait_until(lambda: socket.socket().connect_ex(('127.0.0.1', port)) == 0, 20)
    return proc, port


proc, port = start_exe()
reply = send(port, {'url': SERIES_URL})
check('exe fetches through the browser', 'Une s' in (reply or {}).get('html', ''), True)
check('browser running for the exe', bool(browser_pids()), True)
check('exe refuses file://', send(port, {'url': 'file:///C:/Windows/win.ini'})['error'][:7],
      'Refused')
t0 = time.time()
check('shutdown answered', send(port, {'command': 'shutdown'}), {'ok': True})
check('exe exits after shutdown', wait_until(lambda: proc.poll() is not None, 10), True)
check('browser gone after shutdown (%.1f s)' % (time.time() - t0),
      wait_until(lambda: not browser_pids()), True)

print('--- a killed exe takes its browser with it (S3)')
os.remove(os.path.join(DATA, 'clearance.json'))
proc, port = start_exe()
send(port, {'url': SERIES_URL})
check('browser running', bool(browser_pids()), True)
subprocess.run(['taskkill', '/PID', str(proc.pid), '/F'], capture_output=True)  # bootloader
for pid in subprocess.run(
        ['powershell', '-NoProfile', '-Command',
         "Get-CimInstance Win32_Process -Filter \"Name='BedethequeFetcher.exe'\" | "
         "Where-Object { $_.CommandLine -like '*--port %d*' } | ForEach-Object { $_.ProcessId }"
         % port], capture_output=True, text=True).stdout.split():
    subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
check('browser gone after End task on the exe', wait_until(lambda: not browser_pids()), True)

finish()
