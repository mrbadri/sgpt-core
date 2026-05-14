"""One-time script: rename user memory files from user_{bale_tid}.md to user_{user_id}.md.

Run once after deploying the multi-platform identity migration.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Allow running from the backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.db.session import get_db_session
from app.services.bale_user_service import fetch_user_by_identity
from app.settings import settings


def main() -> None:
    mem_root = settings.user_memories_dir.strip()
    if not mem_root:
        print("USER_MEMORIES_DIR not set — nothing to do.")
        return

    mem_dir = Path(mem_root)
    if not mem_dir.exists():
        print(f"Memory directory does not exist: {mem_dir}")
        return

    pattern = re.compile(r"^user_(\d+)\.md$")
    files = [f for f in mem_dir.iterdir() if pattern.match(f.name)]

    if not files:
        print("No legacy memory files found.")
        return

    print(f"Found {len(files)} legacy memory file(s) to migrate.")
    db = get_db_session()
    renamed = 0
    skipped = 0

    try:
        for file in files:
            m = pattern.match(file.name)
            if not m:
                continue
            bale_tid = m.group(1)
            user = fetch_user_by_identity(db, "bale", bale_tid)
            if user is None:
                print(f"  SKIP {file.name} — no identity found for bale_tid={bale_tid}")
                skipped += 1
                continue
            new_path = mem_dir / f"user_{user.id}.md"
            if new_path.exists():
                print(f"  SKIP {file.name} — target {new_path.name} already exists")
                skipped += 1
                continue
            file.rename(new_path)
            print(f"  OK   {file.name} → {new_path.name}")
            renamed += 1
    finally:
        db.close()

    print(f"\nDone. Renamed: {renamed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
