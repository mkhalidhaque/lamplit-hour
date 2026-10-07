"""Append the episode to world/story_log.csv and move it from queue/ to published/."""
import csv
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_episode  # noqa: E402

FIELDS = ["date", "series", "place", "character", "season", "ambience", "story_title", "summary", "source_tradition", "source_note"]


def main(path):
    ep = load_episode(path)
    log = Path("world/story_log.csv")
    new = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        row = {k: ep.get(k, "") for k in FIELDS}
        row["date"] = date.today().isoformat()
        row["summary"] = ep.get("summary", "")
        w.writerow(row)
    Path("published").mkdir(exist_ok=True)
    shutil.move(path, Path("published") / Path(path).name)
    print("logged and moved to published/")


if __name__ == "__main__":
    main(sys.argv[1])
