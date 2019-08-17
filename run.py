import logging
from pathlib import Path

from windvisdata.latest_gfs_to_json import latest_gfs_to_json

log_file = Path(__file__).parent / "wind-vis-data.log"

logging.basicConfig(filename=log_file, level=logging.DEBUG)


def main():
    try:
        latest_gfs_to_json()
    except Exception:
        logging.exception("latest_gfs_to_json failed")


if __name__ == "__main__":
    main()
