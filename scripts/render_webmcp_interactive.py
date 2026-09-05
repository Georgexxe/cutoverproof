"""Render a continuous, click-led CutoverProof WebMCP demo.

The film stays inside the product. It combines the current polished Home and
human-gate captures with the successful live assessment/evidence/replay take,
then adds the same high-visibility green pointer language used by the team's
earlier demos.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "submission" / "video"
BUILD = VIDEO / "webmcp-interactive-build"
FFMPEG = Path("C:/Program Files/FFmpeg/8.1.2/bin/ffmpeg.exe")
FFPROBE = Path("C:/Program Files/FFmpeg/8.1.2/bin/ffprobe.exe")

W, H, FPS, DURATION = 1920, 1080, 24, 157.0
CURSOR_W, CURSOR_H = 640, 360
SCALE = W / CURSOR_W


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            str(FFPROBE),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return float(result.stdout.strip())


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


# Pointer keyframes. Coordinates are on the 1920x1080 product canvas.
POINTER = [
    (0.0, 1848, 45),
    (3.0, 1488, 172),
    (9.0, 1488, 172),
    (13.0, 760, 706),
    (17.0, 1488, 172),
    (21.0, 758, 662),
    (26.0, 1068, 662),
    (31.0, 1370, 662),
    (36.0, 1488, 172),
    (42.0, 1010, 1018),
    (47.0, 730, 1018),
    (53.0, 1480, 1045),
    (57.0, 1480, 1045),
    (59.0, 700, 610),
    (62.0, 838, 610),
    (65.0, 974, 610),
    (68.0, 1120, 610),
    (71.5, 1155, 777),
    (74.0, 1538, 783),
    (80.0, 1560, 150),
    (86.0, 1700, 150),
    (91.0, 1600, 255),
    (96.0, 760, 465),
    (101.0, 750, 712),
    (106.0, 1405, 767),
    (110.0, 805, 448),
    (114.0, 805, 550),
    (118.0, 805, 650),
    (122.0, 760, 835),
    (127.0, 1252, 838),
    (130.0, 960, 705),
    (136.5, 960, 705),
    (139.0, 1185, 790),
    (144.0, 1810, 332),
    (145.0, 1400, 455),
    (151.0, 1460, 330),
    (157.0, 1460, 330),
]

CLICKS = [9.0, 26.0, 36.0, 56.7, 71.5, 106.0, 127.0, 130.0, 139.0, 145.0]


def pointer_position(t: float) -> tuple[float, float]:
    for index in range(len(POINTER) - 1):
        t0, x0, y0 = POINTER[index]
        t1, x1, y1 = POINTER[index + 1]
        if t <= t1:
            amount = ease((t - t0) / max(0.001, t1 - t0))
            return x0 + (x1 - x0) * amount, y0 + (y1 - y0) * amount
    return POINTER[-1][1], POINTER[-1][2]


def render_cursor(path: Path) -> None:
    command = [
        str(FFMPEG),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        f"{CURSOR_W}x{CURSOR_H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "qtrle",
        "-pix_fmt",
        "argb",
        str(path),
    ]
    process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE)
    assert process.stdin is not None
    total_frames = round(DURATION * FPS)
    for frame_index in range(total_frames):
        t = frame_index / FPS
        x, y = pointer_position(t)
        x /= SCALE
        y /= SCALE
        frame = Image.new("RGBA", (CURSOR_W, CURSOR_H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame, "RGBA")

        # Click pulse: a quick lime ring that expands and disappears.
        for click_time in CLICKS:
            age = t - click_time
            if 0.0 <= age <= 0.52:
                progress = age / 0.52
                radius = 7 + 10 * progress
                alpha = round(220 * (1.0 - progress))
                draw.ellipse(
                    (x - radius, y - radius, x + radius, y + radius),
                    outline=(25, 220, 126, alpha),
                    width=2,
                )

        # A crisp, branded pointer dot with a soft halo and dark outline.
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(25, 220, 126, 52))
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(11, 17, 39, 245))
        draw.ellipse((x - 3.6, y - 3.6, x + 3.6, y + 3.6), fill=(42, 232, 143, 255))
        process.stdin.write(frame.tobytes())

    process.stdin.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def build_background(path: Path) -> None:
    home = VIDEO / "frames" / "40-webmcp-home.png"
    draft = VIDEO / "frames" / "41-agent-review-handoff.png"
    gate = VIDEO / "frames" / "42-human-run-review.png"
    raw = VIDEO / "CutoverProof_WebMCP_Live_Capture_RAW.mp4"
    verified = VIDEO / "frames" / "28-repair-verified.png"

    filters = (
        f"[0:v]fps={FPS},scale={W}:{H},setsar=1,trim=duration=42,setpts=PTS-STARTPTS[v0];"
        f"[1:v]fps={FPS},scale={W}:{H},setsar=1,trim=duration=15,setpts=PTS-STARTPTS[v1];"
        f"[2:v]fps={FPS},scale={W}:{H},setsar=1,trim=duration=15,setpts=PTS-STARTPTS[v2];"
        f"[3:v]trim=start=74:end=148,setpts=PTS-STARTPTS,fps={FPS},"
        "drawbox=x=0:y=1000:w=1920:h=80:color=white:t=fill[v3];"
        f"[4:v]fps={FPS},scale={W}:{H},setsar=1,trim=duration=11,setpts=PTS-STARTPTS[v4];"
        "[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0,format=yuv420p[out]"
    )
    run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-loop",
            "1",
            "-i",
            str(home),
            "-loop",
            "1",
            "-i",
            str(draft),
            "-loop",
            "1",
            "-i",
            str(gate),
            "-i",
            str(raw),
            "-loop",
            "1",
            "-i",
            str(verified),
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-t",
            f"{DURATION:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(path),
        ]
    )


def finish(background: Path, cursor: Path, output: Path) -> None:
    beats = json.loads((VIDEO / "webmcp-live-narration.json").read_text(encoding="utf-8"))
    command = [
        str(FFMPEG),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(background),
        "-i",
        str(cursor),
    ]
    filters: list[str] = [
        "[1:v]scale=1920:1080[cur]",
        "[0:v][cur]overlay=0:0:format=auto,ass='submission/video/webmcp-interactive.ass'[video]",
    ]
    labels: list[str] = []
    for input_index, beat in enumerate(beats, start=2):
        command.extend(["-i", str(VIDEO / "webmcp-live-voice" / f"{beat['id']}.wav")])
        delay = round(float(beat["start"]) * 1000)
        label = f"voice{input_index}"
        filters.append(
            f"[{input_index}:a]adelay={delay}:all=1,volume=-1dB,"
            f"highpass=f=55,lowpass=f=8000[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=8,apad=pad_dur=2[audio]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[video]",
            "-map",
            "[audio]",
            "-t",
            f"{DURATION:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    run(command)


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    background = BUILD / "continuous-product-take.mp4"
    cursor = BUILD / "green-pointer.mov"
    output = VIDEO / "CutoverProof_WebMCP_Submission_INTERACTIVE.mp4"

    build_background(background)
    render_cursor(cursor)
    finish(background, cursor, output)
    print(f"COMPLETE {output} ({probe_duration(output):.2f}s)")


if __name__ == "__main__":
    main()
