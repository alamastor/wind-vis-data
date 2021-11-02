from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging
import json
from contextlib import contextmanager

import numpy as np

import pygrib

LOG = logging.getLogger(__name__)

GRIB_DIR = Path(__file__).parent.parent / "grib_files"
GRIB_DIR.mkdir(exist_ok=True)
GFS_HOURS = 180
GFS_INTERVAL = 3
SPATIAL_RESOLUTION = 1
GRIB_DATA_RESOLUTION = 1


@dataclass
class GribDataset:
    run_datetime: datetime
    taus: list[int] = field(
        default_factory=lambda: list(range(0, GFS_HOURS + GFS_INTERVAL, GFS_INTERVAL))
    )
    resolution: float = SPATIAL_RESOLUTION

    def file_path(self, tau: int) -> Path:
        return GRIB_DIR / f"gfs_100_{self.run_datetime:%Y%m%d_%H%M}_{tau:03d}.grb2"

    @property
    def max_wind_speed(self) -> float:
        max_wind_speed = 0
        for tau in self.taus:
            with self.data(tau) as grib_data:
                u_data = grib_data.select(name="U component of wind")[0]["values"]
                v_data = grib_data.select(name="V component of wind")[0]["values"]
            max_wind_speed = max(
                np.max(np.sqrt(u_data ** 2 + v_data ** 2)), max_wind_speed
            )
        return max_wind_speed

    @contextmanager
    def data(self, tau: int):
        grib_data = pygrib.open(str(self.file_path(tau)))  # type: ignore
        try:
            yield grib_data
        finally:
            grib_data.close()

    def tau_to_json(
        self,
        tau,
        param,
        unit,
        json_file_path,
        *,
        target_resolution: float = GRIB_DATA_RESOLUTION,
    ) -> None:
        if target_resolution % GRIB_DATA_RESOLUTION != 0:
            raise ValueError(
                f"target_resolution {target_resolution} is not a multiple of grib "
                "resolution."
            )
        with self.data(tau) as tau_data:
            data = tau_data.select(name=param)[0]["values"]

            data_dict = {"param": param, "unit": unit, "data": []}
            for x in range(360):
                if x % target_resolution == 0:
                    data_dict["data"].append([])

                for y in range(180, -1, -1):
                    if y % target_resolution == 0:
                        data_dict["data"][-1].append(round(float(data[y][x])))

            with open(json_file_path, "w") as w:
                json.dump(data_dict, w)
            LOG.info("created %s", json_file_path)


def purge_all_grib_files():
    LOG.info("Purging all downloaded grib files.")
    for grib_file in GRIB_DIR.glob("*"):
        grib_file.unlink()
