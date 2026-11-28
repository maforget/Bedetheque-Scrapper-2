''' Fetcher: which URLs are fetched, and when the browser fallback is used. '''
import contextlib
import io
import json
import os
import time
import urllib.request

from testlib import check, finish
from fetcherlib import (SERIES_URL, FakeBrowser, cookie, http_error, load_fetcher,
                        temp_data_dir)

temp_data_dir()
m = load_fetcher()

print('--- only https://*.bedetheque.com is allowed (S1)')
for url in ['file:///C:/Windows/win.ini', 'http://www.bedetheque.com/',
            'https://evil.com/', 'https://bedetheque.com.evil.com/',
            'https://evilbedetheque.com/', 'ftp://www.bedetheque.com/', '', 'not a url',
            'https://[bad/']:
    check('refused  %r' % url, m.is_allowed(url), False)
for url in ['https://www.bedetheque.com/serie-1.html', 'https://bedetheque.com/',
            'https://WWW.Bedetheque.COM/x']:
    check('allowed  %r' % url, m.is_allowed(url), True)


def refused(call):
    try:
        call()
        return False
    except ValueError:
        return True


check('Daemon.fetch refuses file://', refused(lambda: m.Daemon().fetch('file:///C:/x')), True)
check('BrowserFetcher.fetch refuses other hosts',
      refused(lambda: m.BrowserFetcher().fetch('https://evil.com/')), True)
check('BrowserFetcher._solve refuses other hosts',
      refused(lambda: m.BrowserFetcher()._solve('https://evil.com/')), True)
err = io.StringIO()
with contextlib.redirect_stderr(err):
    code = m.main_cloudscraper('https://evil.com/')
check('cloudscraper mode refuses other hosts', (code, 'Refused' in err.getvalue()), (2, True))

handler = m._AllowedRedirects()
req = urllib.request.Request(SERIES_URL)
try:
    handler.redirect_request(req, io.BytesIO(), 302, 'Found', {}, 'https://evil.com/')
    check('redirect off-site refused', False)
except urllib.error.HTTPError:
    check('redirect off-site refused', True)
check('redirect inside bedetheque followed',
      handler.redirect_request(req, io.BytesIO(), 302, 'Found', {},
                               'https://www.bedetheque.com/y.html').full_url,
      'https://www.bedetheque.com/y.html')


def daemon_with(browser, *responses):
    '''A Daemon whose plain HTTP answers come from responses (HTML strings
    or HTTPErrors, in order) and whose browser is browser.'''
    d = m.Daemon()
    d._browser = browser
    answers = list(responses)
    d.requests = []

    def read(opener, url):
        d.requests.append(opener.addheaders)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer, url
    d._read_html = read
    return d


def fetch(d, url=SERIES_URL):
    try:
        return d.fetch(url)
    except Exception as exc:
        return exc


print('--- a plain 403/503 keeps the old behaviour (B1)')
for code in (403, 503):
    b = FakeBrowser()
    d = daemon_with(b, http_error(SERIES_URL, code))
    result = fetch(d)
    check('plain %d is returned as an error' % code, getattr(result, 'code', None), code)
    check('plain %d does not use the browser' % code, b.calls, [])

d = daemon_with(FakeBrowser(), http_error(SERIES_URL, 403))
d._jar.set_cookie(m._jar_cookie(cookie('csrf_cookie_bel')))
d._jar.set_cookie(m._jar_cookie(cookie('cf_clearance')))
fetch(d)
check('403 drops the CSRF cookie but keeps cf_clearance',
      sorted(c.name for c in d._jar), ['cf_clearance'])

print('--- a Cloudflare challenge goes through the browser')
ua = 'Mozilla/5.0 Test Edg/158.0'
b = FakeBrowser(html='<html>through browser</html>', clearance=(ua, cookie('cf_clearance', 'abc')))
d = daemon_with(b, http_error(SERIES_URL, 403, {'cf-mitigated': 'challenge'}), '<html>plain</html>')
check('challenged page comes from the browser', fetch(d), '<html>through browser</html>')
check('browser asked for the clearance with the page (B5)', b.calls, [(SERIES_URL, True)])
check('clearance adopted into the cookie jar',
      [(c.name, c.value) for c in d._jar], [('cf_clearance', 'abc')])
check('next request is plain HTTP', fetch(d), '<html>plain</html>')
check('...with the browser\'s User-Agent', dict(d.requests[-1])['User-Agent'], ua)
check('browser not used again', len(b.calls), 1)

saved = json.load(open(m._clearance_file(), encoding='utf-8'))
check('only cf_clearance is saved (review point 3)', sorted(saved), ['cookie', 'user_agent'])
check('saved cookie is cf_clearance', saved['cookie']['name'], 'cf_clearance')

print('--- still challenged with a fresh clearance: stay on the browser')
b = FakeBrowser(html='<html>b</html>', clearance=(ua, cookie('cf_clearance')))
d = daemon_with(b, http_error(SERIES_URL, 403, {'cf-mitigated': 'challenge'}),
                http_error(SERIES_URL, 403, {'cf-mitigated': 'challenge'}))
fetch(d)
fetch(d)
check('second challenge switches to the browser for a while',
      d._browser_until > time.time() + m.BROWSER_STICKY_SECS - 5, True)
check('while sticky, pages come from the browser without plain HTTP',
      (fetch(d), len(d.requests)), ('<html>b</html>', 2))

print('--- browser fallback failure is reported with the HTTP error')
d = daemon_with(FakeBrowser(error=RuntimeError('no browser')),
                http_error(SERIES_URL, 403, {'cf-mitigated': 'challenge'}))
result = fetch(d)
check('error names the challenge and the browser failure',
      'Cloudflare challenge' in str(result) and 'no browser' in str(result), True)

print('--- close_browser closes the browser')
b = FakeBrowser()
d = daemon_with(b)
d.close()
check('Daemon.close closes the browser', b.closed, 1)

finish()
