''' Plugin (IronPython), live: the plugin starts the built BedethequeFetcher.exe
and its Shutdown hook stops it, so ComicRack can overwrite the exe when it
installs an update. No page is fetched. '''
from testlib import check, finish
from pluginlib import FETCHER_EXE, load_plugin, load_plugin_scope, temp_folder
import clr
import time
clr.AddReference('System')
import System
from System import Environment, Guid
from System.Diagnostics import Process
from System.IO import Directory, File, FileAccess, FileMode, FileShare, Path
from System.Net import IPAddress
from System.Net.Sockets import TcpListener

if not File.Exists(FETCHER_EXE):
    check('src/BedethequeFetcher.exe exists (run: python build_fetcher.py)', False)
    finish()
else:
    P, folder = load_plugin(with_exe=True)
    # The fetcher writes its log and clearance under LOCALAPPDATA: use a temp
    # one, so the real files are left alone.
    data = temp_folder('BD2LiveTest-')
    Environment.SetEnvironmentVariable('LOCALAPPDATA', data)
    listener = TcpListener(IPAddress.Loopback, 0)
    listener.Start()
    P.DAEMON_PORT = listener.LocalEndpoint.Port   # a free port, not ComicRack's
    listener.Stop()
    exe = Path.Combine(folder, 'BedethequeFetcher.exe')

    def ours():
        return [p for p in Process.GetProcessesByName('BedethequeFetcher')
                if p.MainModule.FileName.lower() == exe.lower()]

    def writable():
        try:
            File.Open(exe, FileMode.Open, FileAccess.ReadWrite, FileShare.None).Close()
            return True
        except Exception:
            return False

    print('--- start')
    check('ensure_fetch_daemon starts the exe', P.ensure_fetch_daemon(), True)
    check('it listens on the port the plugin uses', P.is_daemon_running(), True)
    check('exe and its PyInstaller child running', len(ours()), 2)
    check('the running exe is locked', writable(), False)

    print('--- Shutdown hook, run from its own script scope as in ComicRack')
    hook = load_plugin_scope(folder, 'BD2_shutdown_scope')
    hook.DAEMON_PORT = P.DAEMON_PORT
    check('the hook\'s scope is a separate module', hook is not P, True)
    t0 = time.time()
    check('BD2_shutdown returns True', hook.BD2_shutdown(True), True)
    took = time.time() - t0
    check('no fetcher left when the hook returns (%.2f s)' % took, len(ours()), 0)
    check('the exe can be overwritten', writable(), True)
    check('port closed', P.is_daemon_running(), False)
    t0 = time.time()
    hook.BD2_shutdown(True)
    check('a second close returns at once', time.time() - t0 < 0.5, True)
    finish()
