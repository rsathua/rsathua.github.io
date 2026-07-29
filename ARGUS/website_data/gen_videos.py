#!/usr/bin/env python3
"""
Iterates through all subdirectories of a given root folder. For each
subdirectory, looks for cam_0_rgb, cam_1_rgb, and vggt_rgb folders
containing frames named 0.jpg, 1.jpg, 2.jpg, ... and compiles each
into an .mp4 video (via ffmpeg) saved back into that same subdirectory.
"""

import argparse
import re
import subprocess
import shutil
from pathlib import Path

CAM_FOLDERS = ["cam_0_rgb", "cam_1_rgb", "vggt_rgb"]
FRAME_PATTERN = re.compile(r"^(\d+)\.jpg$")


def get_sorted_frames(folder: Path):
    """Return list of frame paths sorted numerically by filename."""
    frames = []
    for f in folder.iterdir():
        m = FRAME_PATTERN.match(f.name)
        if m:
            frames.append((int(m.group(1)), f))
    frames.sort(key=lambda x: x[0])
    return [f for _, f in frames]


def make_video(frames, output_path: Path, fps: int):
    if not frames:
        print(f"  [skip] no frames found for {output_path.stem}")
        return

    # Write an ffmpeg concat list so frame numbers don't need to be
    # contiguous or zero-padded.
    list_file = output_path.with_suffix(".txt")
    frame_duration = 1.0 / fps
    with open(list_file, "w") as f:
        for frame_path in frames:
            f.write(f"file '{frame_path.resolve().as_posix()}'\n")
            f.write(f"duration {frame_duration}\n")
        # concat demuxer quirk: last frame's duration is ignored unless
        # the file is listed again at the end.
        f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-vsync", "vfr",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    list_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  [error] ffmpeg failed for {output_path}:\n{result.stderr}")
        return

    print(f"  [done] wrote {output_path} ({len(frames)} frames)")


def process_root(root: Path, fps: int):
    for subdir in sorted(p for p in root.iterdir() if p.is_dir()):
        print(f"Processing {subdir}")
        for cam_folder_name in CAM_FOLDERS:
            cam_folder = subdir / cam_folder_name
            if not cam_folder.is_dir():
                print(f"  [skip] {cam_folder_name} not found in {subdir}")
                continue

            frames = get_sorted_frames(cam_folder)
            output_path = subdir / f"{cam_folder_name}.mp4"
            make_video(frames, output_path, fps)

def main():
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not found on PATH. Install it first (e.g. apt install ffmpeg).")

    parser = argparse.ArgumentParser(
        description="Generate mp4 videos from cam_0_rgb, cam_1_rgb, and vggt_rgb frame folders."
    )
    parser.add_argument("root", type=str, help="Root folder containing subdirectories to process")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    process_root(root, args.fps)


if __name__ == "__main__":
    main()