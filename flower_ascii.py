#!/usr/bin/env python3
"""Offline 2D ASCII flower animation, recreated from the supplied video.

Requires only the Python standard library. Keep flower_frames.bin beside this file.
Run: python flower_ascii.py
Keys: Space = pause/resume, R = restart, Q or Esc = quit.
"""

from __future__ import annotations

import math
import os
import shutil
import struct
import sys
import time
import zlib
from pathlib import Path
from typing import Optional

ATLAS_FILE = Path(__file__).with_name("flower_frames.bin")
HEADER_FORMAT = "<8sHHHHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
EXPECTED_MAGIC = b"FLWASCII"
TEXT_PATTERN = "let it bloom"
FPS_FALLBACK = 30


def load_atlas() -> tuple[int, int, int, int, bytes]:
    """Load the compressed, local frame atlas from its binary data file."""
    if not ATLAS_FILE.is_file():
        raise FileNotFoundError(
            f"Missing {ATLAS_FILE.name}. Keep it in the same folder as this script."
        )

    packed = ATLAS_FILE.read_bytes()
    if len(packed) < HEADER_SIZE:
        raise ValueError("The frame atlas is incomplete.")

    magic, version, width, height, fps, frame_count = struct.unpack(
        HEADER_FORMAT, packed[:HEADER_SIZE]
    )
    if magic != EXPECTED_MAGIC or version != 1:
        raise ValueError("Unsupported or damaged frame atlas.")
    if width < 1 or height < 1 or fps < 1 or frame_count < 1:
        raise ValueError("The frame atlas contains invalid dimensions.")

    pixels = zlib.decompress(packed[HEADER_SIZE:])
    expected_size = width * height * 3 * frame_count
    if len(pixels) != expected_size:
        raise ValueError("The frame atlas data length does not match its header.")

    return width, height, fps, frame_count, pixels


def clamp_byte(value: float) -> int:
    return max(0, min(255, int(value)))


def sample_cell(
    frame: memoryview,
    source_width: int,
    source_height: int,
    x: int,
    y: int,
    target_width: int,
    target_height: int,
) -> tuple[int, int, int]:
    """Area-average the atlas when the terminal is smaller than the source grid."""
    x0 = (x * source_width) // target_width
    x1 = max(x0 + 1, ((x + 1) * source_width + target_width - 1) // target_width)
    y0 = (y * source_height) // target_height
    y1 = max(y0 + 1, ((y + 1) * source_height + target_height - 1) // target_height)
    x1 = min(source_width, x1)
    y1 = min(source_height, y1)

    red = green = blue = count = 0
    for source_y in range(y0, y1):
        offset = (source_y * source_width + x0) * 3
        for _source_x in range(x0, x1):
            red += frame[offset]
            green += frame[offset + 1]
            blue += frame[offset + 2]
            offset += 3
            count += 1
    if count == 0:
        return 0, 0, 0
    return red // count, green // count, blue // count


def choose_glyph(red: int, green: int, blue: int, x: int, y: int) -> str:
    """Use small text-like glyphs so the surface reads as rows of ASCII."""
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luminance < 8:
        return " "
    if luminance < 20:
        return "."
    if luminance < 38:
        return ":;,'"[(x + y * 3) % 4]
    if luminance < 58:
        return "itlf"[(x + y * 5) % 4]
    glyph = TEXT_PATTERN[(x + y * 5) % len(TEXT_PATTERN)]
    return "i" if glyph == " " else glyph


def make_color(red: int, green: int, blue: int) -> tuple[int, int, int]:
    """Lift the photographed screen slightly without flattening its pink shadows."""
    return (
        clamp_byte(red * 1.34),
        clamp_byte(green * 1.30),
        clamp_byte(blue * 1.34),
    )


def render_frame(
    source_frame: memoryview,
    source_width: int,
    source_height: int,
    terminal_width: int,
    terminal_height: int,
) -> str:
    # The source texture aspect is chosen to match a monospace terminal cell.
    available_width = max(1, terminal_width - 2)
    available_height = max(1, terminal_height - 2)
    aspect = source_width / source_height
    target_width = min(available_width, max(1, int(available_height * aspect)))
    target_height = max(1, min(available_height, int(target_width / aspect)))
    target_width = max(1, min(available_width, int(target_height * aspect)))

    left_pad = max(0, (terminal_width - target_width) // 2)
    top_pad = max(0, (terminal_height - target_height) // 2)
    lines: list[str] = []
    empty = " " * left_pad

    for y in range(terminal_height):
        if y < top_pad or y >= top_pad + target_height:
            lines.append(" " * terminal_width)
            continue

        pieces: list[str] = [empty]
        last_color: Optional[tuple[int, int, int]] = None
        target_y = y - top_pad
        for x in range(target_width):
            red, green, blue = sample_cell(
                source_frame, source_width, source_height,
                x, target_y, target_width, target_height
            )
            glyph = choose_glyph(red, green, blue, x, target_y)
            if glyph == " ":
                pieces.append(" ")
                continue
            color = make_color(red, green, blue)
            if color != last_color:
                pieces.append(f"\x1b[38;2;{color[0]};{color[1]};{color[2]}m")
                last_color = color
            pieces.append(glyph)
        pieces.append("\x1b[0m")
        pieces.append(" " * max(0, terminal_width - left_pad - target_width))
        lines.append("".join(pieces))

    return "\n".join(lines)


def enable_windows_ansi() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004 | 0x0008)
    except Exception:
        # Windows Terminal already supports ANSI in normal configurations.
        pass


def read_key() -> Optional[str]:
    if os.name == "nt":
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getwch()
                if key in ("\x00", "\xe0"):
                    if msvcrt.kbhit():
                        msvcrt.getwch()
                    return None
                return key
        except Exception:
            return None
    else:
        try:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            if ready:
                return sys.stdin.read(1)
        except (OSError, ValueError):
            return None
    return None


def main() -> int:
    try:
        width, height, fps, frame_count, atlas = load_atlas()
    except (OSError, ValueError, zlib.error) as error:
        print(f"Could not load the ASCII flower: {error}", file=sys.stderr)
        return 1

    global TEXT_PATTERN
    enable_windows_ansi()
    try:
        print("ASCII Flower customizer")
        phrase = input("Your text (used as ASCII characters, Enter = default): ").strip()
        if phrase:
            TEXT_PATTERN = "".join(phrase.split())[:64] or TEXT_PATTERN
    except (EOFError, KeyboardInterrupt):
        pass
    frame_size = width * height * 3
    frame_duration = 1.0 / fps
    terminal_size = shutil.get_terminal_size((110, 42))
    terminal_width = max(50, min(160, terminal_size.columns - 1))
    terminal_height = max(24, min(60, terminal_size.lines - 1))

    started = time.perf_counter()
    paused_at: Optional[float] = None
    paused_total = 0.0
    previous_frame = -1

    sys.stdout.write("\x1b[2J\x1b[H\x1b[?25l")
    sys.stdout.flush()
    try:
        while True:
            frame_started = time.perf_counter()
            key = read_key()
            if key:
                normalized = key.lower()
                if normalized in ("q", "\x1b"):
                    break
                if normalized == " ":
                    if paused_at is None:
                        paused_at = time.perf_counter()
                    else:
                        paused_total += time.perf_counter() - paused_at
                        paused_at = None
                elif normalized == "r":
                    started = time.perf_counter()
                    paused_total = 0.0
                    paused_at = None
                    previous_frame = -1

            now = paused_at if paused_at is not None else time.perf_counter()
            elapsed = max(0.0, now - started - paused_total)
            frame_index = int(elapsed * fps) % frame_count
            if frame_index != previous_frame:
                start = frame_index * frame_size
                current_frame = memoryview(atlas)[start:start + frame_size]
                output = render_frame(
                    current_frame, width, height, terminal_width, terminal_height
                )
                sys.stdout.write("\x1b[H" + output)
                sys.stdout.flush()
                previous_frame = frame_index

            delay = frame_duration - (time.perf_counter() - frame_started)
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
