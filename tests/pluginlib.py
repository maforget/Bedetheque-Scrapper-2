''' Helpers for the plugin tests (ComicRack CE's IronPython 2.7). '''
import clr
import sys
from testlib import at_finish
clr.AddReference('System')
clr.AddReference('System.Windows.Forms')
clr.AddReferenceToFileAndPath(
    r'C:\Program Files\ComicRack Community Edition\ComicRack.Engine.dll')
from System import Guid
from System.IO import Directory, File, Path, SearchOption
from System.Windows.Forms import Form

ROOT = Path.GetDirectoryName(Path.GetDirectoryName(Path.GetFullPath(sys.argv[0])))
SRC = Path.Combine(ROOT, 'src')
PLUGIN_PY = Path.Combine(SRC, 'BedethequeScraper2.py')
FETCHER_EXE = Path.Combine(SRC, 'BedethequeFetcher.exe')


class FakeApp(object):
    # below 0.9.182, so ThemeMe() leaves the forms alone
    ProductVersion = '0.9.100'


class FakeComicRack(object):
    def __init__(self):
        self.App = FakeApp()
        self.MainWindow = Form()


def temp_folder(prefix):
    '''A new temp folder, deleted by testlib.finish(). Files the test process
    still holds (an image a form loaded) can't be deleted then; such leftovers
    of earlier runs are deleted here.'''
    for old in Directory.GetDirectories(Path.GetTempPath(), prefix + '*'):
        try:
            Directory.Delete(old, True)
        except Exception:
            pass
    folder = Path.Combine(Path.GetTempPath(), prefix + Guid.NewGuid().ToString('N'))
    Directory.CreateDirectory(folder)

    def remove():
        try:
            Directory.Delete(folder, True)
        except Exception:
            pass
    at_finish(remove)
    return folder


def load_plugin_scope(folder, name):
    '''Another, independent copy of the plugin module from folder. ComicRack
    gives each plugin command (Books, Shutdown, ...) its own script scope, so
    globals set by one command are not seen by another.'''
    import imp
    module = imp.load_source(name, Path.Combine(folder, 'BedethequeScraper2.py'))
    module.ComicRack = FakeComicRack()
    module.aWord = module.Translate()
    return module


def load_plugin(with_exe=False):
    '''Imports the plugin from a copy of src/ in a new temp folder, so
    App.Config and the logs it writes never touch src/. Sets the ComicRack
    global and the translations. Returns (module, folder).'''
    folder = temp_folder('BD2PluginTest-')
    for f in Directory.GetFiles(SRC, '*', SearchOption.TopDirectoryOnly):
        name = Path.GetFileName(f)
        if name == 'BedethequeFetcher.exe' and not with_exe:
            continue
        if name in ('App.Config', 'BD2_debug_log.txt', 'BD2_Rename_Log.txt'):
            continue
        File.Copy(f, Path.Combine(folder, name))
    sys.path.insert(0, folder)
    for name in list(sys.modules):
        if name == 'BedethequeScraper2':
            del sys.modules[name]
    import BedethequeScraper2 as plugin
    plugin.ComicRack = FakeComicRack()
    plugin.aWord = plugin.Translate()
    return plugin, folder
