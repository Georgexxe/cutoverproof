param(
    [string]$Capture = ".\submission\video\CutoverProof_WebMCP_Live_Capture_RAW.mp4",
    [string]$Narration = ".\submission\video\webmcp-live-narration.json",
    [string]$VoiceDir = ".\submission\video\webmcp-live-voice",
    [string]$Captions = ".\submission\video\webmcp-live.ass",
    [string]$Output = ".\submission\video\CutoverProof_WebMCP_Submission_FINAL.mp4"
)

$ErrorActionPreference = "Stop"
$ffmpeg = "C:\Program Files\FFmpeg\8.1.2\bin\ffmpeg.exe"
$beats = Get-Content -LiteralPath $Narration -Raw | ConvertFrom-Json
$arguments = @("-hide_banner", "-loglevel", "error", "-y", "-i", $Capture)
$filterParts = @()
$audioLabels = @()

for ($index = 0; $index -lt $beats.Count; $index++) {
    $beat = $beats[$index]
    $arguments += @("-i", (Join-Path $VoiceDir "$($beat.id).wav"))
    $delay = [int]([double]$beat.start * 1000)
    $inputIndex = $index + 1
    $label = "voice$inputIndex"
    $filterParts += "[${inputIndex}:a]adelay=$delay`:all=1,volume=-1dB,highpass=f=55,lowpass=f=8000[$label]"
    $audioLabels += "[$label]"
}

$captionFilter = $Captions.Replace('\', '/').Replace(':', '\:')
$filterParts += "[0:v]trim=start=0:end=157,setpts=PTS-STARTPTS,ass='$captionFilter'[video]"
$filterParts += "$($audioLabels -join '')amix=inputs=$($beats.Count):duration=longest:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=8,apad=pad_dur=2[audio]"

$arguments += @(
    "-filter_complex", ($filterParts -join ";"),
    "-map", "[video]", "-map", "[audio]", "-t", "157",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-movflags", "+faststart", $Output
)

& $ffmpeg @arguments
if ($LASTEXITCODE -ne 0) { throw "FFmpeg failed with exit code $LASTEXITCODE" }
Write-Output "COMPLETE $Output"
