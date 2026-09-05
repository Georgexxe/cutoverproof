"""Render the motion-led CutoverProof WebMCP submission film.

The film deliberately uses clean product captures for the visual story.  A real
Windows cursor is composited only where a human click matters, so the browser
automation cursor and its status toast never appear in the submission.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from render_submission_video import (
    ASSETS,
    BRAND,
    BRAND_SOFT,
    FFMPEG,
    FFPROBE,
    H,
    INK,
    LINE,
    MUTED,
    ROOT,
    SUCCESS,
    W,
    WHITE,
    caption_chunks,
    duration,
    face,
    logo,
    srt_time,
)


VIDEO = ROOT / "submission" / "video"
FRAMES = VIDEO / "frames"
VOICE = VIDEO / "webmcp-voice"
BUILD = VIDEO / "webmcp-cinematic-build"
PLAN = VIDEO / "webmcp-narration.json"
OUTPUT = VIDEO / "CutoverProof_WebMCP_Submission_CINEMATIC.mp4"
FPS = 24


def run(command: list[str]) -> None:
    subprocess.run([command[0], "-hide_banner", "-loglevel", "error", *command[1:]], check=True)


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def ramp(now: float, start: float, span: float = 0.7) -> float:
    return ease((now - start) / span)


def lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def load_shot(name: str) -> Image.Image:
    return Image.open(FRAMES / name).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)


SHOTS = {
    name: load_shot(name)
    for name in (
        "22-live-progress.png",
        "24-imported-decision.png",
        "25-readable-evidence.png",
        "26-detailed-timeline.png",
        "27-human-approval.png",
        "28-repair-verified.png",
        "31-repaired-replay-focus.png",
        "32-live-progress-focus.png",
        "40-webmcp-home.png",
        "41-agent-review-handoff.png",
        "42-human-run-review.png",
    )
}


def windows_cursor() -> Image.Image:
    """Decode the highest-resolution BGRA frame from Windows' real Aero cursor."""
    data = Path("C:/Windows/Cursors/aero_arrow.cur").read_bytes()
    count = struct.unpack_from("<H", data, 4)[0]
    entries: list[tuple[int, int, int, int]] = []
    for index in range(count):
        offset = 6 + index * 16
        width = data[offset] or 256
        height = data[offset + 1] or 256
        size, image_offset = struct.unpack_from("<II", data, offset + 8)
        entries.append((width * height, width, size, image_offset))
    _, width, _, image_offset = max(entries)
    header_size, dib_width, dib_height, _, bits = struct.unpack_from("<IiiHH", data, image_offset)
    if bits != 32 or dib_width != width:
        raise RuntimeError("Unsupported Windows cursor format")
    height = abs(dib_height) // 2
    pixels = data[image_offset + header_size : image_offset + header_size + width * height * 4]
    image = Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return image.resize((58, 58), Image.Resampling.LANCZOS)


CURSOR = windows_cursor()


def dark_base() -> Image.Image:
    image = Image.new("RGB", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1330, -510, 2320, 480), fill=(56, 71, 233, 145))
    draw.ellipse((-560, 650, 540, 1750), fill=(31, 44, 112, 255))
    return image


def light_base() -> Image.Image:
    image = Image.new("RGB", (W, H), "#fbfbfd")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1390, -500, 2350, 460), fill=(56, 71, 233, 22))
    draw.ellipse((-520, 650, 520, 1690), fill=(56, 71, 233, 16))
    return image


def label(image: Image.Image, text: str, width: int = 900) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((52, 38, width, 106), radius=18, fill=(13, 18, 39, 236))
    draw.text((82, 73), text, font=face(25, 800), fill=WHITE, anchor="lm")


def crop_motion(source: Image.Image, amount: float, start: tuple[int, int, int, int], end: tuple[int, int, int, int]) -> Image.Image:
    p = ease(amount)
    box = tuple(round(lerp(a, b, p)) for a, b in zip(start, end, strict=True))
    return source.crop(box).resize((W, H), Image.Resampling.BILINEAR)


def crossfade(first: Image.Image, second: Image.Image, amount: float) -> Image.Image:
    return Image.blend(first, second, ease(amount))


def cursor_at(image: Image.Image, start: tuple[int, int], end: tuple[int, int], amount: float, click: bool = False) -> None:
    p = ease(amount)
    x = round(lerp(start[0], end[0], p))
    y = round(lerp(start[1], end[1], p))
    image.paste(CURSOR, (x, y), CURSOR)
    if click:
        draw = ImageDraw.Draw(image, "RGBA")
        draw.ellipse((x - 13, y - 13, x + 38, y + 38), outline=(56, 71, 233, 175), width=4)


def stat_card(image: Image.Image, box: tuple[int, int, int, int], value: str, title: str, subtitle: str, amount: float, accent: str = BRAND) -> None:
    p = ease(amount)
    if p <= 0:
        return
    x1, y1, x2, y2 = box
    y_shift = round((1 - p) * 42)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.rounded_rectangle((x1, y1 + y_shift, x2, y2 + y_shift), radius=22, fill=(255, 255, 255, round(246 * p)), outline=accent, width=3)
    draw.text((x1 + 30, y1 + 48 + y_shift), value, font=face(58, 800), fill=accent, anchor="lm")
    draw.text((x1 + 30, y1 + 102 + y_shift), title, font=face(24, 800), fill=INK, anchor="lm")
    draw.text((x1 + 30, y1 + 140 + y_shift), subtitle, font=face(19, 500), fill=MUTED, anchor="lm")
    image.paste(layer, (0, 0), layer)


def title_frame(now: float, total: float) -> Image.Image:
    image = dark_base()
    draw = ImageDraw.Draw(image, "RGBA")
    mark = Image.open(ROOT / "web" / "src" / "assets" / "cutoverproof-mark.png").convert("RGBA")
    mark.thumbnail((84, 84), Image.Resampling.LANCZOS)
    image.paste(mark, (112, 88), mark)
    draw.text((218, 130), "CutoverProof", font=face(55, display=True), fill=WHITE, anchor="lm")
    draw.text((112, 292), "PRODUCTION CHANGE CONTROL", font=face(27, 800), fill="#aeb7ff")
    draw.multiline_text((112, 350), "Prove the change\nbefore you cut over.", font=face(94, display=True), fill=WHITE, spacing=-4)
    draw.text((112, 646), "One live workflow. Three independent authorities.", font=face(34, 700), fill="#d9ddff")
    stats_start = min(8.0, total * 0.42)
    targets = (("5", "WEBMCP TOOLS", "closed schemas"), ("4", "CANDIDATES", "bounded search"), ("8", "OPERATIONS", "declared only"), ("1", "INVARIANT", "PostgreSQL-owned"))
    for index, (value, title, subtitle) in enumerate(targets):
        progress = ramp(now, stats_start + index * 0.35, 0.65)
        shown = str(round(int(value) * progress))
        stat_card(image, (112 + index * 430, 770, 502 + index * 430, 958), shown, title, subtitle, progress)
    return image


def authorities_frame(now: float, total: float) -> Image.Image:
    source = SHOTS["40-webmcp-home.png"]
    image = crop_motion(source, now / total, (0, 0, W, H), (430, 115, 1690, 824))
    label(image, "ONE DECISION · THREE INDEPENDENT AUTHORITIES", 1010)
    if now > total * 0.42:
        cards = (("AGENT", "prepares"), ("POSTGRESQL", "proves"), ("HUMAN", "authorizes"))
        for index, (head, action) in enumerate(cards):
            p = ramp(now, total * 0.42 + index * 0.5, 0.7)
            x1 = 135 + index * 590
            stat_card(image, (x1, 790, x1 + 520, 982), action, head, "authority stays separated", p, SUCCESS if index == 1 else BRAND)
    return image


TOOLS = [
    ("list_migration_contracts", "READ", "discover bounded contracts"),
    ("inspect_migration_contract", "READ", "inspect phases and authority"),
    ("create_change_review_draft", "WRITE", "creates review, never execution"),
    ("read_verified_migration_evidence", "READ", "reads verifier-owned evidence"),
    ("open_human_repair_review", "NAVIGATE", "opens review, never approves"),
]


def tools_frame(now: float, total: float) -> Image.Image:
    image = light_base()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((92, 90), "The WebMCP authority surface", font=face(58, display=True), fill=INK)
    draw.text((92, 164), "FIVE CLOSED SCHEMAS · ZERO REPAIR, VERDICT, SQL, OR DEPLOY AUTHORITY", font=face(22, 800), fill=BRAND)
    positions = ((92, 255, 910, 430), (1010, 255, 1828, 430), (92, 470, 910, 645), (1010, 470, 1828, 645), (550, 685, 1370, 860))
    for index, ((name, boundary, detail), box) in enumerate(zip(TOOLS, positions, strict=True)):
        p = ramp(now, 1.0 + index * 1.25, 0.75)
        if p <= 0:
            continue
        x1, y1, x2, y2 = box
        shift = round((1 - p) * 70)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer, "RGBA")
        ld.rounded_rectangle((x1, y1 + shift, x2, y2 + shift), radius=20, fill=(255, 255, 255, round(250 * p)), outline=LINE, width=2)
        ld.rounded_rectangle((x1 + 24, y1 + 24 + shift, x1 + 170, y1 + 62 + shift), radius=10, fill=BRAND_SOFT)
        ld.text((x1 + 97, y1 + 44 + shift), boundary, font=face(17, 800), fill=BRAND, anchor="mm")
        ld.text((x1 + 24, y1 + 96 + shift), name, font=face(25, 800), fill=INK)
        ld.text((x1 + 24, y1 + 136 + shift), detail, font=face(20, 500), fill=MUTED)
        image.paste(layer, (0, 0), layer)
    if now > total - 4.0:
        p = ramp(now, total - 4.0, 0.7)
        draw.rounded_rectangle((300, 914, 1620, 1000), radius=18, fill=(13, 18, 39, round(245 * p)))
        draw.text((960, 956), "The agent prepares. PostgreSQL proves. A human authorizes.", font=face(29, 700), fill=WHITE, anchor="mm")
    return image


def handoff_frame(now: float, total: float) -> Image.Image:
    first = crop_motion(SHOTS["40-webmcp-home.png"], min(1, now / 6), (0, 0, W, H), (390, 290, 1740, 1050))
    second = crop_motion(SHOTS["41-agent-review-handoff.png"], min(1, max(0, (now - 6) / 7)), (210, 202, 1770, 1080), (410, 349, 1710, 1080))
    image = first if now < 5.3 else crossfade(first, second, (now - 5.3) / 1.1)
    label(image, "WEBMCP CREATES A VISIBLE REVIEW · NOTHING EXECUTES", 1070)
    if now > 8:
        stat_card(image, (116, 790, 640, 985), "DRAFT", "IDEMPOTENT HANDOFF", "visible in the engineer's workspace", ramp(now, 8, 0.7))
    return image


def human_gate_frame(now: float, total: float) -> Image.Image:
    gate = crop_motion(SHOTS["42-human-run-review.png"], min(1, now / 8), (0, 0, W, H), (360, 160, 1560, 835))
    label(gate, "A HUMAN MUST START THE BOUNDED SANDBOX RUN", 960)
    if now < 9.5:
        cursor_at(gate, (1710, 245), (1325, 965), min(1, max(0, (now - 4.0) / 4.5)), click=8.0 < now < 8.35)
        return gate
    progress = crop_motion(SHOTS["32-live-progress-focus.png"], min(1, (now - 9.5) / max(1, total - 9.5)), (0, 0, W, H), (210, 70, 1780, 953))
    label(progress, "REAL JOB STATE · VALIDATE → PLAN → EXECUTE → VERIFY → EVIDENCE", 1250)
    return crossfade(gate, progress, (now - 9.5) / 0.8)


def evidence_frame(now: float, total: float) -> Image.Image:
    if now < total * 0.34:
        image = crop_motion(SHOTS["24-imported-decision.png"], now / (total * 0.34), (0, 0, W, H), (520, 90, 1660, 731))
        label(image, "POSTGRESQL BLOCKS CUTOVER WITH A COUNTEREXAMPLE", 1050)
        stat_card(image, (1270, 730, 1810, 970), "1", "VIOLATING ROW", "row 42 · shipped vs pending", ramp(now, 2.1, 0.8), "#e23a35")
        return image
    if now < total * 0.68:
        local = (now - total * 0.34) / (total * 0.34)
        image = crop_motion(SHOTS["25-readable-evidence.png"], local, (0, 0, W, H), (850, 90, 1510, 1000))
        label(image, "READ-ONLY INVARIANT RETURNS THE EXACT FAILING ROW", 1090)
        return image
    local = (now - total * 0.68) / (total * 0.32)
    image = crop_motion(SHOTS["26-detailed-timeline.png"], local, (0, 0, W, H), (0, 115, 1530, 976))
    label(image, "THE AUDIT RECORD BINDS SCHEDULE, EVIDENCE, AND VERDICT", 1110)
    return image


def approval_frame(now: float, total: float) -> Image.Image:
    if now < total * 0.42:
        image = crop_motion(SHOTS["27-human-approval.png"], now / (total * 0.42), (0, 0, W, H), (360, 160, 1560, 835))
        label(image, "NAMED HUMAN APPROVAL · ONE ALLOW-LISTED SANDBOX REPAIR", 1170)
        cursor_at(image, (1710, 245), (1325, 965), min(1, max(0, (now - 3.0) / 4.0)), click=6.7 < now < 7.05)
        return image
    if now < total * 0.68:
        local = (now - total * 0.42) / (total * 0.26)
        image = crop_motion(SHOTS["28-repair-verified.png"], local, (0, 0, W, H), (500, 80, 1700, 755))
        label(image, "THE IDENTICAL FAILING SCHEDULE RUNS AGAIN", 930)
        return image
    local = (now - total * 0.68) / (total * 0.32)
    image = crop_motion(SHOTS["31-repaired-replay-focus.png"], local, (0, 0, W, H), (340, 70, 1700, 835))
    label(image, "REPAIR VERIFIED IN SANDBOX", 690)
    stat_card(image, (1260, 755, 1810, 985), "0", "VIOLATING ROWS", "same schedule · independent replay", ramp(now, total * 0.72, 0.7), SUCCESS)
    return image


def close_frame(now: float, total: float) -> Image.Image:
    split = total * 0.58
    if now < split:
        image = light_base()
        draw = ImageDraw.Draw(image, "RGBA")
        draw.text((95, 90), "Measured, not merely claimed", font=face(62, display=True), fill=INK)
        draw.text((95, 170), "Equal model, facts, seed, and four-candidate execution budget", font=face(27, 500), fill=MUTED)
        cards = (
            ("3 / 3", "UNSAFE RECALL", "specialised agent", BRAND),
            ("0 / 2", "SAFE FALSE ALARMS", "no invented blockers", SUCCESS),
            ("1.00", "MEAN EFFORT", "counterexample found early", BRAND),
        )
        for index, (value, title, subtitle, accent) in enumerate(cards):
            p = ramp(now, 1.0 + index * 0.8, 0.7)
            stat_card(image, (100 + index * 600, 330, 650 + index * 600, 635), value, title, subtitle, p, accent)
        draw.rounded_rectangle((260, 780, 1660, 905), radius=22, fill="#eefaf5", outline="#b9e4d2", width=2)
        draw.text((960, 842), "Earlier semantic selection—not a claim of exhaustive safety.", font=face(31, 700), fill=SUCCESS, anchor="mm")
        return image
    p = (now - split) / max(0.1, total - split)
    image = dark_base()
    draw = ImageDraw.Draw(image, "RGBA")
    mark = Image.open(ROOT / "web" / "src" / "assets" / "cutoverproof-mark.png").convert("RGBA")
    mark.thumbnail((92, 92), Image.Resampling.LANCZOS)
    image.paste(mark, (758, 142), mark)
    draw.text((880, 188), "CutoverProof", font=face(60, display=True), fill=WHITE, anchor="lm")
    draw.text((960, 410), "A trust control plane", font=face(78, display=True), fill=WHITE, anchor="mm")
    draw.text((960, 505), "for agent-led production change.", font=face(70, display=True), fill="#8995ff", anchor="mm")
    draw.rounded_rectangle((420, 680, 1500, 696), radius=8, fill=BRAND)
    draw.text((960, 790), "Declared contract  •  Bounded experiments  •  Independent proof  •  Human authority", font=face(29, 700), fill="#d0d5ff", anchor="mm")
    return image


VISUALS = (title_frame, authorities_frame, tools_frame, handoff_frame, human_gate_frame, evidence_frame, approval_frame, close_frame)


def render_beat(index: int, beat: dict[str, str], visual, captions: list[str], global_cursor: float, caption_number: int) -> tuple[Path, float, int]:
    audio = VOICE / f"{beat['id']}.wav"
    audio_duration = duration(audio)
    clip_duration = audio_duration + 0.65
    frame_count = math.ceil(clip_duration * FPS)
    silent = BUILD / f"{index:02d}-{beat['id']}-silent.mp4"
    clip = BUILD / f"{index:02d}-{beat['id']}.mp4"
    process = subprocess.Popen(
        [
            str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(silent),
        ],
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    for frame_index in range(frame_count):
        now = frame_index / FPS
        frame = visual(now, clip_duration).convert("RGB")
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"FFmpeg frame encoder failed for {beat['id']}")
    run([
        str(FFMPEG), "-y", "-i", str(silent), "-i", str(audio),
        "-filter_complex", "[1:a]volume=-1dB,highpass=f=55,lowpass=f=8000,loudnorm=I=-17:TP=-2:LRA=9,adelay=250:all=1,apad=pad_dur=1[a]",
        "-map", "0:v", "-map", "[a]", "-t", f"{clip_duration:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(clip),
    ])

    chunks = caption_chunks(beat["text"])
    weights = [max(1, len(chunk.split())) for chunk in chunks]
    local = global_cursor + 0.25
    for chunk, weight in zip(chunks, weights, strict=True):
        span = audio_duration * weight / sum(weights)
        captions.append(f"{caption_number}\n{srt_time(local)} --> {srt_time(local + span)}\n{chunk}\n")
        caption_number += 1
        local += span
    return clip, clip_duration, caption_number


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    beats = json.loads(PLAN.read_text(encoding="utf-8"))
    if len(beats) != len(VISUALS):
        raise RuntimeError("The cinematic renderer expects eight narration beats")
    clips: list[Path] = []
    captions: list[str] = []
    cursor = 0.0
    caption_number = 1
    for index, (beat, visual) in enumerate(zip(beats, VISUALS, strict=True), start=1):
        print(f"Rendering {index}/8: {beat['id']}", flush=True)
        clip, clip_duration, caption_number = render_beat(index, beat, visual, captions, cursor, caption_number)
        clips.append(clip)
        cursor += clip_duration
    concat = BUILD / "clips.ffconcat"
    concat.write_text("ffconcat version 1.0\n" + "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clips) + "\n", encoding="utf-8")
    run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(OUTPUT)])
    OUTPUT.with_suffix(".srt").write_text("\n".join(captions), encoding="utf-8")
    print(f"COMPLETE {OUTPUT} ({duration(OUTPUT):.2f}s)")


def rebuild_selected(indices: set[int]) -> None:
    """Re-render selected beats, then remux them with the accepted beat clips."""
    BUILD.mkdir(parents=True, exist_ok=True)
    beats = json.loads(PLAN.read_text(encoding="utf-8"))
    for index in sorted(indices):
        if index < 1 or index > len(beats):
            raise ValueError(f"Beat index out of range: {index}")
        print(f"Re-rendering {index}/8: {beats[index - 1]['id']}", flush=True)
        render_beat(index, beats[index - 1], VISUALS[index - 1], [], 0.0, 1)
    clips = [BUILD / f"{index:02d}-{beat['id']}.mp4" for index, beat in enumerate(beats, start=1)]
    missing = [path for path in clips if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing accepted beat clips: {missing}")
    concat = BUILD / "clips.ffconcat"
    concat.write_text("ffconcat version 1.0\n" + "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clips) + "\n", encoding="utf-8")
    run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(OUTPUT)])
    print(f"COMPLETE {OUTPUT} ({duration(OUTPUT):.2f}s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated beat numbers to re-render before remuxing")
    arguments = parser.parse_args()
    if arguments.only:
        rebuild_selected({int(value) for value in arguments.only.split(",")})
    else:
        main()
