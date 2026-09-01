"""Render the final CutoverProof competition demo from verified product captures."""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "submission" / "video"
BUILD = VIDEO / "build"
FRAMES = VIDEO / "frames"
VOICE = VIDEO / "voice"
ASSETS = VIDEO / "assets"
FFMPEG = Path("C:/Program Files/FFmpeg/8.1.2/bin/ffmpeg.exe")
FFPROBE = Path("C:/Program Files/FFmpeg/8.1.2/bin/ffprobe.exe")
W, H, FPS = 1920, 1080, 24

INK = "#0d1227"
BRAND = "#3847e9"
BRAND_SOFT = "#f0f2ff"
MUTED = "#69718a"
LINE = "#d9ddea"
SUCCESS = "#16845b"
DANGER = "#e23a35"
WHITE = "#ffffff"


def face(size: int, weight: int = 700, display: bool = False) -> ImageFont.FreeTypeFont:
    name = "Newsreader-700.ttf" if display else f"AlegreyaSans-{weight}.ttf"
    return ImageFont.truetype(str(ASSETS / name), size)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [str(FFPROBE), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True,
        check=True,
        text=True,
    )
    return float(result.stdout.strip())


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def logo(image: Image.Image, x: int, y: int, size: int = 72) -> None:
    mark = Image.open(ROOT / "web" / "src" / "assets" / "cutoverproof-mark.png").convert("RGBA")
    mark.thumbnail((size, size), Image.Resampling.LANCZOS)
    image.alpha_composite(mark, (x, y))


def base_slide() -> Image.Image:
    image = Image.new("RGBA", (W, H), "#fbfbfd")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1390, -500, 2350, 460), fill=(56, 71, 233, 24))
    draw.ellipse((-520, 650, 520, 1690), fill=(56, 71, 233, 18))
    return image


def title_slide() -> Image.Image:
    image = Image.new("RGBA", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1340, -450, 2300, 510), fill=(56, 71, 233, 135))
    draw.ellipse((-520, 640, 560, 1720), fill=(31, 44, 112, 255))
    logo(image, 110, 96, 88)
    draw.text((220, 140), "CutoverProof", font=face(56, display=True), fill=WHITE, anchor="lm")
    draw.text((110, 315), "POSTGRESQL MIGRATION TESTING", font=face(27, 800), fill="#aeb7ff")
    headline = "Find the ordering\nthat breaks the migration."
    draw.multiline_text((110, 370), headline, font=face(92, display=True), fill=WHITE, spacing=-2)
    draw.rounded_rectangle((110, 760, 1480, 890), radius=24, fill=(255, 255, 255, 18), outline=(255, 255, 255, 46), width=2)
    draw.text((155, 805), "Migration tools verify steps.", font=face(34, 700), fill="#d9ddff")
    draw.text((700, 805), "Failures live in schedules.", font=face(34, 800), fill="#7f8cff")
    return image


def screenshot_slide(path: Path, label: str) -> Image.Image:
    shot = Image.open(path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    image = shot.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((52, 38, 870, 104), radius=18, fill=(13, 18, 39, 226))
    draw.text((82, 72), label, font=face(25, 800), fill=WHITE, anchor="lm")
    return image


def progress_slide(label: str) -> Image.Image:
    """Keep the real workspace visible while enlarging its live job state."""
    source = Image.open(FRAMES / "22-live-progress.png").convert("RGB")
    image = source.convert("RGBA")
    dim = Image.new("RGBA", (W, H), (13, 18, 39, 74))
    image.alpha_composite(dim)
    progress = source.crop((1380, 102, 1898, 224)).resize((1036, 244), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((786, 235, 1862, 519), radius=24, fill=(255, 255, 255, 248), outline=BRAND, width=3)
    image.alpha_composite(progress.convert("RGBA"), (806, 255))
    draw.rounded_rectangle((52, 38, 870, 104), radius=18, fill=(13, 18, 39, 235))
    draw.text((82, 72), label, font=face(25, 800), fill=WHITE, anchor="lm")
    draw.text((115, 710), "Real job state", font=face(58, display=True), fill=WHITE)
    draw.text((115, 790), "Validation → planning → execution → verification → evidence", font=face(31, 700), fill="#e2e5ff")
    return image


def audit_replay_slide(label: str) -> Image.Image:
    """Focus the final audit on the approved identical-schedule replay."""
    source = Image.open(FRAMES / "29-repaired-detailed-timeline.png").convert("RGB")
    replay = source.crop((28, 820, 816, 1205))
    replay = replay.resize((1740, 850), Image.Resampling.LANCZOS)
    image = base_slide()
    image.alpha_composite(replay.convert("RGBA"), (90, 165))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((52, 38, 960, 104), radius=18, fill=(13, 18, 39, 235))
    draw.text((82, 72), label, font=face(25, 800), fill=WHITE, anchor="lm")
    draw.rounded_rectangle((1305, 860, 1765, 975), radius=18, fill="#eefaf5", outline="#b9e4d2", width=2)
    draw.text((1535, 900), "IDENTICAL SCHEDULE", font=face(20, 800), fill=SUCCESS, anchor="mm")
    draw.text((1535, 942), "0 violating rows", font=face(30, 800), fill=INK, anchor="mm")
    return image


def architecture_slide() -> Image.Image:
    image = base_slide()
    draw = ImageDraw.Draw(image, "RGBA")
    logo(image, 85, 58, 64)
    draw.text((170, 92), "CutoverProof architecture", font=face(50, display=True), fill=INK, anchor="lm")
    draw.text((85, 164), "ONE CONTROLLED LOOP · TWO INDEPENDENT DECISION BOUNDARIES", font=face(23, 800), fill=BRAND)

    def card(box: tuple[int, int, int, int], title: str, subtitle: str, accent: str = BRAND, fill: str = WHITE) -> None:
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=17, fill=fill, outline=accent, width=2)
        draw.rounded_rectangle((x1, y1, x1 + 9, y2), radius=5, fill=accent)
        draw.text((x1 + 24, y1 + 27), title, font=face(23, 800), fill=INK)
        for line_index, line in enumerate(wrap(draw, subtitle, face(18, 500), x2 - x1 - 45)):
            draw.text((x1 + 24, y1 + 66 + line_index * 21), line, font=face(18, 500), fill=MUTED)

    def arrow(start: tuple[int, int], end: tuple[int, int], color: str = BRAND, dashed: bool = False) -> None:
        x1, y1 = start
        x2, y2 = end
        if dashed:
            span = max(1, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5))
            for offset in range(0, span, 17):
                ratio1 = offset / span
                ratio2 = min(1, (offset + 9) / span)
                draw.line((x1 + (x2 - x1) * ratio1, y1 + (y2 - y1) * ratio1, x1 + (x2 - x1) * ratio2, y1 + (y2 - y1) * ratio2), fill=color, width=4)
        else:
            draw.line((x1, y1, x2, y2), fill=color, width=4)
        length = max(1.0, math.hypot(x2 - x1, y2 - y1))
        unit_x, unit_y = (x2 - x1) / length, (y2 - y1) / length
        base_x, base_y = x2 - unit_x * 14, y2 - unit_y * 14
        perp_x, perp_y = -unit_y * 8, unit_x * 8
        draw.polygon(((x2, y2), (base_x + perp_x, base_y + perp_y), (base_x - perp_x, base_y - perp_y)), fill=color)

    # Customer boundary.
    draw.rounded_rectangle((70, 260, 355, 780), radius=24, fill="#ffffff", outline="#cfd4e6", width=2)
    draw.text((95, 292), "ENGINEER", font=face(18, 800), fill=MUTED)
    card((95, 342, 330, 485), "React portal", "Import pack, watch progress, review evidence")
    card((95, 590, 330, 733), "Named reviewer", "Approve one bounded sandbox repair", SUCCESS, "#f6fcf9")

    # Deployed application trust boundary.
    draw.rounded_rectangle((410, 220, 1510, 845), radius=28, fill=(255, 255, 255, 190), outline=BRAND, width=3)
    draw.text((445, 252), "GOOGLE CLOUD RUN · REACT + FASTAPI WORKFLOW", font=face(19, 800), fill=BRAND)
    card((450, 305, 700, 445), "Pack validator", "Schema, seed, named operations, read-only invariant")
    card((785, 305, 1035, 445), "Tool gateway", "Vocabulary, phase rules, schedule length, budget")
    card((1120, 305, 1465, 445), "Evidence recorder", "Result JSON, agent trajectory, HTML timeline", SUCCESS, "#f6fcf9")
    card((450, 590, 700, 730), "Deterministic executor", "Reset, seed, execute the exact ordering")
    card((785, 590, 1035, 730), "PostgreSQL 17", "Disposable cutoverproof_sandbox", SUCCESS, "#f6fcf9")
    card((1120, 590, 1465, 730), "SQL invariant verifier", "Zero rows passes; returned rows block cutover", SUCCESS, "#f6fcf9")

    # External reasoning service is outside the deterministic verdict path.
    card((1570, 315, 1845, 475), "Vertex AI · Gemini", "Proposes a hypothesis, schedule, and allow-listed repair", BRAND, "#f7f8ff")
    draw.text((1585, 548), "NO RAW SQL TOOL", font=face(17, 800), fill=DANGER)
    draw.text((1585, 573), "NO VERDICT AUTHORITY", font=face(17, 800), fill=DANGER)

    arrow((330, 410), (450, 410))
    arrow((700, 375), (785, 375))
    draw.line((910, 445, 910, 510), fill=BRAND, width=4)
    draw.line((1705, 475, 1705, 510), fill=BRAND, width=4)
    arrow((925, 510), (1690, 510), dashed=True)
    arrow((1690, 530), (925, 530), dashed=True)
    arrow((910, 445), (575, 590))
    arrow((700, 660), (785, 660))
    arrow((1035, 660), (1120, 660), SUCCESS)
    arrow((1290, 590), (1290, 445), SUCCESS)
    arrow((1120, 385), (1035, 385), SUCCESS)
    draw.line((1290, 305, 1290, 280, 375, 280, 375, 410), fill=SUCCESS, width=4)
    arrow((375, 410), (330, 410), SUCCESS)
    arrow((330, 660), (450, 660), SUCCESS)

    draw.rounded_rectangle((435, 875, 1485, 1000), radius=22, fill=INK)
    draw.text((960, 918), "Gemini selects experiments. PostgreSQL and SQL invariants decide what happened.", font=face(28, 800), fill=WHITE, anchor="mm")
    draw.text((960, 963), "A repair runs only after named human approval, then replays the identical failing schedule.", font=face(22, 500), fill="#cbd2ff", anchor="mm")
    return image


def benchmark_slide() -> Image.Image:
    image = base_slide()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((95, 90), "Measured improvement", font=face(62, display=True), fill=INK)
    draw.text((95, 166), "Equal model, facts, seed, and four-candidate execution budget", font=face(26, 500), fill=MUTED)
    headers = ["Approach", "Unsafe recall", "Safe false alarms", "Mean effort"]
    rows = [
        ("Specialised iterative agent", "3 / 3", "0 / 2", "1.00"),
        ("One-shot Gemini baseline", "2 / 3", "0 / 2", "2.33"),
        ("Seeded heuristic explorer", "3 / 3", "0 / 2", "3.00"),
    ]
    xs = [120, 850, 1160, 1530]
    draw.rounded_rectangle((90, 260, 1830, 760), radius=24, fill=WHITE, outline=LINE, width=2)
    draw.rounded_rectangle((90, 260, 1830, 360), radius=24, fill=INK)
    for x, header in zip(xs, headers, strict=True):
        draw.text((x, 312), header, font=face(24, 700), fill=WHITE, anchor="lm")
    for row_index, row in enumerate(rows):
        y = 430 + row_index * 130
        if row_index == 0:
            draw.rounded_rectangle((105, y - 48, 1815, y + 60), radius=14, fill=BRAND_SOFT)
        for column, value in enumerate(row):
            color = BRAND if row_index == 0 and column > 0 else INK
            weight = 800 if row_index == 0 else 700
            draw.text((xs[column], y), value, font=face(29 if column == 0 else 31, weight), fill=color, anchor="lm")
    draw.rounded_rectangle((260, 845, 1660, 947), radius=20, fill="#eefaf5", outline="#b9e4d2", width=2)
    draw.text((960, 897), "Advantage: earlier semantic selection—not a claim of exhaustive safety.", font=face(29, 700), fill=SUCCESS, anchor="mm")
    return image


def changelog_slide() -> Image.Image:
    image = base_slide()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((95, 90), "How evaluation strengthened the system", font=face(62, display=True), fill=INK)
    draw.text((95, 170), "Every verdict must remain tied to executed database evidence.", font=face(31, 700), fill=BRAND)
    items = [
        ("FAIL CLOSED", "Provider and parser errors", "Authentication, quota, parse, and verifier faults cannot become migration verdicts."),
        ("SEPARATED", "Schedule and repair reasoning", "A repair is considered only after a database-verified failure."),
        ("PRESERVED", "Invalid and failed experiments", "Metrics remain auditable instead of silently converting failures into misses."),
        ("VERIFIED", "Customer import and replay path", "Uploaded packs produce the same PostgreSQL evidence and bounded approval record."),
    ]
    y = 285
    for tag, title, detail in items:
        color = SUCCESS if tag == "VERIFIED" else BRAND
        draw.rounded_rectangle((95, y, 1825, y + 150), radius=20, fill=WHITE, outline=LINE, width=2)
        draw.rounded_rectangle((125, y + 38, 300, y + 96), radius=14, fill=color)
        draw.text((212, y + 68), tag, font=face(22, 800), fill=WHITE, anchor="mm")
        draw.text((345, y + 48), title, font=face(31, 800), fill=INK)
        draw.text((345, y + 93), detail, font=face(23, 500), fill=MUTED)
        y += 170
    return image


def end_slide() -> Image.Image:
    image = Image.new("RGBA", (W, H), INK)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((1350, -460, 2310, 500), fill=(56, 71, 233, 145))
    draw.ellipse((-520, 630, 560, 1710), fill=(31, 44, 112, 255))
    logo(image, 725, 160, 94)
    draw.text((850, 207), "CutoverProof", font=face(60, display=True), fill=WHITE, anchor="lm")
    draw.text((960, 470), "Find the ordering that proves", font=face(68, 700), fill=WHITE, anchor="mm")
    draw.text((960, 555), "when a migration is not safe.", font=face(68, 800), fill="#8390ff", anchor="mm")
    draw.rounded_rectangle((475, 720, 1445, 736), radius=8, fill=BRAND)
    draw.text((960, 825), "Gemini  •  PostgreSQL  •  Cloud Run", font=face(32, 500), fill="#cbd2ff", anchor="mm")
    return image


def make_frame(beat: dict, destination: Path) -> None:
    visual = beat["visual"]
    if visual == "title":
        image = title_slide()
    elif visual == "architecture":
        image = architecture_slide()
    elif visual == "benchmark":
        image = benchmark_slide()
    elif visual == "changelog":
        image = changelog_slide()
    elif visual == "audit_replay":
        image = audit_replay_slide(beat["label"])
    elif visual == "progress":
        image = progress_slide(beat["label"])
    elif visual == "end":
        image = end_slide()
    else:
        image = screenshot_slide(VIDEO / visual, beat["label"])
    image.convert("RGB").save(destination, "PNG", optimize=True)


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def caption_chunks(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= 11:
            chunks.append(sentence)
        else:
            middle = len(words) // 2
            chunks.extend((" ".join(words[:middle]), " ".join(words[middle:])))
    return [chunk for chunk in chunks if chunk]


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    plan = json.loads((VIDEO / "narration.json").read_text(encoding="utf-8"))
    clips: list[Path] = []
    srt_entries: list[str] = []
    cursor = 0.0
    caption_number = 1

    for index, beat in enumerate(plan, start=1):
        frame = BUILD / f"{index:02d}-{beat['id']}.png"
        audio = VOICE / f"{beat['id']}.wav"
        clip = BUILD / f"{index:02d}-{beat['id']}.mp4"
        make_frame(beat, frame)
        audio_duration = duration(audio)
        clip_duration = audio_duration + 1.05
        run([
            str(FFMPEG), "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(frame), "-i", str(audio),
            "-filter_complex",
            f"[0:v]zoompan=z='min(zoom+0.00007,1.022)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p[v];"
            "[1:a]volume=-3dB,highpass=f=55,lowpass=f=8000,loudnorm=I=-17:TP=-2:LRA=9,adelay=420:all=1,apad=pad_dur=1[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{clip_duration:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(clip),
        ])
        clips.append(clip)

        chunks = caption_chunks(beat["text"])
        weights = [max(1, len(chunk.split())) for chunk in chunks]
        local = cursor + 0.42
        for chunk, weight in zip(chunks, weights, strict=True):
            span = audio_duration * weight / sum(weights)
            srt_entries.append(f"{caption_number}\n{srt_time(local)} --> {srt_time(local + span)}\n{chunk}\n")
            caption_number += 1
            local += span
        cursor += clip_duration

    concat = BUILD / "clips.ffconcat"
    concat.write_text("ffconcat version 1.0\n" + "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clips) + "\n", encoding="utf-8")
    output = VIDEO / "CutoverProof_Competition_Demo_FINAL.mp4"
    run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(output)])
    output.with_suffix(".srt").write_text("\n".join(srt_entries), encoding="utf-8")
    print(f"COMPLETE {output} ({duration(output):.2f}s)")


if __name__ == "__main__":
    main()
