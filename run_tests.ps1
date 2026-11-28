# Runs every tests\test_*.py, then builds the plugin. Exit code 1 if
# anything failed.
#   - test_*_ipy.py run in ComicRack CE's IronPython (the plugin side);
#   - the others run in CPython 3 (the fetcher side).
#   - *_live* tests use bedetheque.com, the system browser and the built
#     BedethequeFetcher.exe. They run only with -Live. A fresh browser profile
#     can get a Cloudflare challenge that needs a click in the window shown.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\run_tests.ps1 [name-filter] [-Live] [-NoBuild]
param([string]$Filter = '', [switch]$Live, [switch]$NoBuild)
Set-Location $PSScriptRoot
$failed = @()
$tests = Get-ChildItem tests\test_*.py | Where-Object {
    $_.Name -like "*$Filter*" -and ($Live -or $_.Name -notlike '*_live*')
}
foreach ($t in $tests) {
    "`n===== $($t.Name)"
    if ($t.Name -like '*_ipy.py') {
        powershell -NoProfile -STA -ExecutionPolicy Bypass -File .\run_ironpython.ps1 $t.FullName
    } else {
        python $t.FullName
    }
    if ($LASTEXITCODE -ne 0) { $failed += $t.Name }
}
if (-not $NoBuild) {
    "`n===== build"
    python CreatePlugin.py
    if ($LASTEXITCODE -ne 0) { $failed += 'build' }
}
if ($failed.Count) { "`nFAILED: $($failed -join ', ')"; exit 1 }
"`nALL PASSED"
