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
import http.client
import http.cookiejar
import json
import logging
import logging.handlers
import shutil
import socket
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request

"""
Small daemon that fetches bedetheque.com pages on demand.

It keeps one opener + cookie jar alive for the whole run and renews the
csrf_cookie_bel token automatically (on expiry, or when the server rejects
it). Clients talk to it over a local TCP socket, one JSON object per line:

    client > daemon:  {"url": "https://..."}\n
    daemon > client:  {"url": "...", "html": "..."}\n   or   {"error": "..."}\n

Usage:
    python BedethequeFetcher.py [--host 127.0.0.1] [--port 56789]
"""

BASE_URL = "https://www.bedetheque.com"
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

log = logging.getLogger("fetch_daemon")

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
        urllib.request.HTTPCookieProcessor(jar))
    headers = list(HEADERS)
    if user_agent:
        # cf_clearance is only valid for the User-Agent that earned it.
        headers = [(k, user_agent if k == "User-Agent" else v) for k, v in headers]
    opener.addheaders = headers
    return opener


def _clearance_file():
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    return os.path.join(base, "BedethequeScraper2", "clearance.json")


def _load_clearance():
    """(user_agent, [cdp cookie dicts]) saved after a browser session, else (None, [])."""
    try:
        with open(_clearance_file(), encoding="utf-8") as fh:
            data = json.load(fh)
        now = time.time()
        cookies = [c for c in data["cookies"]
                   if not (c.get("expires", -1) > 0 and c["expires"] < now)]
        if any(c["name"] == "cf_clearance" for c in cookies):
            return data["user_agent"], cookies
    except Exception:
        pass
    return None, []


def _save_clearance(user_agent, cookies):
    try:
        os.makedirs(os.path.dirname(_clearance_file()), exist_ok=True)
        with open(_clearance_file(), "w", encoding="utf-8") as fh:
            json.dump({"user_agent": user_agent, "cookies": cookies}, fh)
    except OSError:
        log.warning("could not save %s", _clearance_file())


def _jar_cookie(c):
    """http.cookiejar.Cookie from a DevTools cookie dict."""
    domain = c["domain"]
    expires = int(c["expires"]) if c.get("expires", -1) > 0 else None
    return http.cookiejar.Cookie(
        0, c["name"], c["value"], None, False, domain, True,
        domain.startswith("."), c.get("path", "/"), True, bool(c.get("secure")),
        expires, expires is None, None, None, {})


class Daemon:
    """Shared state for outgoing requests: cookie jar, opener, CSRF token.
    Guarded by a lock because clients are served on separate threads."""

    def __init__(self):
        self._lock = threading.Lock()
        self._jar = _load_jar()
        self._ua, saved = _load_clearance()
        for c in saved:
            self._jar.set_cookie(_jar_cookie(c))
        if saved:
            log.info("loaded saved Cloudflare clearance")
        self._opener = _build_opener(self._jar, self._ua)
        self._browser = BrowserFetcher()
        self._browser_until = 0.0
        self._fresh = False  # clearance adopted, not yet confirmed by urllib

    def _reset(self):
        """Drop the rejected CSRF token so the next fetch gets a fresh one.
        The Cloudflare clearance is kept."""
        for c in list(self._jar):
            if c.name != "cf_clearance":
                self._jar.clear(c.domain, c.path, c.name)
        self._opener = _build_opener(self._jar, self._ua)

    def _adopt_browser_session(self):
        """Take the cookies and User-Agent of the cleared browser, so plain
        HTTP requests pass Cloudflare too (and keep passing after restarts)."""
        try:
            ua, cookies = self._browser.session()
        except Exception as exc:
            log.warning("could not read the browser session: %s", exc)
            return
        if not any(c["name"] == "cf_clearance" for c in cookies):
            return
        with self._lock:
            for c in cookies:
                self._jar.set_cookie(_jar_cookie(c))
            self._ua = ua
            self._opener = _build_opener(self._jar, ua)
            self._fresh = True
        _save_clearance(ua, [{k: c.get(k) for k in
                              ("name", "value", "domain", "path", "expires", "secure")}
                             for c in cookies])
        log.info("adopted Cloudflare clearance from the browser")

    def fetch(self, url):
        """Return the HTML of url. A 403/503 (Cloudflare) drops the cookies for
        a refresh and retries through the system browser."""
        if time.time() < self._browser_until:
            return self._browser.fetch(url)
        with self._lock:
            opener = self._opener
        try:
            html, _ = self._read_html(opener, url)
            self._fresh = False
            return html
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                log.info("403 on %s, token will be refreshed on next request", url)
                with self._lock:
                    self._reset()
            if exc.code not in (403, 503):
                raise
            log.info("%d on %s, retrying through the system browser", exc.code, url)
            try:
                html = self._browser.fetch(url)
            except Exception as browser_exc:
                raise RuntimeError("HTTP Error %d, and the browser fallback failed: %s"
                                   % (exc.code, browser_exc)) from exc
            if self._fresh:
                # urllib was rejected even with the browser's clearance
                # (e.g. TLS fingerprint check): stay on the browser for a while.
                self._fresh = False
                self._browser_until = time.time() + BROWSER_STICKY_SECS
            else:
                self._adopt_browser_session()
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


BROWSER_IDLE_SECS = 60        # close the browser after this long without a fetch
BROWSER_QUIET_SECS = 20       # wait this long for an automatic challenge to clear
BROWSER_INTERACTIVE_SECS = 60  # then show the window and let the user solve it
BROWSER_STICKY_SECS = 900     # after a 403, go straight to the browser for this long
_CHALLENGE_TITLE_JS = ("/just a moment|un instant|attention required|"
                       "checking your browser|verify you are human/i")


def _config_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = None  # plugin's App.Config, set from --config


def read_browser_setting():
    """BrowserPath from the plugin's App.Config (<configuration><BrowserPath>)."""
    path = CONFIG_FILE or os.path.join(_config_dir(), "App.Config")
    try:
        import xml.etree.ElementTree as ET
        node = ET.parse(path).getroot().find("BrowserPath")
        return (node.text or "").strip() if node is not None else ""
    except Exception:
        return ""


def find_browser():
    """The configured browser, or the first Edge/Chrome/Brave found."""
    configured = read_browser_setting()
    if configured:
        if os.path.isfile(configured):
            return configured
        raise RuntimeError("BrowserPath in App.Config does not exist: " + configured)
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
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    path = os.path.join(base, "BedethequeScraper2", "browser_profile")
    os.makedirs(path, exist_ok=True)
    return path


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


HIDDEN_DESKTOP = "BedethequeScraper2"


class _DesktopProcess:
    """A process started on a separate, never-displayed Windows desktop.

    Cloudflare rejects headless browsers, so the browser must run with a real
    window; on its own desktop that window can never be seen and can never take
    the foreground or the keyboard focus from the user's applications.
    Exposes the small part of the subprocess.Popen API used here."""

    def __init__(self, args, desktop):
        import ctypes
        from ctypes import wintypes as wt

        class STARTUPINFOW(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR),
                        ("lpDesktop", wt.LPWSTR), ("lpTitle", wt.LPWSTR),
                        ("dwX", wt.DWORD), ("dwY", wt.DWORD), ("dwXSize", wt.DWORD),
                        ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
                        ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD),
                        ("dwFlags", wt.DWORD), ("wShowWindow", wt.WORD),
                        ("cbReserved2", wt.WORD), ("lpReserved2", ctypes.c_void_p),
                        ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE),
                        ("hStdError", wt.HANDLE)]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                        ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]

        self._k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.CreateDesktopW.restype = wt.HANDLE
        user32.CreateDesktopW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p,
                                          wt.DWORD, wt.DWORD, ctypes.c_void_p]
        user32.CloseDesktop.argtypes = [wt.HANDLE]
        self._k32.CreateProcessW.argtypes = [
            wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wt.BOOL,
            wt.DWORD, ctypes.c_void_p, wt.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p]
        for name in ("WaitForSingleObject", "GetExitCodeProcess", "TerminateProcess",
                     "CloseHandle"):
            getattr(self._k32, name).restype = wt.DWORD
        self._k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
        self._k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
        self._k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
        self._k32.CloseHandle.argtypes = [wt.HANDLE]
        self._wt, self._ctypes = wt, ctypes

        GENERIC_ALL = 0x10000000
        self._user32 = user32
        self._desktop = user32.CreateDesktopW(desktop, None, None, 0, GENERIC_ALL, None)
        if not self._desktop:
            raise OSError(ctypes.get_last_error(), "CreateDesktopW failed")
        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(si)
        si.lpDesktop = desktop
        pi = PROCESS_INFORMATION()
        CREATE_NO_WINDOW = 0x08000000
        cmd = ctypes.create_unicode_buffer(subprocess.list2cmdline(args))
        if not self._k32.CreateProcessW(None, cmd, None, None, False, CREATE_NO_WINDOW,
                                        None, None, ctypes.byref(si), ctypes.byref(pi)):
            err = ctypes.get_last_error()
            user32.CloseDesktop(self._desktop)
            raise OSError(err, "CreateProcessW failed")
        self._k32.CloseHandle(pi.hThread)
        self._handle = pi.hProcess
        self.pid = pi.dwProcessId
        self.returncode = None

    def poll(self):
        if self.returncode is None:
            code = self._wt.DWORD()
            self._k32.GetExitCodeProcess(self._handle, self._ctypes.byref(code))
            if code.value != 259:  # STILL_ACTIVE
                self.returncode = code.value
                self._release()
        return self.returncode

    def wait(self, timeout=None):
        ms = 0xFFFFFFFF if timeout is None else int(timeout * 1000)
        if self.returncode is None and self._k32.WaitForSingleObject(self._handle, ms) != 0:
            raise subprocess.TimeoutExpired("browser", timeout)
        return self.poll()

    def terminate(self):
        if self.returncode is None:
            self._k32.TerminateProcess(self._handle, 1)

    kill = terminate

    def _release(self):
        if self._handle:
            self._k32.CloseHandle(self._handle)
            self._handle = None
        if self._desktop:
            self._user32.CloseDesktop(self._desktop)
            self._desktop = None


class BrowserBusy(RuntimeError):
    pass


class BrowserFetcher:
    """Fetches pages through the system browser (Cloudflare challenge fallback).

    One browser with a persistent profile (keeps cf_clearance) is driven over
    the DevTools protocol. Cloudflare rejects headless browsers, so it runs
    with a normal window, but on a separate hidden desktop where it cannot be
    seen or take the focus. If the challenge does not clear on its own (it
    needs the user), the browser is restarted on the user's desktop. Once the
    challenge is cleared, pages are read with an in-page fetch(), which
    returns the original HTML source."""

    def __init__(self):
        self._lock = threading.RLock()
        self._proc = None
        self._ws = None
        self._msg_id = 0
        self._last_used = 0.0

    # --- lifecycle -------------------------------------------------------
    def _alive(self):
        return (self._proc is not None and self._proc.poll() is None
                and self._ws is not None)

    def _start(self, visible=False):
        try:
            from websockets.sync.client import connect
        except ImportError:
            raise RuntimeError("the 'websockets' package is required for the "
                               "browser fallback")
        self.close()
        exe = find_browser()
        port = _free_port()
        args = [exe, "--remote-debugging-port=%d" % port,
                "--user-data-dir=" + _profile_dir(),
                "--no-first-run", "--no-default-browser-check", "--mute-audio",
                "--hide-crash-restore-bubble", "about:blank"]
        self._proc = None
        if not visible:
            try:
                self._proc = _DesktopProcess(args, HIDDEN_DESKTOP)
                log.info("starting browser %s on port %d (hidden desktop)", exe, port)
            except OSError as exc:
                log.warning("hidden desktop unavailable (%s); the browser "
                            "window will be visible", exc)
        if self._proc is None:
            log.info("starting browser %s on port %d (visible)", exe, port)
            self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
        ws_url = None
        deadline = time.time() + 20
        while time.time() < deadline and ws_url is None:
            if self._proc.poll() is not None:
                raise BrowserBusy("browser exited immediately (is the same "
                                   "profile open in another process?)")
            try:
                with urllib.request.urlopen(
                        "http://127.0.0.1:%d/json/list" % port, timeout=2) as r:
                    pages = [t for t in json.load(r) if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
            except Exception:
                time.sleep(0.3)
        if ws_url is None:
            self.close()
            raise RuntimeError("browser did not expose its DevTools port")
        self._ws = connect(ws_url, max_size=None)
        self._msg_id = 0
        self._call("Page.enable")
        threading.Thread(target=self._idle_watch, daemon=True).start()

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
                for stop in (lambda: proc.wait(8), proc.terminate, lambda: proc.wait(5),
                             proc.kill):
                    try:
                        stop()
                    except Exception:
                        pass
                    if proc.poll() is not None:
                        break

    def _idle_watch(self):
        proc = self._proc
        while proc is not None and proc is self._proc:
            time.sleep(15)
            with self._lock:
                if proc is self._proc and time.time() - self._last_used > BROWSER_IDLE_SECS:
                    log.info("closing idle browser")
                    self.close()
                    return

    # --- DevTools --------------------------------------------------------
    def _call(self, method, timeout=60, **params):
        self._msg_id += 1
        mid = self._msg_id
        self._ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        deadline = time.time() + timeout
        while True:
            left = deadline - time.time()
            if left <= 0:
                raise RuntimeError("browser call timed out: " + method)
            try:
                msg = json.loads(self._ws.recv(timeout=left))
            except TimeoutError:
                raise RuntimeError("browser call timed out: " + method)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (method, msg["error"].get("message")))
                return msg.get("result", {})

    def _eval(self, expr, timeout=60, await_promise=False):
        res = self._call("Runtime.evaluate", timeout=timeout, expression=expr,
                         returnByValue=True, awaitPromise=await_promise)
        if "exceptionDetails" in res:
            raise RuntimeError("page script failed: " +
                               str(res["exceptionDetails"].get("text")))
        return res.get("result", {}).get("value")

    # --- challenge handling ---------------------------------------------
    def _page_state(self):
        try:
            return self._eval(
                "JSON.stringify({host: location.hostname, ready: document.readyState,"
                " challenge: %s.test(document.title) ||"
                " !!document.querySelector('#challenge-running,#challenge-form,"
                ".cf-turnstile')})" % _CHALLENGE_TITLE_JS, timeout=10)
        except Exception:
            return None  # mid-navigation

    def _cleared(self):
        raw = self._page_state()
        if not raw:
            return False
        st = json.loads(raw)
        return (st["host"].endswith("bedetheque.com") and not st["challenge"]
                and st["ready"] != "loading")

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
        self._call("Page.navigate", url=url)
        time.sleep(1)
        if self._wait_cleared(BROWSER_QUIET_SECS):
            return
        log.info("challenge needs the user; showing the browser window")
        self._start(visible=True)
        self._call("Page.navigate", url=url)
        if not self._wait_cleared(BROWSER_INTERACTIVE_SECS):
            raise RuntimeError("Cloudflare challenge was not solved in the browser")

    # --- public ----------------------------------------------------------
    def session(self):
        """(User-Agent, DevTools cookies for bedetheque) of the running browser."""
        with self._lock:
            if not self._alive():
                raise RuntimeError("browser is not running")
            cookies = self._call("Network.getCookies", urls=[BASE_URL + "/"])["cookies"]
            return self._eval("navigator.userAgent"), cookies

    def _page_fetch(self, url):
        js = ("(async()=>{const r=await fetch(%s,{credentials:'include'});"
              "const b=await r.arrayBuffer();"
              "const m=/charset=([^;]+)/i.exec(r.headers.get('content-type')||'');"
              "let t;try{t=new TextDecoder(m?m[1].trim():'utf-8').decode(b)}"
              "catch(e){t=new TextDecoder('utf-8').decode(b)}"
              "return JSON.stringify({status:r.status,"
              "cf:r.headers.get('cf-mitigated')||'',html:t})})()") % json.dumps(url)
        return json.loads(self._eval(js, timeout=60, await_promise=True))

    def fetch(self, url):
        with self._lock:
            self._last_used = time.time()
            try:
                if not self._alive():
                    try:
                        self._start()
                    except BrowserBusy:
                        time.sleep(3)  # a previous browser may still hold the profile
                        self._start()
                if not self._cleared():
                    self._solve(BASE_URL + "/")
                res = self._page_fetch(url)
                if res["cf"] or res["status"] in (403, 503):
                    self._solve(url)
                    res = self._page_fetch(url)
            except Exception:
                self.close()  # next call starts from a clean browser
                raise
            self._last_used = time.time()
            if res["cf"] or res["status"] >= 400:
                raise RuntimeError("HTTP Error %d (browser)" % res["status"])
            return res["html"]


_daemon = None


def daemon():
    global _daemon
    if _daemon is None:
        _daemon = Daemon()
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

            if request.get("command") == "close_browser":
                daemon().close()
                log.info("browser closed on request")
                _send_json(conn, {"ok": True})
                return
            url = request.get("url")
            if not url or not isinstance(url, str):
                log.warning("missing 'url' from %s", peer)
                _send_json(conn, {"error": "Missing 'url' in request"})
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
        log_dir = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(),
                               "BedethequeScraper2")
        os.makedirs(log_dir, exist_ok=True)
        # The plugin discards the daemon's stderr, so keep a log on disk.
        handlers.append(logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "fetcher.log"), maxBytes=500000,
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


import ctypes
import subprocess
import threading

_PROCESS_SYNCHRONIZE = 0x00100000
_INFINITE = 0xFFFFFFFF

def _terminate_self_and_children():
    """Force-kill this process and its entire subtree."""
    log.info("terminating self (pid %s) and children", os.getpid())
    try:
        # /T kills the whole process tree rooted at our PID, so any
        # subprocesses we spawned (e.g. for cloudscraper) go down too.
        subprocess.call(
            ["taskkill", "/PID", str(os.getpid()), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    # Fallback in case taskkill didn't finish us off for some reason.
    os._exit(1)


def watch_parent(parent_pid):
    """Kill this process tree the moment parent_pid exits.
    parent_pid must be passed in explicitly (e.g. via --parent_pid),
    not derived from os.getppid() -- when frozen with PyInstaller
    onefile, getppid() returns the bootloader's PID, not the PID of
    the process that actually launched us."""
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
        _terminate_self_and_children()

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
    parser.add_argument("--config", default=None,
                        help="path of the plugin's App.Config (browser setting)")
    parser.add_argument("--parent_pid", type=int, default=None,
                        help="PID to watch; process exits when this PID dies")
    ns = parser.parse_args()
    CONFIG_FILE = ns.config
    
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
