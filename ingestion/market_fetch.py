import logging
import os

import requests

from core.config import (
    MARKET_AGGREGATE_CSV,
    MARKET_JOB_POSTINGS_SOURCE_BASE_URL,
    MARKET_SECTOR_CSV,
    RAW_DATA_DIR,
)
from core.logging import setup_logging

logger = logging.getLogger(__name__)

DOWNLOAD_TIMEOUT = 60  # seconds
SOURCE_FILES = (MARKET_AGGREGATE_CSV, MARKET_SECTOR_CSV)


def download_csv(filename: str) -> None:
    url = MARKET_JOB_POSTINGS_SOURCE_BASE_URL + filename
    dest = RAW_DATA_DIR + filename
    tmp = dest + ".tmp"

    logger.info("market_fetch.downloading", extra={"url": url})
    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    response.raise_for_status()

    with open(tmp, "wb") as fh:
        for chunk in response.iter_content(chunk_size=8192):
            fh.write(chunk)

    os.replace(tmp, dest)
    logger.info("market_fetch.saved", extra={"dest": dest, "bytes": os.path.getsize(dest)})


def main() -> None:
    setup_logging()
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    for filename in SOURCE_FILES:
        download_csv(filename)


if __name__ == "__main__":
    main()
