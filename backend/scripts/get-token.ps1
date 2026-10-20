$envFile = Join-Path $PSScriptRoot "..\.env"
$vars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+?)\s*=\s*(.*)$') { $vars[$matches[1]] = $matches[2].Trim('"') }
}

$email = Read-Host "Email (e.g. usera@test.com)"
$password = Read-Host "Password" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))

$body = @{ email = $email; password = $plain } | ConvertTo-Json
$url = ($vars["SUPABASE_URL"]).TrimEnd("/") + "/auth/v1/token?grant_type=password"

$resp = Invoke-RestMethod -Method Post -Uri $url `
    -Headers @{ apikey = $vars["SUPABASE_ANON_KEY"]; "Content-Type" = "application/json" } `
    -Body $body

Write-Host "`nACCESS TOKEN (valid ~1 hour):`n"
Write-Host $resp.access_token