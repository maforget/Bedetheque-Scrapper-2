''' Plugin (IronPython): settings, browser path, fetcher launch arguments,
cloudscraper fallback, daemon commands, shutdown hook, dialog owners. '''
from testlib import check, finish
from pluginlib import PLUGIN_PY, load_plugin
import clr
import re
clr.AddReference('System')
from System.IO import File, Path
from System.Net import IPAddress
from System.Net.Sockets import TcpListener
from System.Text import Encoding
from System.Threading import Thread, ThreadStart

print('--- the plugin compiles in ComicRack\'s IronPython')
source = File.ReadAllText(PLUGIN_PY)
try:
    compile(source, PLUGIN_PY, 'exec')
    check('compiles', True)
except SyntaxError, e:
    check('compiles', '%s (line %s)' % (e, e.lineno), True)

P, folder = load_plugin()

print('--- translations for the browser row')
for lang in ('FR', 'EN'):
    P.LANGENFR = lang
    words = P.Translate()
    check('%s label (T0153) present' % lang, len(words[152]) > 10, True)
    check('%s button (T0154) present' % lang, len(words[153]) > 3, True)
P.LANGENFR = 'FR'
P.aWord = P.Translate()

print('--- BrowserPath setting')
check('loads', P.LoadSetting(), True)
check('defaults to empty (auto-detect)', P.BrowserPath, '')
P.BrowserPath = r'C:\Program Files\Some Browser\browser.exe'
P.SaveSetting()
P.BrowserPath = 'changed'
P.LoadSetting()
check('survives save and load', P.BrowserPath, r'C:\Program Files\Some Browser\browser.exe')

print('--- settings form: browser row')
form = P.BDConfigForm()
check('text box shows the setting', form._TBBrowserPath.Text, P.BrowserPath)
check('label text', form._labelBrowserPath.Text, P.Trans(153))
check('browse button text', form._ButtonBrowserPath.Text, P.Trans(154))
check('row is on the first tab',
      [c.Name for c in form._tabPage1.Controls
       if c.Name in ('labelBrowserPath', 'TBBrowserPath', 'ButtonBrowserPath')],
      ['labelBrowserPath', 'TBBrowserPath', 'ButtonBrowserPath'])
check('OK button is below the tabs',
      form._OKButton.Top >= form._TabData.Bottom, True)
form._TBBrowserPath.Text = '  C:\\Other\\edge.exe  '
form.button_Click(form._OKButton, None)
check('OK stores the trimmed path', P.BrowserPath, 'C:\\Other\\edge.exe')
form.Dispose()

print('--- fetcher launch arguments')
P.use_cloudscraper = False
P.BrowserPath = ''
check('no exe and no script: nothing to launch', P.get_args(), None)
check('...and the missing file is logged', 'not found in ' + folder in File.ReadAllText(Path.Combine(folder, 'BD2_Rename_Log.txt')), True)
exe = Path.Combine(folder, 'BedethequeFetcher.exe')
File.WriteAllText(exe, 'dummy')
what, args = P.get_args()
check('exe from the plugin folder (no copy elsewhere)', what, exe)
check('port always passed, no browser when auto-detect', args, ' --port %d' % P.DAEMON_PORT)
P.BrowserPath = '"C:\\Program Files\\Edge\\msedge.exe"'
what, args = P.get_args()
check('browser path passed, quoted once',
      args, ' --port %d --browser "C:\\Program Files\\Edge\\msedge.exe"' % P.DAEMON_PORT)
check('no App.Config path passed', '--config' in args, False)
P.BrowserPath = ''
P.use_cloudscraper = True
what, args = P.get_args('https://www.bedetheque.com/x.html')
check('cloudscraper mode adds the URL',
      args.endswith(' --cloudscraper --url https://www.bedetheque.com/x.html'), True)
P.use_cloudscraper = False
File.Delete(exe)

print('--- cloudscraper failure falls back to the daemon for the session')
calls = []


def failing_cloudscraper(url):
    calls.append('cloudscraper')
    raise Exception('BedethequeFetcher exit code 1: HTTP: 403')


def daemon_fetch(url):
    calls.append('daemon')
    return '<html>daemon</html>'


P.fetch_cloudscraper = failing_cloudscraper
P.fetch_daemon = daemon_fetch
P.use_cloudscraper = True
P.cloudscraper_failed = False
check('first page comes from the daemon', P.fetch('https://www.bedetheque.com/a'),
      '<html>daemon</html>')
check('cloudscraper tried once, then the daemon', calls, ['cloudscraper', 'daemon'])
check('marked as failed', P.cloudscraper_failed, True)
del calls[:]
P.fetch('https://www.bedetheque.com/b')
check('next page skips cloudscraper', calls, ['daemon'])
P.cloudscraper_failed = False
P.fetch_cloudscraper = lambda url: '<html>cloudscraper</html>'
check('working cloudscraper is still used', P.fetch('https://www.bedetheque.com/c'),
      '<html>cloudscraper</html>')
P.use_cloudscraper = False


class FakeDaemonServer(object):
    '''Listens like the fetcher daemon and records the request lines.'''

    def __init__(self):
        self.listener = TcpListener(IPAddress.Loopback, 0)
        self.listener.Start()
        self.port = self.listener.LocalEndpoint.Port
        self.lines = []
        self.running = True
        t = Thread(ThreadStart(self._serve))
        t.IsBackground = True
        t.Start()

    def _serve(self):
        while self.running:
            try:
                client = self.listener.AcceptTcpClient()
            except Exception:
                return
            stream = client.GetStream()
            data = ''
            buf = System.Array.CreateInstance(System.Byte, 4096)
            while not data.endswith('\n'):
                n = stream.Read(buf, 0, buf.Length)
                if n == 0:
                    break
                data += Encoding.UTF8.GetString(buf, 0, n)
            if data.strip():
                self.lines.append(data.strip())
                reply = Encoding.UTF8.GetBytes('{"ok": true}\n')
                stream.Write(reply, 0, reply.Length)
            client.Close()

    def stop(self):
        self.running = False
        self.listener.Stop()


import System
server = FakeDaemonServer()
P.DAEMON_PORT = server.port

print('--- commands sent to the daemon')
P.release_browser()
check('release_browser sends close_browser', server.lines[-1:], ['{"command": "close_browser"}'])
check('end of every scrape asks to close the browser',
      len(re.findall(r'f\.Close\(\)\s+release_browser\(\)', source)), 2)


class FakeProcess(object):
    def __init__(self, exits):
        self.exits = exits
        self.waited = []
        self.killed = False

    def WaitForExit(self, ms):
        self.waited.append(ms)
        return self.exits or self.killed

    def Kill(self):
        self.killed = True


print('--- shutdown hook')
running = []
P._fetcher_processes = lambda: list(running)
del server.lines[:]
check('hook returns True', P.BD2_shutdown(True), True)
check('no fetcher running: nothing sent', server.lines, [])
proc = FakeProcess(exits=True)
running[:] = [proc]
check('hook returns True with a running fetcher', P.BD2_shutdown(False), True)
check('shutdown command sent', server.lines, ['{"command": "shutdown"}'])
check('waited for the process to exit', (proc.waited, proc.killed), ([10000], False))
stuck = FakeProcess(exits=False)
running[:] = [stuck]
P.BD2_shutdown(True)
check('a fetcher that does not exit is killed', stuck.killed, True)
real_stop = P.stop_fetch_daemon
P.stop_fetch_daemon = lambda: 1 / 0
check('hook returns True even if stopping fails', P.BD2_shutdown(True), True)
P.stop_fetch_daemon = real_stop
server.stop()
running[:] = [FakeProcess(exits=True)]
check('daemon not answering: hook still returns True', P.BD2_shutdown(True), True)
# ComicRack runs each plugin command in its own script scope: the hook must
# not depend on state left by the scrape command.
check('no module state shared between commands', 'daemon_process' in source, False)

print('--- shutdown hook is declared for ComicRack')
hook = re.search(r'#@Name ([^\r\n]+)\r?\n#@Key ([^\r\n]+)\r?\n#@Hook Shutdown\r?\n(?:#@[^\r\n]*\r?\n)*def (\w+)\(',
                 source)
check('Shutdown hook header', hook and (hook.group(2), hook.group(3)),
      ('Bedetheque2-shutdown', 'BD2_shutdown'))
check('its key is not used by another hook',
      len(re.findall(r'#@Key Bedetheque2-shutdown\b', source)), 1)

print('--- dialogs are owned by ComicRack\'s window (focus fix)')
for var in ('pickAseries', 'pickAnAlbum', 'pickAvar', 'scrape'):
    check('%s.ShowDialog(ComicRack.MainWindow)' % var,
          '%s.ShowDialog(ComicRack.MainWindow)' % var in source, True)
check('browse dialog owned by the settings form', 'dialog.ShowDialog(self)' in source, True)

finish()
