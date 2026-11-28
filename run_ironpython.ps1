# Runs a Python script with ComicRack CE's own IronPython 2.7 (Windows
# PowerShell 5.1, .NET Framework), so the plugin tests use the same runtime
# as ComicRack. tests\ is put on sys.path.
#
#   powershell -NoProfile -STA -ExecutionPolicy Bypass -File .\run_ironpython.ps1 tests\test_x_ipy.py [args...]
#
# Exit code: 0 if the script printed "0 failure(s)" or no failure line, and
# raised no exception; 1 otherwise.
param([Parameter(Mandatory = $true)][string]$Script,
      [Parameter(ValueFromRemainingArguments = $true)][string[]]$ScriptArgs)
$cr = 'C:\Program Files\ComicRack Community Edition'
foreach ($dll in 'Microsoft.Scripting', 'Microsoft.Dynamic', 'IronPython', 'IronPython.Modules') {
    Add-Type -Path "$cr\$dll.dll"
}
$engine = [IronPython.Hosting.Python]::CreateEngine()
$paths = $engine.GetSearchPaths()
$paths.Add((Join-Path $PSScriptRoot 'tests'))
$paths.Add("$cr\Lib")
$engine.SetSearchPaths($paths)
$sys = [IronPython.Hosting.Python]::GetSysModule($engine)
$argv = New-Object IronPython.Runtime.List
$argv.append((Resolve-Path $Script).Path)
foreach ($a in $ScriptArgs) { $argv.append($a) }
$sys.argv = $argv
$stream = New-Object System.IO.MemoryStream
$utf8 = New-Object System.Text.UTF8Encoding $false     # no byte-order mark
$engine.Runtime.IO.SetOutput($stream, $utf8)
$engine.Runtime.IO.SetErrorOutput($stream, $utf8)
$failed = $false
try {
    $engine.ExecuteFile((Resolve-Path $Script).Path) | Out-Null
} catch {
    $inner = if ($_.Exception.InnerException) { $_.Exception.InnerException } else { $_.Exception }
    $failed = $true
    try {
        # ScriptEngine.GetService<ExceptionOperations>(params object[]) is
        # generic, which PowerShell 5 can't call directly
        $get = $engine.GetType().GetMethod('GetService').MakeGenericMethod(
            [Microsoft.Scripting.Hosting.ExceptionOperations])
        $ops = $get.Invoke($engine, [object[]]@(, [object[]]@()))
        $msg = $ops.FormatException($inner)
    } catch {
        $msg = $inner.ToString()
    }
}
$out = [Text.Encoding]::UTF8.GetString($stream.ToArray())
$out
if ($failed) { "PYTHON ERROR: $msg" }
if ($failed -or $out -match '(?m)^[1-9]\d* failure\(s\)') { exit 1 }
exit 0
