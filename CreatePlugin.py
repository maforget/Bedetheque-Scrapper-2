import os
import subprocess
import sys
import zipfile

def zip_files(list_files, out_name):    
    with zipfile.ZipFile(out_name, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename in list_files:
            name = os.path.basename(filename)
            archive.write(filename, name)
        
def read_file(path):
    #absolute_path = os.path.dirname(__file__)
    #full_path = os.path.join(absolute_path, path)
    
    out_path = path if os.path.isabs(path) else find_path(path)     
    return open(out_path)

def find_path(filename):
    dir = os.path.dirname(__file__)
    files = enumerate_files(dir)
    for file in files:
        if file.endswith(filename):
            return file
        
def enumerate_files(dir, topOnly = False):
    onlyfiles = []
    for f in os.listdir(dir):
        full_path = os.path.join(dir, f)
        if os.path.isfile(full_path):
            onlyfiles.append(full_path)
        elif not topOnly:
            onlyfiles.extend(enumerate_files(full_path))
    return onlyfiles
    
def get_ignore(dir):
    path = find_path(".gitignore")
    gitignore = read_file(path)
    
    ignore = []
    for line in gitignore:
        full_path = find_path(line.strip().lstrip("/\\"))
        if full_path and not full_path in ignore:
            ignore.append(full_path)
    
    ignore.append(path)
    ignore.append(find_path(".crplugin"))
    ignore.append(__file__)
    return ignore

def get_package_files():
    path = find_path("Package.ini")
    package_dir = os.path.dirname(path)
    files = enumerate_files(package_dir, topOnly=True)
    ignore = get_ignore(package_dir)
    package_files = []
    
    for f in files:
        if not f in ignore:
            package_files.append(f)
            
    return package_files
            
    
def get_plugin_name():
    package = read_file("Package.ini")

    thedict = dict()
    for line in package:
        l = line.split('=')
        key = l[0].strip()
        value = l[1].strip()
        thedict[key] = value
    
    name = thedict["Name"]
    version = thedict["Version"]
    # dir = os.path.expanduser("~/Desktop")
    dir = os.path.dirname(__file__)
    out_name = os.path.join(dir, f"{name}_v{version}.crplugin")
    return out_name


def is_running_in_ci():
    # GitHub Actions sets this on every runner automatically.
    return os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


def build_fetcher_exe():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    build_script = os.path.join(root_dir, "build_fetcher.py")

    if not os.path.isfile(build_script):
        raise FileNotFoundError("build_fetcher.py not found: " + build_script)

    print("Building BedethequeFetcher.exe...", file=sys.stderr)
    subprocess.run(
        [sys.executable, build_script],
        check=True,
        cwd=root_dir,
    )

    exe_path = find_path("BedethequeFetcher.exe")
    if not exe_path:
        raise FileNotFoundError(
            "build_fetcher.py ran but BedethequeFetcher.exe was not found "
            "afterwards (expected in src/)."
        )


if __name__ == '__main__':
    # On the GitHub runner, building the exe and zipping is handled by
    # dedicated workflow steps (a separate Windows job builds the exe,
    # montudor/action-zip does the zipping). This script's only job there
    # is to print the target .crplugin filename on stdout, which the
    # workflow captures with $(python CreatePlugin.py).
    #
    # Locally, there's no such pipeline, so pass --local (or just run
    # outside of GitHub Actions) to have this script build the exe itself
    # and produce the finished .crplugin directly.
    local_build = not is_running_in_ci()

    if "--local" in sys.argv:
        local_build = True
    elif "--ci" in sys.argv:
        local_build = False

    name = get_plugin_name()

    if local_build:
        build_fetcher_exe()
        files = get_package_files()
        zip_files(files, name)
        print("Created:", name, file=sys.stderr)

    print(name)