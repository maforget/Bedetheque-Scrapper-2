import os
import sys

# When run via the dev-only fallback, this script lives in the published
# plugin folder alongside other files meant for IronPython 2.7 (e.g. a
# types.py shim defining py2-only names like `long`). Python auto-prepends
# this script's own directory to sys.path, so those same-named files can
# shadow real stdlib modules (types, and anything that imports it - re,
# enum, logging, ...) before any external module gets a chance to import.
# Strip it before importing anything else that could trigger that chain.
#
# Skip this entirely when frozen (running as the built exe): there,
# __file__'s directory is PyInstaller's extraction folder (_MEIPASS),
# which is the one sys.path entry the exe needs to find its own bundled
# modules - such as the bundled scraper library - so it must stay in sys.path.
if not getattr(sys, "frozen", False):
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _SCRIPT_DIR]

# print("sys.path:", sys.path, file=sys.stderr)

import argparse
import ctypes
import http.client
import http.cookiejar
import json
import logging
import logging.handlers
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request
from ctypes import wintypes
from urllib.parse import urlsplit

"""
Small daemon that fetches bedetheque.com pages on demand.

It keeps one opener + cookie jar alive for the whole run and renews the
csrf_cookie_bel token automatically (on expiry, or when the server rejects
it). Clients talk to it over a local TCP socket, one JSON object per line:

    client > daemon:  {"url": "https://..."}\n
    daemon > client:  {"url": "...", "html": "..."}\n   or   {"error": "..."}\n
    client > daemon:  {"command": "close_browser"}\n
    daemon > client:  {"ok": true}\n
    client > daemon:  {"command": "shutdown"}\n
    daemon > client:  {"ok": true}\n   then the daemon exits

When Cloudflare answers with a challenge, the page is fetched through the
system browser instead (see BrowserFetcher), and the browser's cf_clearance
cookie is reused for later plain HTTP requests.

Usage:
    python BedethequeFetcher.py [--host 127.0.0.1] [--port 56789]
                                [--browser "C:\\path\\to\\msedge.exe"]
"""

BASE_URL = "https://www.bedetheque.com"
ALLOWED_DOMAIN = "bedetheque.com"
TIMEOUT = 30

COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "bedetheque_cookies.txt")

HEADERS = [
    ("User-Agent",
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
     "AppleWebKit/537.36 (KHTML, like Gecko) "
     "Chrome/124.0.0.0 Safari/537.36"),
    ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ("Accept-Language", "en-US,en;q=0.5"),
    ("Connection", "keep-alive"),
    ("Upgrade-Insecure-Requests", "1"),
    ("Referer", BASE_URL + "/"),
]

# The only cookie taken from the browser and saved to disk. Everything else
# (CSRF token, session, a login made in the visible window) stays in the
# browser profile.
CLEARANCE_COOKIE = "cf_clearance"

BROWSER_IDLE_SECS = 60         # close the browser after this long without a fetch
BROWSER_QUIET_SECS = 20        # wait this long for an automatic challenge to clear
BROWSER_INTERACTIVE_SECS = 60  # then show the window and let the user solve it
BROWSER_STICKY_SECS = 900      # if urllib is rejected even with a fresh clearance,
                               # use the browser for this long
BROWSER_START_SECS = 20        # time allowed for the browser to open DevTools
HIDDEN_DESKTOP = "BedethequeScraper2"
_CHALLENGE_TITLE_JS = ("/just a moment|un instant|attention required|"
                       "checking your browser|verify you are human/i")

log = logging.getLogger("fetch_daemon")

# Local connections (DevTools) must never go through the system proxy.
_direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def is_allowed(url):
    """Only https pages of bedetheque.com may be fetched or opened."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return False
    return parts.scheme == "https" and (
        host == ALLOWED_DOMAIN or host.endswith("." + ALLOWED_DOMAIN))


class _AllowedRedirects(urllib.request.HTTPRedirectHandler):
    """Follow redirects only to allowed URLs."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed(newurl):
            raise urllib.error.HTTPError(
                newurl, code, "redirect to a non-bedetheque URL refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _load_jar():
    """Read the cookie jar from disk, or create an empty one."""
    jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
    if os.path.exists(COOKIE_FILE):
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
        except (OSError, http.client.HTTPException):
            jar.clear()
    return jar


def _build_opener(jar, user_agent=None):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _AllowedRedirects())
    headers = list(HEADERS)
    if user_agent:
        # cf_clearance is only valid for the User-Agent that earned it.
        headers = [(k, user_agent if k == "User-Agent" else v) for k, v in headers]
    opener.addheaders = headers
    return opener


# --- saved Cloudflare clearance ----------------------------------------------
def _data_dir():
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    path = os.path.join(base, "BedethequeScraper2")
    os.makedirs(path, exist_ok=True)
    return path


def _clearance_file():
    return os.path.join(_data_dir(), "clearance.json")


def _load_clearance():
    """(user_agent, cookie dict) of the saved, unexpired cf_clearance,
    else (None, None)."""
    try:
        with open(_clearance_file(), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None, None
    cookie = data.get("cookie")
    if cookie is None:
        # Older format: a list of all bedetheque cookies. Keep only the
        # clearance, and rewrite the file without the others.
        cookie = next((c for c in data.get("cookies", [])
                       if c.get("name") == CLEARANCE_COOKIE), None)
        if cookie is not None and data.get("user_agent"):
            _save_clearance(data["user_agent"], cookie)
    if (not cookie or cookie.get("name") != CLEARANCE_COOKIE
            or not data.get("user_agent")):
        return None, None
    if 0 < (cookie.get("expires") or -1) < time.time():
        return None, None
    return data["user_agent"], cookie


def _save_clearance(user_agent, cookie):
    """Write the clearance atomically (temp file + os.replace)."""
    path = _clearance_file()
    tmp = path + ".tmp"
    keep = {k: cookie.get(k) for k in
            ("name", "value", "domain", "path", "expires", "secure")}
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"user_agent": user_agent, "cookie": keep}, fh)
        os.replace(tmp, path)
    except OSError:
        log.warning("could not save %s", path)
        try:
            os.remove(tmp)
        except OSError:
            pass


def _jar_cookie(c):
    """http.cookiejar.Cookie from a DevTools cookie dict."""
    domain = c["domain"]
    expires = int(c["expires"]) if (c.get("expires") or -1) > 0 else None
    return http.cookiejar.Cookie(
        0, c["name"], c["value"], None, False, domain, True,
        domain.startswith("."), c.get("path") or "/", True, bool(c.get("secure")),
        expires, expires is None, None, None, {})


class Daemon:
    """Shared state for outgoing requests: cookie jar, opener, CSRF token.
    Guarded by a lock because clients are served on separate threads."""

    def __init__(self, browser_path=None):
        self._lock = threading.Lock()
        self._jar = _load_jar()
        self._ua, cookie = _load_clearance()
        if cookie:
            self._jar.set_cookie(_jar_cookie(cookie))
            log.info("loaded saved Cloudflare clearance")
        self._opener = _build_opener(self._jar, self._ua)
        self._browser = BrowserFetcher(browser_path)
        self._browser_until = 0.0  # use the browser directly until then
        self._fresh = False        # clearance adopted, not yet confirmed by urllib

    def _reset(self):
        """Drop the rejected CSRF token so the next fetch gets a fresh one.
        The Cloudflare clearance is kept. Caller holds the lock."""
        for c in list(self._jar):
            if c.name != CLEARANCE_COOKIE:
                self._jar.clear(c.domain, c.path, c.name)
        self._opener = _build_opener(self._jar, self._ua)

    def _adopt(self, user_agent, cookie):
        """Use the browser's cf_clearance (and its User-Agent) for plain HTTP
        requests, now and after restarts."""
        with self._lock:
            self._jar.set_cookie(_jar_cookie(cookie))
            self._ua = user_agent
            self._opener = _build_opener(self._jar, user_agent)
            self._fresh = True
        _save_clearance(user_agent, cookie)
        log.info("adopted Cloudflare clearance from the browser")

    def fetch(self, url):
        """Return the HTML of url. A Cloudflare challenge (cf-mitigated header)
        is retried through the system browser; a plain 403 only refreshes the
        CSRF token for the next request, as before."""
        if not is_allowed(url):
            raise ValueError("refused: only https://*.bedetheque.com URLs are fetched")
        with self._lock:
            use_browser = time.time() < self._browser_until
            opener = self._opener
        if use_browser:
            return self._browser.fetch(url)[0]
        try:
            html, _ = self._read_html(opener, url)
        except urllib.error.HTTPError as exc:
            challenged = bool(exc.headers and exc.headers.get("cf-mitigated"))
            if not challenged:
                if exc.code == 403:
                    log.info("403 on %s, token will be refreshed on next request", url)
                    with self._lock:
                        self._reset()
                raise
            log.info("Cloudflare challenge (HTTP %d) on %s, retrying through "
                     "the system browser", exc.code, url)
            try:
                html, clearance = self._browser.fetch(url, want_clearance=True)
            except Exception as browser_exc:
                raise RuntimeError("HTTP Error %d (Cloudflare challenge), and the "
                                   "browser fallback failed: %s"
                                   % (exc.code, browser_exc)) from exc
            with self._lock:
                rejected_again = self._fresh
                self._fresh = False
                if rejected_again:
                    self._browser_until = time.time() + BROWSER_STICKY_SECS
            if rejected_again:
                # urllib was challenged even with the browser's clearance
                # (e.g. TLS fingerprint check): stay on the browser for a while.
                log.info("plain HTTP still challenged with the browser's clearance; "
                         "using the browser for %d s", BROWSER_STICKY_SECS)
            elif clearance:
                self._adopt(*clearance)
            return html
        with self._lock:
            self._fresh = False
        return html

    def close(self):
        self._browser.close()

    @staticmethod
    def _read_html(opener, url):
        with opener.open(url, timeout=TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            html = resp.read().decode(charset, errors="replace")
            final_url = resp.geturl()
        return html, final_url


# --- system browser ----------------------------------------------------------
def find_browser(configured=None):
    """The given browser, or the first Edge/Chrome/Brave found."""
    if configured:
        if os.path.isfile(configured):
            return configured
        raise RuntimeError("browser not found: " + configured)
    roots = [os.environ.get(k) for k in
             ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    rel = [r"Microsoft\Edge\Application\msedge.exe",
           r"Google\Chrome\Application\chrome.exe",
           r"BraveSoftware\Brave-Browser\Application\brave.exe"]
    for sub in rel:
        for root in roots:
            if root and os.path.isfile(os.path.join(root, sub)):
                return os.path.join(root, sub)
    for name in ("msedge", "chrome", "brave"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("No Edge/Chrome/Brave found. Set the browser path in the "
                       "plugin configuration.")


def _profile_dir():
    path = os.path.join(_data_dir(), "browser_profile")
    os.makedirs(path, exist_ok=True)
    return path


class BrowserError(RuntimeError):
    """The browser or the DevTools connection is unusable: restart it."""


class BrowserBusy(BrowserError):
    """The browser could not start with our profile."""


class PageError(RuntimeError):
    """A page-level failure (script error, failed fetch). The browser is fine."""


class DesktopUnavailable(OSError):
    pass


# Win32 declarations for _JobProcess.
class _STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class _PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", _IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_u32 = ctypes.WinDLL("user32", use_last_error=True)
_k32.CreateProcessW.argtypes = [
    wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
    wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
    ctypes.c_void_p, ctypes.c_void_p]
_k32.CreateJobObjectW.restype = wintypes.HANDLE
_k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
_k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                         ctypes.c_void_p, wintypes.DWORD]
_k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
_k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
_k32.ResumeThread.argtypes = [wintypes.HANDLE]
_k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_k32.WaitForSingleObject.restype = wintypes.DWORD
_k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
_k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
_k32.CloseHandle.argtypes = [wintypes.HANDLE]
_u32.CreateDesktopW.restype = wintypes.HANDLE
_u32.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p,
                                wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
_u32.CloseDesktop.argtypes = [wintypes.HANDLE]


class _JobProcess:
    """The browser process, inside a Job Object that Windows terminates when
    the fetcher exits for any reason (crash, Task Manager), so no browser is
    ever left behind holding the profile.

    With desktop set, the process runs on that separate, never-displayed
    desktop: Cloudflare rejects headless browsers, so the browser needs a real
    window, and there it can never be seen or take the focus.
    Exposes the small part of the subprocess.Popen API used here."""

    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    _JobObjectExtendedLimitInformation = 9
    _CREATE_SUSPENDED = 0x4
    _STILL_ACTIVE = 259

    def __init__(self, args, desktop=None):
        self._desktop = None
        self._job = None
        self._handle = None
        self.returncode = None
        if desktop:
            GENERIC_ALL = 0x10000000
            self._desktop = _u32.CreateDesktopW(desktop, None, None, 0, GENERIC_ALL, None)
            if not self._desktop:
                raise DesktopUnavailable(ctypes.get_last_error(), "CreateDesktopW failed")
        try:
            self._job = self._create_job()
            si = _STARTUPINFOW()
            si.cb = ctypes.sizeof(si)
            si.lpDesktop = desktop
            pi = _PROCESS_INFORMATION()
            cmd = ctypes.create_unicode_buffer(subprocess.list2cmdline(args))
            # Suspended, so the browser cannot start helper processes before
            # it is in the job. No handles are inherited.
            if not _k32.CreateProcessW(None, cmd, None, None, False,
                                       self._CREATE_SUSPENDED, None, None,
                                       ctypes.byref(si), ctypes.byref(pi)):
                raise OSError(ctypes.get_last_error(), "CreateProcessW failed")
            self._handle = pi.hProcess
            self.pid = pi.dwProcessId
            if self._job and not _k32.AssignProcessToJobObject(self._job, pi.hProcess):
                log.warning("could not put the browser in a job object (error %d); "
                            "it may outlive the fetcher if the fetcher is killed",
                            ctypes.get_last_error())
            _k32.ResumeThread(pi.hThread)
            _k32.CloseHandle(pi.hThread)
        except Exception:
            self._release()
            raise

    def _create_job(self):
        job = _k32.CreateJobObjectW(None, None)
        if not job:
            log.warning("CreateJobObjectW failed (error %d)", ctypes.get_last_error())
            return None
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = self._JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _k32.SetInformationJobObject(job, self._JobObjectExtendedLimitInformation,
                                            ctypes.byref(info), ctypes.sizeof(info)):
            log.warning("SetInformationJobObject failed (error %d)", ctypes.get_last_error())
        return job

    def poll(self):
        if self.returncode is None and self._handle:
            code = wintypes.DWORD()
            _k32.GetExitCodeProcess(self._handle, ctypes.byref(code))
            if code.value != self._STILL_ACTIVE:
                self.returncode = code.value
        return self.returncode

    def wait(self, timeout=None):
        ms = 0xFFFFFFFF if timeout is None else int(timeout * 1000)
        if self.returncode is None and _k32.WaitForSingleObject(self._handle, ms) != 0:
            raise subprocess.TimeoutExpired("browser", timeout)
        return self.poll()

    def terminate(self):
        if self.poll() is None:
            _k32.TerminateProcess(self._handle, 1)

    def kill(self):
        """Terminate the browser and every helper process it started."""
        if self._job:
            _k32.TerminateJobObject(self._job, 1)
        else:
            self.terminate()

    def _release(self):
        # Closing the job handle also kills anything still running in it.
        for attr, closer in (("_handle", _k32.CloseHandle), ("_job", _k32.CloseHandle),
                             ("_desktop", _u32.CloseDesktop)):
            h = getattr(self, attr)
            if h:
                closer(h)
                setattr(self, attr, None)

    def close(self):
        self.poll()
        self._release()


class BrowserFetcher:
    """Fetches pages through the system browser (Cloudflare challenge fallback).

    One browser with a persistent profile is driven over the DevTools
    protocol. Cloudflare rejects headless browsers, so it runs with a normal
    window, but on a separate hidden desktop where it cannot be seen or take
    the focus. If the challenge does not clear on its own (it needs the user),
    the browser is restarted on the user's desktop. Once the challenge is
    cleared, pages are read with an in-page fetch(), which returns the
    original HTML source."""

    def __init__(self, browser_path=None):
        self._browser_path = browser_path
        self._lock = threading.RLock()
        self._proc = None
        self._ws = None
        self._msg_id = 0
        self._last_used = 0.0
        self._visible = False
        self._ua = None

    # --- lifecycle -------------------------------------------------------
    def _alive(self):
        return (self._proc is not None and self._proc.poll() is None
                and self._ws is not None)

    def _start(self, visible=False):
        try:
            from websockets.sync.client import connect
        except ImportError:
            raise BrowserError("the 'websockets' package (15 or later) is required "
                               "for the browser fallback")
        self.close()
        exe = find_browser(self._browser_path)
        profile = _profile_dir()
        # Port 0: the browser picks a free port itself and writes it to
        # DevToolsActivePort, so no other program can take it in between.
        port_file = os.path.join(profile, "DevToolsActivePort")
        try:
            os.remove(port_file)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise BrowserBusy("the browser profile is in use (%s)" % exc)
        args = [exe, "--remote-debugging-port=0", "--user-data-dir=" + profile,
                "--no-first-run", "--no-default-browser-check", "--mute-audio",
                "--hide-crash-restore-bubble", "about:blank"]
        if not visible:
            try:
                self._proc = _JobProcess(args, HIDDEN_DESKTOP)
            except DesktopUnavailable as exc:
                # Go straight to the interactive path; this is the only case
                # where the browser window shows without a challenge needing it.
                log.warning("hidden desktop unavailable (%s); the browser window "
                            "will be shown", exc)
                visible = True
        if visible:
            self._proc = _JobProcess(args)
        self._visible = visible
        log.info("started browser %s (pid %d, %s)", exe, self._proc.pid,
                 "visible" if visible else "hidden desktop")

        ws_url = None
        deadline = time.time() + BROWSER_START_SECS
        while ws_url is None:
            if self._proc.poll() is not None:
                code = self._proc.returncode
                self.close()
                raise BrowserBusy(
                    "the browser exited right after starting (exit code %d). This "
                    "usually means another browser process already uses the profile "
                    "%s and the new process handed over to it; close that process "
                    "and try again." % (code, profile))
            if time.time() > deadline:
                self.close()
                raise BrowserError("the browser did not open its DevTools port within "
                                   "%d s" % BROWSER_START_SECS)
            ws_url = self._page_ws_url(port_file)
            if ws_url is None:
                time.sleep(0.3)
        try:
            self._ws = connect(ws_url, max_size=None, proxy=None, open_timeout=10)
        except Exception as exc:
            self.close()
            raise BrowserError("could not connect to the browser: %s" % exc)
        self._msg_id = 0
        self._ua = self._eval("navigator.userAgent")
        threading.Thread(target=self._idle_watch, args=(self._proc,),
                         daemon=True).start()

    @staticmethod
    def _page_ws_url(port_file):
        """WebSocket URL of the browser's page, once DevTools is up."""
        try:
            with open(port_file, encoding="utf-8") as fh:
                port = int(fh.readline().strip())
            with _direct.open("http://127.0.0.1:%d/json/list" % port, timeout=2) as r:
                pages = [t for t in json.load(r) if t.get("type") == "page"]
        except (OSError, ValueError):
            return None
        return pages[0]["webSocketDebuggerUrl"] if pages else None

    def close(self):
        with self._lock:
            proc, self._proc = self._proc, None
            if self._ws is not None:
                # Ask the browser to quit by itself, so it also ends its own
                # helper processes. Only the process we started is ever touched.
                try:
                    self._call("Browser.close", timeout=5)
                except Exception:
                    pass
                try:
                    self._ws.close()
                except Exception:
                    pass
                self._ws = None
            if proc is not None:
                for stop in (lambda: proc.wait(8), proc.terminate,
                             lambda: proc.wait(5), proc.kill):
                    try:
                        stop()
                    except Exception:
                        pass
                    if proc.poll() is not None:
                        break
                proc.close()

    def _idle_watch(self, proc):
        while proc is self._proc:
            time.sleep(15)
            with self._lock:
                if proc is self._proc and time.time() - self._last_used > BROWSER_IDLE_SECS:
                    log.info("closing idle browser")
                    self.close()
                    return

    # --- DevTools --------------------------------------------------------
    def _call(self, method, timeout=60, **params):
        """Send a DevTools command. Connection problems raise BrowserError;
        an error answer from the browser raises PageError."""
        if self._ws is None:
            raise BrowserError("browser is not running")
        self._msg_id += 1
        mid = self._msg_id
        deadline = time.time() + timeout
        try:
            self._ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            while True:
                left = deadline - time.time()
                if left <= 0:
                    raise TimeoutError
                msg = json.loads(self._ws.recv(timeout=left))
                if msg.get("id") == mid:
                    break
        except TimeoutError:
            raise BrowserError("browser did not answer %s within %d s" % (method, timeout))
        except Exception as exc:  # ConnectionClosed, OSError, bad JSON
            raise BrowserError("lost the connection to the browser: %s" % exc)
        if "error" in msg:
            raise PageError("%s: %s" % (method, msg["error"].get("message")))
        return msg.get("result", {})

    def _eval(self, expr, timeout=60, await_promise=False):
        res = self._call("Runtime.evaluate", timeout=timeout, expression=expr,
                         returnByValue=True, awaitPromise=await_promise)
        if "exceptionDetails" in res:
            details = res["exceptionDetails"]
            text = (details.get("exception") or {}).get("description") or details.get("text")
            raise PageError("page script failed: %s" % text)
        return res.get("result", {}).get("value")

    # --- challenge handling ---------------------------------------------
    def _cleared(self):
        try:
            raw = self._eval(
                "JSON.stringify({host: location.hostname, ready: document.readyState,"
                " challenge: %s.test(document.title) ||"
                " !!document.querySelector('#challenge-running,#challenge-form,"
                ".cf-turnstile')})" % _CHALLENGE_TITLE_JS, timeout=10)
        except PageError:
            return False  # mid-navigation
        st = json.loads(raw)
        host = st["host"].lower()
        return ((host == ALLOWED_DOMAIN or host.endswith("." + ALLOWED_DOMAIN))
                and not st["challenge"] and st["ready"] != "loading")

    def _wait_cleared(self, secs):
        deadline = time.time() + secs
        while time.time() < deadline:
            if self._cleared():
                return True
            time.sleep(0.5)
        return False

    def _solve(self, url):
        """Navigate to url and wait until Cloudflare lets the page through.
        If it does not clear on its own, show a browser window for the user."""
        if not is_allowed(url):
            raise ValueError("refused to open a non-bedetheque URL: " + url)
        if not self._visible:
            self._call("Page.navigate", url=url)
            time.sleep(1)
            if self._wait_cleared(BROWSER_QUIET_SECS):
                return
            log.info("challenge needs the user; showing the browser window")
            self._start(visible=True)
        self._call("Page.navigate", url=url)
        if not self._wait_cleared(BROWSER_INTERACTIVE_SECS):
            self.close()
            raise RuntimeError("the Cloudflare challenge was not solved in the browser")

    def _clearance(self):
        """(User-Agent, cf_clearance cookie) of the browser, or None."""
        cookies = self._call("Network.getCookies", urls=[BASE_URL + "/"])["cookies"]
        cookie = next((c for c in cookies if c["name"] == CLEARANCE_COOKIE), None)
        return (self._ua, cookie) if cookie and self._ua else None

    def _page_fetch(self, url):
        js = ("(async()=>{const r=await fetch(%s,{credentials:'include'});"
              "const b=await r.arrayBuffer();"
              "const m=/charset=([^;]+)/i.exec(r.headers.get('content-type')||'');"
              "let t;try{t=new TextDecoder(m?m[1].trim():'utf-8').decode(b)}"
              "catch(e){t=new TextDecoder('utf-8').decode(b)}"
              "return JSON.stringify({status:r.status,"
              "cf:r.headers.get('cf-mitigated')||'',html:t})})()") % json.dumps(url)
        return json.loads(self._eval(js, timeout=60, await_promise=True))

    # --- public ----------------------------------------------------------
    def fetch(self, url, want_clearance=False):
        """Return (html, clearance). clearance is (User-Agent, cf_clearance
        cookie), read in the same locked section as the fetch, when
        want_clearance is set; else None."""
        if not is_allowed(url):
            raise ValueError("refused: only https://*.bedetheque.com URLs are fetched")
        with self._lock:
            self._last_used = time.time()
            try:
                if not self._alive():
                    self._start()
                if not self._cleared():
                    self._solve(BASE_URL + "/")
                res = self._page_fetch(url)
                if res["cf"] or res["status"] in (403, 503):
                    self._solve(url)
                    res = self._page_fetch(url)
                clearance = self._clearance() if want_clearance else None
            except BrowserError:
                self.close()  # next call starts from a clean browser
                raise
            finally:
                self._last_used = time.time()
        if res["cf"] or res["status"] >= 400:
            raise RuntimeError("HTTP Error %d (browser)" % res["status"])
        return res["html"], clearance


_daemon = None
_browser_path = None  # from --browser


def daemon():
    global _daemon
    if _daemon is None:
        _daemon = Daemon(_browser_path)
    return _daemon


def _fetch_url(url):
    try:
        return {"url": url, "html": daemon().fetch(url)}
    except Exception as exc:
        return {"error": str(exc), "traceback": traceback.format_exc()}


def _read_line(conn):
    buf = bytearray()
    while not buf.endswith(b"\n"):
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf).decode("utf-8").strip()


def _send_json(conn, payload):
    conn.sendall((json.dumps(payload) + "\n").encode("utf-8"))


def _handle_client(conn, addr):
    peer = f"{addr[0]}:{addr[1]}"
    log.info("connect  %s", peer)
    with conn:
        try:
            line = _read_line(conn)
            if not line:
                return

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                log.warning("bad json from %s", peer)
                _send_json(conn, {"error": "Invalid JSON request"})
                return
            if not isinstance(request, dict):
                _send_json(conn, {"error": "Invalid JSON request"})
                return

            if request.get("command") == "close_browser":
                daemon().close()
                log.info("browser closed on request")
                _send_json(conn, {"ok": True})
                return
            if request.get("command") == "shutdown":
                # Sent by the plugin when ComicRack closes, so the exe is no
                # longer running (and locked) when ComicRack installs an update.
                log.info("shutting down on request")
                daemon().close()
                _send_json(conn, {"ok": True})
                logging.shutdown()
                os._exit(0)
            url = request.get("url")
            if not url or not isinstance(url, str):
                log.warning("missing 'url' from %s", peer)
                _send_json(conn, {"error": "Missing 'url' in request"})
                return
            if not is_allowed(url):
                log.warning("refused  %s from %s", url, peer)
                _send_json(conn, {"error": "Refused: only https://*.bedetheque.com "
                                           "URLs are fetched"})
                return

            log.info("request  %s", url)
            result = _fetch_url(url)
            if "error" in result:
                log.info("failed   %s: %s", url, result["error"])
            else:
                html = result["html"]
                log.info("served   %s (%d bytes)", url, len(html.encode("utf-8")))
            _send_json(conn, result)
        except (ConnectionResetError, BrokenPipeError):
            log.info("dropped  %s (client gone)", peer)
        except OSError:
            log.exception("socket error with %s", peer)
        except Exception:
            log.exception("internal error handling %s", peer)
            try:
                _send_json(conn, {"error": "daemon internal error"})
            except OSError:
                pass


def main_cloudscraper(target_url):
    if not is_allowed(target_url):
        print("Refused: only https://*.bedetheque.com URLs are fetched", file=sys.stderr)
        return 2

    import cloudscraper

    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True,
        }
    )

    scraper.headers.update({
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    })

    if "/search/tout" in target_url.lower():
        homepage_url = "https://www.bedetheque.com/"

        homepage_response = scraper.get(
            homepage_url,
            timeout=30,
        )
        homepage_response.raise_for_status()

        response = scraper.get(
            target_url,
            headers={
                "Referer": homepage_url,
            },
            timeout=30,
        )
    else:
        response = scraper.get(
            target_url,
            timeout=30,
        )

    # All diagnostics go to stderr. stdout is reserved exclusively for the
    # page payload, since the caller reads stdout as the HTML content.
    print("HTTP:", response.status_code, file=sys.stderr)
    print("Final URL:", response.url, file=sys.stderr)

    response.raise_for_status()

    # Normalize to UTF-8 regardless of the page's original declared charset,
    # so the caller can always decode stdout as UTF-8 without guessing.
    html_text = response.text
    payload = html_text.encode("utf-8")

    # Write raw bytes to the underlying buffer (not the text wrapper) so no
    # platform-specific newline translation or encoding re-interpretation
    # happens on the way out.
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()

    return 0

def main_daemon(host="127.0.0.1", port=56789):
    """Run the daemon server.

    Returns an integer exit code: ``0`` for a clean shutdown (e.g. Ctrl‑C),
    ``1`` for any unexpected error that caused the loop to break.
    """
    handlers = [logging.StreamHandler()]
    try:
        # The plugin discards the daemon's stderr, so keep a log on disk.
        handlers.append(logging.handlers.RotatingFileHandler(
            os.path.join(_data_dir(), "fetcher.log"), maxBytes=500000,
            backupCount=1, encoding="utf-8"))
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(message)s",
                        datefmt="%H:%M:%S", handlers=handlers)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    error_occurred = False
    try:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        # Poll every second: on Windows a blocking accept() keeps the main
        # thread inside a native call, where Ctrl-C never gets delivered.
        srv.settimeout(1.0)
        daemon()
        log.info("listening on %s:%s", host, port)
        while True:
            try:
                client, client_addr = srv.accept()
            except KeyboardInterrupt:
                log.info("shutting down (Ctrl-C)")
                break
            except socket.timeout:
                continue
            except OSError:
                traceback.print_exc()
                continue
            except Exception as exc:
                # Catch any unexpected exception that could crash the daemon loop
                log.exception("Daemon loop unexpected error: %s", exc)
                error_occurred = True
                break
            threading.Thread(target=_handle_client, args=(client, client_addr),
                             daemon=True).start()
    finally:
        srv.close()
        daemon().close()
    return 1 if error_occurred else 0


_PROCESS_SYNCHRONIZE = 0x00100000
_INFINITE = 0xFFFFFFFF


def watch_parent(parent_pid):
    """Exit the moment parent_pid exits.
    parent_pid must be passed in explicitly (e.g. via --parent_pid),
    not derived from os.getppid() -- when frozen with PyInstaller
    onefile, getppid() returns the bootloader's PID, not the PID of
    the process that actually launched us.
    The browser is in a kill-on-close job object, so exiting also ends it;
    the PyInstaller bootloader exits once this process has."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(_PROCESS_SYNCHRONIZE, False, parent_pid)
    if not handle:
        log.warning(
            "could not open handle to parent pid %s (already gone?); "
            "parent-exit detection disabled", parent_pid
        )
        return None

    def _wait():
        kernel32.WaitForSingleObject(handle, _INFINITE)
        kernel32.CloseHandle(handle)
        log.info("parent process %s exited; shutting down", parent_pid)
        logging.shutdown()
        os._exit(1)

    t = threading.Thread(target=_wait, name="parent-watchdog", daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch bedetheque.com pages for local clients.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=56789)
    parser.add_argument("--cloudscraper", action="store_true")
    parser.add_argument("--url", help="URL to fetch (for cloudscraper mode)")
    parser.add_argument("--browser", default=None,
                        help="browser executable for the Cloudflare fallback "
                             "(default: Edge, Chrome or Brave, found automatically)")
    parser.add_argument("--parent_pid", type=int, default=None,
                        help="PID to watch; process exits when this PID dies")
    ns = parser.parse_args()
    _browser_path = ns.browser

    if ns.parent_pid:
        watch_parent(ns.parent_pid)
    else:
        log.warning("no --parent_pid supplied; parent-exit detection disabled")

    # Run the daemon and exit with the appropriate status code.
    try:
        if ns.cloudscraper and ns.url:
            exit_code = main_cloudscraper(ns.url)
        else:
            exit_code = main_daemon(ns.host, ns.port)
    except KeyboardInterrupt:
        # Ctrl‑C before or during daemon start; treat as clean shutdown.
        log.info("shutting down (Ctrl‑C) via top‑level handler")
        sys.exit(0)
    else:
        sys.exit(exit_code)
