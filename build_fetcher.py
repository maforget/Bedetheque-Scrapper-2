"""
Builds BedethequeFetcher(.exe) with PyInstaller.

Usage (run from the repo root):
    python build_fetcher.py

Layout assumptions:
    ./build_fetcher.py            <- this script
    ./tools/BedethequeFetcher.py  <- entry point
    ./src/                        <- output: BedethequeFetcher.exe is dropped here,
                                    next to BedethequeScraper2.py, ready to be
                                    zipped up by the packaging workflow.

Bundles cloudscraper's browsers.json using the layout cloudscraper itself
recommends for frozen executables (see cloudscraper README, "Executable
Compatibility" / PyInstaller section):

    pyinstaller --add-data "cloudscraper/user_agent/browsers.json;cloudscraper/user_agent/" your_app.py

The source path is resolved dynamically from the installed cloudscraper
package instead of being hardcoded, so this keeps working if cloudscraper's
own on-disk layout changes between versions.
"""

import os
import sys

import cloudscraper
from PyInstaller.__main__ import run as pyinstaller_run

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINT = os.path.join(ROOT_DIR, "tools", "BedethequeFetcher.py")
DIST_DIR = os.path.join(ROOT_DIR, "src")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
SPEC_DIR = ROOT_DIR

# PyInstaller's --add-data separator between "source" and "dest" is ';' on
# Windows and ':' on macOS/Linux.
DATA_SEPARATOR = ";" if os.name == "nt" else ":"


def cloudscraper_browsers_json_data_arg():
    cloudscraper_dir = os.path.dirname(os.path.abspath(cloudscraper.__file__))
    browsers_json = os.path.join(cloudscraper_dir, "user_agent", "browsers.json")

    if not os.path.isfile(browsers_json):
        raise FileNotFoundError(
            "Could not find cloudscraper's browsers.json at: " + browsers_json
        )

    dest = "cloudscraper/user_agent/"
    return "--add-data={0}{1}{2}".format(browsers_json, DATA_SEPARATOR, dest)


def main():
    os.chdir(ROOT_DIR)

    if not os.path.isfile(ENTRY_POINT):
        raise FileNotFoundError("Entry point not found: " + ENTRY_POINT)

    pyinstaller_run([
        ENTRY_POINT,
        "--name=BedethequeFetcher",
        "--onefile",
        "--console",
        cloudscraper_browsers_json_data_arg(),
        "--distpath=" + DIST_DIR,
        "--workpath=" + BUILD_DIR,
        "--specpath=" + SPEC_DIR,
        "--clean",
        "--noconfirm",
    ])


if __name__ == "__main__":
    sys.exit(main())
