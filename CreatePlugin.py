import os
import zipfile

def zip_files(list_files, out_name):    
    with zipfile.ZipFile(out_name, "w") as archive:
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
    desktop = os.path.expanduser("~/Desktop")
    out_name = os.path.join(desktop, f"{name}_v{version}.crplugin")
    return out_name

if __name__ == '__main__':
    name = get_plugin_name()
    files = get_package_files()
    zip_files(files, name)