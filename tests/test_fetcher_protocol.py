''' Fetcher: the local TCP protocol (one JSON object per line). '''
import json
import socket
import threading

from testlib import check, finish
from fetcherlib import SERIES_URL, load_fetcher, temp_data_dir

temp_data_dir()
m = load_fetcher()


class FakeDaemon(object):
    def __init__(self):
        self.fetched = []
        self.closed = 0

    def fetch(self, url):
        self.fetched.append(url)
        if 'boom' in url:
            raise RuntimeError('fetch failed')
        return '<html>%s</html>' % url

    def close(self):
        self.closed += 1


fake = FakeDaemon()
m._daemon = fake


class Exited(BaseException):
    '''Raised instead of exiting; like os._exit, not caught by except Exception.'''


def fake_exit(code):
    raise Exited(code)


m.os._exit = fake_exit


def exchange(raw):
    '''Sends raw bytes to _handle_client and returns (reply, exit code).'''
    server, client = socket.socketpair()
    result = {}

    def serve():
        try:
            m._handle_client(server, ('127.0.0.1', 1))
        except Exited as e:
            result['exit'] = e.args[0]
            server.close()
    t = threading.Thread(target=serve)
    t.start()
    client.sendall(raw)
    data = b''
    while not data.endswith(b'\n'):
        chunk = client.recv(65536)
        if not chunk:
            break
        data += chunk
    client.close()
    t.join(5)
    reply = json.loads(data) if data.strip() else None
    return reply, result.get('exit')


def send(obj):
    return exchange((json.dumps(obj) + '\n').encode('utf-8'))


print('--- page requests')
reply, _ = send({'url': SERIES_URL})
check('page returned', (reply['url'], reply['html']), (SERIES_URL, '<html>%s</html>' % SERIES_URL))
reply, _ = send({'url': 'https://www.bedetheque.com/boom'})
check('fetch error returned as error', reply['error'], 'fetch failed')

print('--- refused and malformed requests (S1)')
before = len(fake.fetched)
for url in ['file:///C:/Windows/win.ini', 'https://evil.com/', 'http://www.bedetheque.com/']:
    reply, _ = send({'url': url})
    check('refused %s' % url, reply['error'].startswith('Refused'), True)
check('refused URLs never reach the fetcher', len(fake.fetched), before)
check('bad JSON', exchange(b'{not json\n')[0], {'error': 'Invalid JSON request'})
check('JSON that is not an object', send(['https://www.bedetheque.com/'])[0],
      {'error': 'Invalid JSON request'})
check('missing url', send({'nope': 1})[0], {'error': "Missing 'url' in request"})
check('url not a string', send({'url': 42})[0], {'error': "Missing 'url' in request"})
check('an HTTP request line is not JSON (browser pages)',
      exchange(b'GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n')[0], {'error': 'Invalid JSON request'})

print('--- commands')
reply, code = send({'command': 'close_browser'})
check('close_browser answers ok', reply, {'ok': True})
check('close_browser closes the browser', fake.closed, 1)
check('close_browser does not exit', code, None)
reply, code = send({'command': 'shutdown'})
check('shutdown answers ok', reply, {'ok': True})
check('shutdown closes the browser first', fake.closed, 2)
check('shutdown exits the daemon with code 0', code, 0)

finish()
