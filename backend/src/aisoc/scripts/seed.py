"""CLI seed entrypoint used by scripts/seed.sh."""

from __future__ import annotations

import asyncio


async def _async_main() -> None:
    from aisoc.core.config import get_settings
    from aisoc.db.seed import run_seed
    from aisoc.db.session import get_session_factory

    settings = get_settings()
    factory = get_session_factory()
    async with factory() as session:
        await run_seed(session, settings)
    print("Seed complete.")
    print(f"  Admin:   {settings.seed_admin_email}")
    print(f"  Analyst: {settings.seed_analyst_email}")


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
