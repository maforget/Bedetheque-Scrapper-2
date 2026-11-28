### You should consider using [ComicRack Community Edition](https://github.com/maforget/ComicRackCE). And if you can please contribute to the project.

# Bedetheque Scrapper 2 for ComicRack
Script that scrapes data from Bedetheque.com for ComicRack.

![Bedetheque Scrapper 2 v5 6 Demo](https://user-images.githubusercontent.com/11904426/115951797-b56dbf80-a4b0-11eb-821b-6e97ca2cfca1.gif)

## Cloudflare and the system browser
Bedetheque.com is protected by Cloudflare. When Cloudflare answers with a challenge, `BedethequeFetcher.exe` loads the page in the browser already installed on your computer (Edge, Chrome or Brave). To use a different browser, set its path in the plugin configuration.

- The browser runs on a separate, hidden Windows desktop, so no window appears and ComicRack keeps the focus. If the challenge needs a click, a browser window opens on your desktop: click the checkbox and scraping continues.
- The browser uses its own profile in `%LOCALAPPDATA%\BedethequeScraper2\browser_profile`. It never touches your normal browser profile, passwords or cookies.
- Only the `cf_clearance` cookie and the browser's User-Agent are saved, in `%LOCALAPPDATA%\BedethequeScraper2\clearance.json`. Later requests use them over plain HTTP, without starting the browser.
- The fetcher only loads `https://*.bedetheque.com` pages, and it closes the browser when the scrape ends or the fetcher exits.
- `%LOCALAPPDATA%\BedethequeScraper2\fetcher.log` lists every URL requested, including search terms. It contains no cookie values.
- Delete `%LOCALAPPDATA%\BedethequeScraper2` to reset everything.

### Antivirus warnings
Starting a browser on a hidden desktop and reading a cookie from it over the browser's remote debugging port is also what some malware does. Because of this, antivirus software can flag `BedethequeFetcher.exe`; Microsoft Defender has flagged a development build as `Trojan:Win32/Bearfoos.A!ml`. Its machine-learning heuristic gives that kind of name to unknown programs. The source of the fetcher is in [`tools/BedethequeFetcher.py`](tools/BedethequeFetcher.py), and the exe is built from it by the release workflow. If your antivirus blocks it, restore the file and report it as a false positive, for Defender at <https://www.microsoft.com/wdsi/filesubmission>.


----

##### Other Plugins: 
- ###### [Amazon Scrapper for ComicRack](https://github.com/maforget/ComicRack_AmazonScrapper). A Scrapper for Amazon books (former Comixology library).
- ###### [Keygen for ComicRack](https://github.com/maforget/ComicRackKeygen). A keygen to activate because of the now dead website. Also includes the Android Client, RAR5 Support Pack to enable RAR5 functionality and additional fixes.
- ###### [Data Manager](https://github.com/maforget/CRDataManager) let's you manipulate your data for ComicRack. Fix the various bugs in the latest v2 release.
- ###### [Backup Manager for ComicRack](https://github.com/maforget/cr-backup-manager) Automates the process of saving the ComicRack library file or easy 1 click backup. Updated to support the Community Edition, Portable mode & Alternate Configurations.
- ###### [Find Image Resolution](https://github.com/maforget/ComicRack_FindImageResolution) to determine the resolution of a comic. Use it by right-clicking => Automation => Find Image Resolution (.NET). Configuration are in File => Automation => Find Image Resolution (.NET) Config.
- ###### [fullscreen.py](https://gist.githubusercontent.com/maforget/186a99205140acd3f7d3328ad1466e62/raw/8c7c0ecab28fb9a6037adbe19ff553e3597cccd6/fullscreen.py). It will automatically fullscreen the application when either opening a book or starting the application depending on which you enable). Copy the file in either `%programfiles%\ComicRack\Scripts` or `%appdata%\cYo\ComicRack\Scripts`.
- ###### [comicrack-copy-move-field](https://github.com/maforget/comicrack-copy-move-field). Moves or copies info from one field to another. Can either replace or append to the destination field. Small update from the original to permit dates to be copied or moved.
