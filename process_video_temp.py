import cv2
import argparse
import subprocess
import tempfile
import os

def resize_video(input_path, output_path, width=640, height=480):
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)

    # Temporary video written by OpenCV
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        temp_path = tmp.name

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
        out.write(resized)

    cap.release()
    out.release()

    # Re-encode for browser compatibility
    cmd = [
        "ffmpeg",
        "-y",
        "-i", temp_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        output_path,
    ]

    subprocess.run(cmd, check=True)

    os.remove(temp_path)

    print(f"Saved browser-compatible video to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input video")
    parser.add_argument("output", help="Output video")
    args = parser.parse_args()

    resize_video(args.input, args.output)