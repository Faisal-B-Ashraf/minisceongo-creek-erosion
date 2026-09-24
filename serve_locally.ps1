# Opens the walk-through and project assistant using only Windows PowerShell (no Python needed).
# Serves the docs folder at http://localhost:8765/ and opens it in the default browser.
# usage:  powershell -ExecutionPolicy Bypass -File serve_locally.ps1 [port] [--no-browser]
# Close this window to stop.
$Port = 8765
$OpenBrowser = $true
foreach ($a in $args) {
    if ($a -match '^\d+$') { $Port = [int]$a }
    elseif ($a -eq '--no-browser') { $OpenBrowser = $false }
}
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'docs'))
$types = @{
    '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8'; '.css' = 'text/css; charset=utf-8'
    '.json' = 'application/json; charset=utf-8'; '.md' = 'text/markdown; charset=utf-8'; '.webp' = 'image/webp'
    '.png' = 'image/png'; '.svg' = 'image/svg+xml'; '.ico' = 'image/x-icon'
}
$prefix = "http://localhost:$Port/"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($prefix)
try { $listener.Start() }
catch { Write-Host "Could not start on port $Port - is it already open in another window?"; Read-Host 'Press Enter to close'; exit 1 }
Write-Host "Serving $root"
Write-Host "Open $prefix   (keep this window open while you use it; close it to stop)"
if ($OpenBrowser) { Start-Process $prefix }
try {
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $res = $ctx.Response
        try {
            $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
            if ([string]::IsNullOrEmpty($rel)) { $rel = 'index.html' }
            $path = [IO.Path]::GetFullPath((Join-Path $root $rel))
            if ($path.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $path -PathType Leaf)) {
                $ext = [IO.Path]::GetExtension($path).ToLowerInvariant()
                $res.ContentType = if ($types.ContainsKey($ext)) { $types[$ext] } else { 'application/octet-stream' }
                $bytes = [IO.File]::ReadAllBytes($path)
            }
            else {
                $res.StatusCode = 404
                $bytes = [Text.Encoding]::UTF8.GetBytes('Not found')
            }
            $res.ContentLength64 = $bytes.Length
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
        }
        catch { }
        finally { $res.OutputStream.Close() }
    }
}
finally { $listener.Stop() }
