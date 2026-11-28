''' Fetcher: _JobProcess (hidden desktop and kill-on-close job, S3), with
harmless processes instead of a browser. '''
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

from testlib import check, finish
from fetcherlib import load_fetcher, temp_data_dir

temp_data_dir()
m = load_fetcher()
k32 = ctypes.WinDLL('kernel32')
u32 = ctypes.WinDLL('user32')
k32.OpenProcess.restype = wintypes.HANDLE
k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
k32.CloseHandle.argtypes = [wintypes.HANDLE]


def alive(pid):
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = wintypes.DWORD()
    k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


def wait_until(pred, secs=10):
    end = time.time() + secs
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return pred()


def windows_of(pid):
    '''Top-level windows of pid on the user's (default) desktop.'''
    found = []
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        owner = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            found.append(hwnd)
        return True
    u32.EnumWindows(proc(cb), 0)
    return found


# A parent that starts a child, then both sleep: stands in for a browser
# and its helper processes. Writes the child's PID to the file in argv[1].
TREE = ('import subprocess, sys, time\n'
        'c = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])\n'
        'open(sys.argv[1], "w").write(str(c.pid))\n'
        'time.sleep(120)\n')
tree_file = os.path.join(os.environ['LOCALAPPDATA'], 'tree.py')
with open(tree_file, 'w') as fh:
    fh.write(TREE)


def child_pid_from(path):
    def read():
        try:
            return int(open(path).read().strip())
        except (OSError, ValueError):
            return None
    wait_until(lambda: read() is not None)
    return read()


print('--- a window on the hidden desktop never reaches the user')


def foreground_pid():
    owner = wintypes.DWORD()
    u32.GetWindowThreadProcessId(u32.GetForegroundWindow(), ctypes.byref(owner))
    return owner.value


p = m._JobProcess(['notepad.exe'], m.HIDDEN_DESKTOP)
owners = set()
end = time.time() + 2
while time.time() < end:
    owners.add(foreground_pid())
    time.sleep(0.02)
check('process runs', p.poll(), None)
# Other windows may come and go (the user is working); the hidden process's
# window must never be the foreground one.
check('it never has the foreground', p.pid in owners, False)
check('no window on the user\'s desktop', windows_of(p.pid), [])
p.kill()
check('kill ends it', wait_until(lambda: not alive(p.pid)), True)
p.close()

print('--- kill() ends the whole process tree')
out = os.path.join(os.environ['LOCALAPPDATA'], 'child1.txt')
p = m._JobProcess([sys.executable, tree_file, out])
child = child_pid_from(out)
check('child started', child is not None and alive(child), True)
p.kill()
check('kill ends the child too', wait_until(lambda: not alive(child)), True)
p.close()

print('--- the job ends the browser when the fetcher dies abnormally (S3)')
HOLDER = ('import importlib.util, sys, time\n'
          'spec = importlib.util.spec_from_file_location("f", sys.argv[1])\n'
          'm = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n'
          'p = m._JobProcess([sys.executable] + sys.argv[2:], m.HIDDEN_DESKTOP)\n'
          'time.sleep(120)\n')
holder_file = os.path.join(os.environ['LOCALAPPDATA'], 'holder.py')
with open(holder_file, 'w') as fh:
    fh.write(HOLDER)
out = os.path.join(os.environ['LOCALAPPDATA'], 'child2.txt')
holder = subprocess.Popen([sys.executable, holder_file, m.__file__, tree_file, out])
child = child_pid_from(out)
check('process tree started by the fake fetcher', child is not None and alive(child), True)
holder.kill()  # TerminateProcess, like Task Manager's End task
holder.wait()
check('killing the fetcher ends the tree', wait_until(lambda: not alive(child)), True)

print('--- graceful close: wait, then terminate')
p = m._JobProcess([sys.executable, '-c', 'import time; time.sleep(120)'])
try:
    p.wait(0.2)
    check('wait() raises TimeoutExpired while running', False)
except subprocess.TimeoutExpired:
    check('wait() raises TimeoutExpired while running', True)
p.terminate()
check('terminate ends it, wait() returns the exit code', p.wait(5), 1)
p.close()

finish()
