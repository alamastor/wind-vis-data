import logging
import sys

from windvisdata.latest_gfs_to_json import latest_gfs_to_json


logging.basicConfig(
    format='%(asctime)-15s %(message)s',
    stream=sys.stdout,
    level=logging.INFO)

latest_gfs_to_json()
