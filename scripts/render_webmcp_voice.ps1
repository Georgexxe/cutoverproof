param(
    [string]$Plan = ".\submission\video\webmcp-narration.json",
    [string]$Output = ".\submission\video\webmcp-voice",
    [string]$Project = "project-ca8af2fe-5aff-496a-bd8"
)

$ErrorActionPreference = "Stop"
$gcloud = "C:\Users\SURFACE\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$voiceName = "en-GB-Chirp3-HD-Charon"
$language = "en-GB"
$endpoint = "https://texttospeech.googleapis.com/v1/text:synthesize"

New-Item -ItemType Directory -Force -Path $Output | Out-Null
$token = (& $gcloud auth print-access-token).Trim()
if (-not $token) { throw "Google Cloud access token is unavailable." }

$headers = @{
    Authorization = "Bearer $token"
    "x-goog-user-project" = $Project
}

$beats = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
$manifest = @()
foreach ($beat in $beats) {
    $path = Join-Path (Resolve-Path -LiteralPath $Output).Path "$($beat.id).wav"
    if (Test-Path -LiteralPath $path) {
        Write-Output "Reusing $($beat.id)"
        $manifest += [ordered]@{ id = $beat.id; audio = "$($beat.id).wav"; voice = $voiceName }
        continue
    }
    Write-Output "Synthesizing $($beat.id)"
    $body = @{
        input = @{ text = $beat.text }
        voice = @{ languageCode = $language; name = $voiceName }
        audioConfig = @{ audioEncoding = "LINEAR16"; sampleRateHertz = 24000 }
    } | ConvertTo-Json -Depth 6 -Compress
    $response = Invoke-RestMethod -Method Post -Uri $endpoint -Headers $headers -ContentType "application/json" -Body $body
    [IO.File]::WriteAllBytes($path, [Convert]::FromBase64String($response.audioContent))
    $manifest += [ordered]@{ id = $beat.id; audio = "$($beat.id).wav"; voice = $voiceName }
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Output "voice_manifest.json") -Encoding UTF8
Write-Output "COMPLETE $Output"
