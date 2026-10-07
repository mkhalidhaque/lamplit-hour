"""Still image + episode.mp3 -> out/episode.mp4 (1920x1080, 2 fps, tiny file).

Usage: python scripts/make_video.py queue/2026-10-08.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import OUT, load_episode, pick_image, run  # noqa: E402


def main(ep_path):
    ep = load_episode(ep_path)
    img = pick_image(ep)
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", "2", "-i", str(img), "-i", str(OUT / "episode.mp3"),
         "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p",
         "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-crf", "30", "-r", "2",
         "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT / "episode.mp4")])
    print(f"episode.mp4 from {img}")


if __name__ == "__main__":
    main(sys.argv[1])
