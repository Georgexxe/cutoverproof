"""Render the under-three-minute CutoverProof WebMCP demonstration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render_submission_video import (
    ASSETS,
    BRAND,
    BRAND_SOFT,
    FFMPEG,
    FPS,
    H,
    INK,
    LINE,
    MUTED,
    ROOT,
    SUCCESS,
    W,
    WHITE,
    base_slide,
    caption_chunks,
    duration,
    face,
    logo,
    srt_time,
)

VIDEO = ROOT / "submission" / "video"
BUILD = VIDEO / "webmcp-build"
VOICE = VIDEO / "webmcp-voice"


def render(command: list[str]) -> None:
    """Run FFmpeg without flooding CI or agent logs with frame-by-frame progress."""
    quiet_command = [command[0], "-hide_banner", "-loglevel", "error", *command[1:]]
    subprocess.run(quiet_command, check=True)


def title_slide() -> Image.Image:
    image = Image.new("RGBA", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1330, -500, 2320, 490), fill=(56, 71, 233, 145))
    draw.ellipse((-540, 660, 540, 1740), fill=(31, 44, 112, 255))
    logo(image, 112, 88, 84)
    draw.text((218, 130), "CutoverProof", font=face(55, display=True), fill=WHITE, anchor="lm")
    draw.text((112, 300), "PRODUCTION CHANGE CONTROL", font=face(27, 800), fill="#aeb7ff")
    draw.multiline_text(
        (112, 355),
        "Prove the change\nbefore you cut over.",
        font=face(94, display=True),
        fill=WHITE,
        spacing=-4,
    )
    draw.rounded_rectangle((112, 760, 1535, 912), radius=24, fill=(255, 255, 255, 18), outline=(255, 255, 255, 48), width=2)
    draw.text((158, 810), "AGENT", font=face(21, 800), fill="#8793ff")
    draw.text((158, 856), "prepares", font=face(31, 700), fill=INK)
    draw.text((518, 810), "POSTGRESQL", font=face(21, 800), fill="#8793ff")
    draw.text((518, 856), "proves", font=face(31, 700), fill=INK)
    draw.text((1010, 810), "HUMAN", font=face(21, 800), fill="#8793ff")
    draw.text((1010, 856), "authorizes", font=face(31, 700), fill=INK)
    return image


def tools_slide() -> Image.Image:
    image = base_slide()
    draw = ImageDraw.Draw(image, "RGBA")
    logo(image, 88, 58, 62)
    draw.text((170, 91), "The WebMCP authority surface", font=face(52, display=True), fill=INK, anchor="lm")
    draw.text((90, 166), "FIVE CLOSED SCHEMAS · ONE VISIBLE WRITE · ZERO REPAIR OR DEPLOY AUTHORITY", font=face(22, 800), fill=BRAND)
    tools = [
        ("list_migration_contracts", "Read available bounded contracts", "READ ONLY"),
        ("inspect_migration_contract", "Read phases, operations, invariants, authority", "READ ONLY"),
        ("create_change_review_draft", "Create an idempotent human-review draft", "NO EXECUTION"),
        ("read_verified_migration_evidence", "Read verifier-owned result and rows", "READ ONLY"),
        ("open_human_repair_review", "Navigate to a pending human decision", "NO APPROVAL"),
    ]
    positions = [(90, 255, 915, 440), (1005, 255, 1830, 440), (90, 475, 915, 660), (1005, 475, 1830, 660), (548, 695, 1372, 880)]
    for (name, detail, boundary), box in zip(tools, positions, strict=True):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=20, fill=WHITE, outline=LINE, width=2)
        draw.rounded_rectangle((x1 + 25, y1 + 25, x1 + 166, y1 + 61), radius=10, fill=BRAND_SOFT)
        draw.text((x1 + 95, y1 + 44), boundary, font=face(16, 800), fill=BRAND, anchor="mm")
        draw.text((x1 + 25, y1 + 92), name, font=face(26, 800), fill=INK)
        draw.text((x1 + 25, y1 + 137), detail, font=face(21, 500), fill=MUTED)
    draw.rounded_rectangle((300, 930, 1620, 1007), radius=18, fill=INK)
    draw.text((960, 968), "The agent can prepare and explain. It cannot decide or authorize.", font=face(27, 700), fill=WHITE, anchor="mm")
    return image


def end_slide() -> Image.Image:
    image = Image.new("RGBA", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1340, -470, 2310, 500), fill=(56, 71, 233, 150))
    logo(image, 760, 150, 92)
    draw.text((880, 196), "CutoverProof", font=face(60, display=True), fill=WHITE, anchor="lm")
    draw.text((960, 430), "A trust control plane", font=face(78, display=True), fill=WHITE, anchor="mm")
    draw.text((960, 525), "for agent-led production change.", font=face(70, display=True), fill="#8995ff", anchor="mm")
    draw.rounded_rectangle((420, 690, 1500, 706), radius=8, fill=BRAND)
    draw.text((960, 800), "Declared contract  •  Bounded experiments  •  Independent proof  •  Human authority", font=face(29, 700), fill="#d0d5ff", anchor="mm")
    return image


def make_frame(beat: dict[str, str], destination: Path) -> None:
    visual = beat["visual"]
    if visual == "title":
        image = title_slide()
    elif visual == "tools":
        image = tools_slide()
    elif visual == "end":
        image = end_slide()
    else:
        # Product captures stay visually authentic. Narration and the separate
        # subtitle file carry the explanation; no renderer label obscures UI.
        image = Image.open(VIDEO / visual).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    image.convert("RGB").save(destination, "PNG", optimize=True)


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    plan = json.loads((VIDEO / "webmcp-narration.json").read_text(encoding="utf-8"))
    clips: list[Path] = []
    captions: list[str] = []
    cursor = 0.0
    caption_number = 1
    for index, beat in enumerate(plan, start=1):
        frame = BUILD / f"{index:02d}-{beat['id']}.png"
        audio = VOICE / f"{beat['id']}.wav"
        clip = BUILD / f"{index:02d}-{beat['id']}.mp4"
        make_frame(beat, frame)
        audio_duration = duration(audio)
        clip_duration = audio_duration + 0.8
        render([
            str(FFMPEG), "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(frame), "-i", str(audio),
            "-filter_complex",
            f"[0:v]zoompan=z='min(zoom+0.00006,1.018)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p[v];"
            "[1:a]volume=-1dB,highpass=f=55,lowpass=f=8000,loudnorm=I=-17:TP=-2:LRA=9,adelay=300:all=1,apad=pad_dur=1[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{clip_duration:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(clip),
        ])
        clips.append(clip)
        chunks = caption_chunks(beat["text"])
        weights = [max(1, len(chunk.split())) for chunk in chunks]
        local = cursor + 0.3
        for chunk, weight in zip(chunks, weights, strict=True):
            span = audio_duration * weight / sum(weights)
            captions.append(f"{caption_number}\n{srt_time(local)} --> {srt_time(local + span)}\n{chunk}\n")
            caption_number += 1
            local += span
        cursor += clip_duration
    concat = BUILD / "clips.ffconcat"
    concat.write_text("ffconcat version 1.0\n" + "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clips) + "\n", encoding="utf-8")
    output = VIDEO / "CutoverProof_WebMCP_Demo.mp4"
    render([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(output)])
    output.with_suffix(".srt").write_text("\n".join(captions), encoding="utf-8")
    print(f"COMPLETE {output} ({duration(output):.2f}s)")


if __name__ == "__main__":
    main()
