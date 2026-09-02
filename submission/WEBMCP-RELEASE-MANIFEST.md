# CutoverProof WebMCP release manifest

Generated and verified on 2026-09-02.

## Submission video

- File: `submission/video/CutoverProof_WebMCP_Demo.mp4`
- Runtime: 150.284333 seconds (2:30.284)
- Container: MP4
- Video: H.264, 1920×1080, 24 fps
- Audio: AAC, 48 kHz, mono
- Size: 4,577,406 bytes
- Decode verification: FFmpeg completed a full decode with zero reported errors
- SHA-256: `BD6A8DA172B452FB87782359331A59CF46D291F7DD0926C7358C5C03F908D628`

## Captions

- File: `submission/video/CutoverProof_WebMCP_Demo.srt`
- Cue count: 41
- Last cue ends: 00:02:29.727
- SHA-256: `C501582D219B4EA3FEE7C0465EF27BADA4E54F08A87CA2BC9B6A79B770D47B4C`

## Verification commands

```powershell
& 'C:\Program Files\FFmpeg\8.1.2\bin\ffprobe.exe' -v error -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels -of json submission\video\CutoverProof_WebMCP_Demo.mp4
& 'C:\Program Files\FFmpeg\8.1.2\bin\ffmpeg.exe' -hide_banner -v error -i submission\video\CutoverProof_WebMCP_Demo.mp4 -f null NUL
Get-FileHash -Algorithm SHA256 submission\video\CutoverProof_WebMCP_Demo.mp4
Get-FileHash -Algorithm SHA256 submission\video\CutoverProof_WebMCP_Demo.srt
```

The narration source is `submission/video/webmcp-narration.json`. The render pipeline is `scripts/render_webmcp_video.py`; local offline voice generation is `scripts/render_webmcp_voice.ps1`.
