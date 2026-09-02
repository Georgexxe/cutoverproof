param(
    [string]$Plan = ".\submission\video\webmcp-narration.json",
    [string]$Output = ".\submission\video\webmcp-voice",
    [string]$Voice = "Microsoft Mark"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
New-Item -ItemType Directory -Force -Path $Output | Out-Null
$beats = Get-Content -LiteralPath $Plan -Raw | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice($Voice)
$synth.Rate = 0
$synth.Volume = 100
try {
    foreach ($beat in $beats) {
        Write-Output "Synthesizing $($beat.id)"
        $destination = Join-Path (Resolve-Path -LiteralPath $Output).Path "$($beat.id).wav"
        $synth.SetOutputToWaveFile($destination)
        $synth.Speak($beat.text)
    }
} finally {
    $synth.SetOutputToNull()
    $synth.Dispose()
}
Write-Output "COMPLETE $Output"
