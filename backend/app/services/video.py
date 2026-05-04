import subprocess
from pathlib import Path

from app.config import model_settings


class VideoProcessingError(RuntimeError):
    pass


def extract_frames(video_path: Path, output_dir: Path, interval_seconds: float) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "frame_%06d.jpg"
    fps = 1 / interval_seconds

    try:
        subprocess.run(
            [
                model_settings.FFMPEG_BIN,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"fps={fps}",
                str(output_pattern),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise VideoProcessingError(
            f"ffmpeg executable not found: {model_settings.FFMPEG_BIN}"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise VideoProcessingError(exc.stderr.strip() or "ffmpeg failed to extract frames") from exc

    frames = sorted(output_dir.glob("frame_*.jpg"))
    if not frames:
        raise VideoProcessingError("No frames were extracted from the uploaded video")

    return frames
