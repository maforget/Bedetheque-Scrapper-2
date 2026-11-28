''' Check helpers shared by the CPython (fetcher) and IronPython (plugin) tests.
Every print() here takes one string, so it works in Python 2 and 3. '''
import sys

_results = []
_cleanups = []


def check(label, got, want=True):
    '''Records and prints one result: got must equal want.'''
    ok = got == want
    _results.append(ok)
    print('%s %-62s %r' % ('ok  ' if ok else 'FAIL', label, got))
    if not ok:
        print('     expected %r' % (want,))
    return ok


def at_finish(fn):
    '''Runs fn when finish() is called (ComicRack's IronPython has no atexit).'''
    _cleanups.append(fn)


def finish():
    '''Prints the failure count. run_ironpython.ps1 turns it into the exit
    code; under CPython the script also exits with 1 on failure.'''
    for fn in _cleanups:
        try:
            fn()
        except Exception:
            pass
    failures = _results.count(False)
    print('%d failure(s)' % failures)
    if sys.platform != 'cli' and failures:
        sys.exit(1)
