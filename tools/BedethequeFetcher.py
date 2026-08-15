import os
import sys
 
# When run via the dev-only fallback, this script lives in the published
# plugin folder alongside other files meant for IronPython 2.7 (e.g. a
# types.py shim defining py2-only names like `long`). Python auto-prepends
# this script's own directory to sys.path, so those same-named files can
# shadow real stdlib modules (types, and anything that imports it - re,
# enum, logging, ...) before cloudscraper even gets a chance to import.
# Strip it before importing anything else that could trigger that chain.
#
# Skip this entirely when frozen (running as the built exe): there,
# __file__'s directory is PyInstaller's extraction folder (_MEIPASS),
# which is the one sys.path entry the exe needs to find its own bundled
# modules - including cloudscraper - so it must stay in sys.path.
if not getattr(sys, "frozen", False):
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _SCRIPT_DIR]


import cloudscraper


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: BedethequeFetcher.py <url>",
            file=sys.stderr,
        )
        return 2

    target_url = sys.argv[1]

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


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
