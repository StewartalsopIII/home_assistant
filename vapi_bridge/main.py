from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import signal

from .config import Config


def _setup_logging() -> None:
    level_name = os.getenv("VAPI_BRIDGE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def _run() -> None:
    config = Config.from_env()
    # Import here so `python -m vapi_bridge.main -h` works without deps installed.
    from .bridge import Bridge  # noqa: WPS433

    bridge = Bridge(config)
    await bridge.start()

    stop_event = asyncio.Event()

    def _stop(*_args: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _stop)

    await stop_event.wait()
    await bridge.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="ESPHome ↔ Vapi UDP audio bridge")
    _ = parser.parse_args()
    _setup_logging()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
