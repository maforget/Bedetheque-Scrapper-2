''' Fetcher: BrowserFetcher logic with a fake browser connection (no browser
is started). Covers B3, B4, B5, B6, S2 and the hand-off message. '''
import http.server
import json
import os
import threading
import time

from testlib import check, finish
from fetcherlib import SERIES_URL, cookie, load_fetcher, temp_data_dir

temp_data_dir()
m = load_fetcher()

print('--- find_browser')
try:
    m.find_browser(r'C:\nope\browser.exe')
    check('missing --browser path refused', False)
except RuntimeError as exc:
    check('missing --browser path refused', 'C:\\nope\\browser.exe' in str(exc))
here = os.path.abspath(__file__)
check('existing --browser path used as is', m.find_browser(here), here)

print('--- DevTools port from DevToolsActivePort, no proxy (S2, B3)')


class DevTools(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps([{'type': 'service_worker', 'webSocketDebuggerUrl': 'ws://x/sw'},
                           {'type': 'page', 'webSocketDebuggerUrl': 'ws://127.0.0.1/page'}])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


server = http.server.HTTPServer(('127.0.0.1', 0), DevTools)
threading.Thread(target=server.serve_forever, daemon=True).start()
port_file = os.path.join(m._profile_dir(), 'DevToolsActivePort')
check('no port file yet: not ready', m.BrowserFetcher._page_ws_url(port_file), None)
with open(port_file, 'w') as fh:
    fh.write('%d\n/devtools/browser/abc\n' % server.server_port)
for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
    os.environ[k] = 'http://127.0.0.1:9'          # a proxy that does not answer
check('page found through a dead system proxy', m.BrowserFetcher._page_ws_url(port_file),
      'ws://127.0.0.1/page')
for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
    del os.environ[k]
with open(port_file, 'w') as fh:
    fh.write('garbage\n')
check('unreadable port file: not ready', m.BrowserFetcher._page_ws_url(port_file), None)
server.shutdown()


class FakeWS(object):
    '''A DevTools connection. answer(msg) returns the reply dict, or raises.'''

    def __init__(self, answer):
        self.answer = answer
        self.sent = []
        self.pending = []

    def send(self, text):
        msg = json.loads(text)
        self.sent.append(msg['method'])
        self.pending.append(msg)

    def recv(self, timeout=None):
        msg = self.pending.pop(0)
        reply = self.answer(msg)
        reply['id'] = msg['id']
        return json.dumps(reply)

    def close(self):
        pass


def browser_with(answer):
    b = m.BrowserFetcher()
    b._ws = FakeWS(answer)
    return b


print('--- error kinds (B6)')


def raises(call, kind):
    try:
        call()
        return None
    except Exception as exc:
        return type(exc).__name__ if isinstance(exc, kind) else 'wrong: %r' % exc


def timeout(msg):
    raise TimeoutError()


def closed(msg):
    raise ConnectionResetError('closed')


check('no answer in time: BrowserError',
      raises(lambda: browser_with(timeout)._call('X', timeout=1), m.BrowserError), 'BrowserError')
check('connection lost: BrowserError',
      raises(lambda: browser_with(closed)._call('X'), m.BrowserError), 'BrowserError')
check('error answer: PageError',
      raises(lambda: browser_with(lambda msg: {'error': {'message': 'no'}})._call('X'),
             m.PageError), 'PageError')
check('script exception: PageError', raises(
    lambda: browser_with(lambda msg: {'result': {'exceptionDetails': {
        'text': 'Uncaught', 'exception': {'description': 'TypeError: Failed to fetch'}}}}
    )._eval('x'), m.PageError), 'PageError')
check('no connection: BrowserError',
      raises(lambda: m.BrowserFetcher()._call('X'), m.BrowserError), 'BrowserError')


class FakeProc(object):
    pid = 4242

    def __init__(self, exit_code=None):
        self.returncode = exit_code

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def terminate(self):
        self.returncode = 1

    kill = terminate

    def close(self):
        pass


def page(status=200, cf='', html='<html>page</html>'):
    return {'result': {'result': {'value': json.dumps(
        {'status': status, 'cf': cf, 'html': html})}}}


def cleared():
    return {'result': {'result': {'value': json.dumps(
        {'host': 'www.bedetheque.com', 'ready': 'complete', 'challenge': False})}}}


def running_browser(on_eval, cookies=()):
    '''A BrowserFetcher that looks started: fake process and connection.'''
    def answer(msg):
        if msg['method'] == 'Runtime.evaluate':
            return on_eval(msg['params']['expression'])
        if msg['method'] == 'Network.getCookies':
            return {'result': {'cookies': list(cookies)}}
        return {'result': {}}
    b = browser_with(answer)
    b._proc = FakeProc()
    b._ua = 'Mozilla/5.0 Test'
    return b


print('--- fetch keeps the browser on page errors, restarts on connection errors (B6)')
state = {'fail': True}


def flaky_fetch(expr):
    if 'document.readyState' in expr:
        return cleared()
    if state['fail']:
        state['fail'] = False
        return {'result': {'exceptionDetails': {'text': 'TypeError: Failed to fetch'}}}
    return page()


b = running_browser(flaky_fetch)
proc = b._proc
check('page error raised', raises(lambda: b.fetch(SERIES_URL), m.PageError), 'PageError')
check('browser kept after a page error', b._proc is proc and b._ws is not None, True)
check('next fetch uses the same browser', b.fetch(SERIES_URL)[0], '<html>page</html>')


def lost(expr):
    raise ConnectionResetError('gone')


b = running_browser(lost)
b._ws.recv = lambda timeout=None: (_ for _ in ()).throw(ConnectionResetError('gone'))
check('connection error raised', raises(lambda: b.fetch(SERIES_URL), m.BrowserError),
      'BrowserError')
check('browser closed after a connection error', (b._proc, b._ws), (None, None))

print('--- clearance read with the page, under the same lock (B5)')
b = running_browser(lambda expr: cleared() if 'readyState' in expr else page(),
                    cookies=[cookie('csrf_cookie_bel'), cookie('cf_clearance', 'zzz')])
html, clearance = b.fetch(SERIES_URL, want_clearance=True)
check('page and clearance together', (html, clearance[0], clearance[1]['value']),
      ('<html>page</html>', 'Mozilla/5.0 Test', 'zzz'))
check('no clearance asked: none returned', b.fetch(SERIES_URL)[1], None)
b = running_browser(lambda expr: cleared() if 'readyState' in expr else page(),
                    cookies=[cookie('csrf_cookie_bel')])
check('no cf_clearance in the browser: None', b.fetch(SERIES_URL, want_clearance=True)[1], None)
b = running_browser(lambda expr: cleared() if 'readyState' in expr else page(status=404))
check('HTTP error from the browser page', raises(lambda: b.fetch(SERIES_URL), RuntimeError),
      'RuntimeError')

print('--- start: hidden desktop, its fallback, and the hand-off message (B4)')
started = []


class StubJob(object):
    '''Records how the browser would be started; exits at once like a
    browser handing over to another instance of the same profile.'''

    def __init__(self, args, desktop=None):
        started.append((desktop, [a for a in args if a.startswith('--remote-debugging')]))
        self.pid = 1
        self.returncode = 21

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def terminate(self):
        pass

    kill = terminate

    def close(self):
        pass


real_job = m._JobProcess
m._JobProcess = StubJob
b = m.BrowserFetcher(browser_path=here)
with b._lock:
    msg = raises(lambda: b._start(), m.BrowserBusy)
check('first start is on the hidden desktop', started[0][0], m.HIDDEN_DESKTOP)
check('browser picks its own DevTools port (S2)', started[0][1], ['--remote-debugging-port=0'])
check('exit right after start: BrowserBusy', msg, 'BrowserBusy')
try:
    with b._lock:
        b._start()
except m.BrowserBusy as exc:
    check('message explains the profile hand-off', 'another browser process' in str(exc), True)


class NoDesktop(StubJob):
    def __init__(self, args, desktop=None):
        if desktop:
            raise m.DesktopUnavailable(5, 'simulated')
        StubJob.__init__(self, args, desktop)


del started[:]
m._JobProcess = NoDesktop
b = m.BrowserFetcher(browser_path=here)
with b._lock:
    raises(lambda: b._start(), m.BrowserBusy)
check('no hidden desktop: started visible, on purpose', (started[0][0], b._visible), (None, True))
m._JobProcess = real_job

print('--- a stale DevToolsActivePort is removed before starting')
with open(port_file, 'w') as fh:
    fh.write('1\n')
m._JobProcess = StubJob
b = m.BrowserFetcher(browser_path=here)
with b._lock:
    raises(lambda: b._start(), m.BrowserBusy)
m._JobProcess = real_job
check('stale port file deleted', os.path.exists(port_file), False)

finish()
