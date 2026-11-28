''' Helpers for the fetcher tests (CPython 3). '''
import atexit
import importlib.util
import io
import os
import shutil
import tempfile
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCHER_PY = os.path.join(ROOT, 'tools', 'BedethequeFetcher.py')
FETCHER_EXE = os.path.join(ROOT, 'src', 'BedethequeFetcher.exe')
SERIES_URL = 'https://www.bedetheque.com/serie-56465-BD-Une-soeur.html'
REAL_DATA = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BedethequeScraper2')


def temp_data_dir(copy_profile=False):
    '''Points LOCALAPPDATA at a new empty temp folder, so the fetcher never
    touches the real clearance, log or browser profile. With copy_profile,
    starts from a copy of the real browser profile (live tests: it usually
    holds a valid cf_clearance, so no challenge needs a click).'''
    folder = tempfile.mkdtemp(prefix='BD2Test-')
    atexit.register(shutil.rmtree, folder, True)  # deleted when the test ends
    if copy_profile:
        src = os.path.join(REAL_DATA, 'browser_profile')
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(folder, 'BedethequeScraper2', 'browser_profile'),
                            ignore=shutil.ignore_patterns('DevToolsActivePort', 'Singleton*',
                                                          'lockfile'))
    os.environ['LOCALAPPDATA'] = folder
    return folder


def load_fetcher():
    '''A fresh copy of tools/BedethequeFetcher.py as a module.'''
    spec = importlib.util.spec_from_file_location('BedethequeFetcher', FETCHER_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Headers(dict):
    '''Case-insensitive response headers, enough for HTTPError.headers.get.'''

    def __init__(self, values=None):
        super().__init__((k.lower(), v) for k, v in (values or {}).items())

    def get(self, key, default=None):
        return dict.get(self, key.lower(), default)


def http_error(url, code, headers=None):
    return urllib.error.HTTPError(url, code, 'test', Headers(headers), io.BytesIO())


def cookie(name, value='v', expires=-1, domain='.bedetheque.com'):
    '''A cookie as DevTools' Network.getCookies returns it.'''
    return {'name': name, 'value': value, 'domain': domain, 'path': '/',
            'expires': expires, 'secure': True, 'httpOnly': True}


class FakeBrowser(object):
    '''Stands in for BrowserFetcher: records calls, returns canned pages.'''

    def __init__(self, html='<html>browser page</html>', clearance=None, error=None):
        self.html = html
        self.clearance = clearance
        self.error = error
        self.calls = []
        self.closed = 0

    def fetch(self, url, want_clearance=False):
        self.calls.append((url, want_clearance))
        if self.error:
            raise self.error
        return self.html, (self.clearance if want_clearance else None)

    def close(self):
        self.closed += 1
