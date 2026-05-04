"""Print how many episodes (``Episodic`` nodes) exist in the configured graph DB."""

from __future__ import annotations

import argparse
import asyncio
import logging

from ingestion.config.falkordb import (
    FALKOR_DATABASE,
    FALKOR_HOST,
    FALKOR_PORT,
    create_falkor_driver,
)

logger = logging.getLogger(__name__)


async def episode_names(driver, *, group_id: str | None) -> list[str]:
    if group_id is None:
        q = """
        MATCH (n:Episodic)
        RETURN coalesce(n.name, n.uuid, '') AS name
        ORDER BY name
        """
        records, _, _ = await driver.execute_query(q)
    else:
        q = """
        MATCH (n:Episodic)
        WHERE n.group_id = $group_id
        RETURN coalesce(n.name, n.uuid, '') AS name
        ORDER BY name
        """
        records, _, _ = await driver.execute_query(q, group_id=group_id)

    return [str(r["name"]) for r in records]


async def _run(driver, *, group_id: str | None) -> None:
    try:
        filter_desc = group_id if group_id is not None else "(بدون فیلتر — همه‌ی Episodic در همین گراف)"
        logger.info(
            "Falkor graph=%s host=%s port=%s group_id_filter=%s",
            FALKOR_DATABASE,
            FALKOR_HOST,
            FALKOR_PORT,
            filter_desc,
        )

        names = await episode_names(driver, group_id=group_id)
        for i, ep_name in enumerate(names, start=1):
            logger.info("episode[%s] name=%s", i, ep_name)

        n = len(names)
        logger.info("episode_count=%s", n)
        print(n)
    finally:
        await driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group-id",
        default=FALKOR_DATABASE,
        help=f"group_id روی نود اپیزود (پیش‌فرض: همان ingest، یعنی {FALKOR_DATABASE!r})",
    )
    parser.add_argument(
        "--all-groups",
        action="store_true",
        help="بدون فیلتر group_id؛ همه‌ی Episodic در همین گراف/دیتابیس فعلی",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )

    gid: str | None = None if args.all_groups else args.group_id

    # ساخت درایور بیرون از event loop تا FalkorDriver تسک ایندکس پس‌زمینه نسازد.
    driver = create_falkor_driver()
    asyncio.run(_run(driver, group_id=gid))


if __name__ == "__main__":
    main()
