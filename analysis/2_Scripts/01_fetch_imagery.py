r"""
Step 1 - Fetch imagery clips of the M-bend for each year and save as GeoTIFFs.

Source
  NYS orthoimagery (free, NYS ITS Geospatial Services): https://orthos.its.ny.gov/arcgis/rest/services/wms/<year>/MapServer

All outputs share one grid: NAD83 NY State Plane East (US ft, EPSG 2260),
extent E 635,900-636,850 / N 863,650-864,150, 0.5 ft pixels (1900 x 1000).

The original analysis also used one 2026 commercial aerial photo (licensed, not redistributed).
It only contributed to the reference centreline; the lidar results do not depend on it.
"""
import io
import json
import os
import urllib.parse
import urllib.request

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_origin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "1_Imagery")

XMIN, YMIN, XMAX, YMAX = 635900.0, 863650.0, 636850.0, 864150.0
PIX = 0.5
W, H = int((XMAX - XMIN) / PIX), int((YMAX - YMIN) / PIX)
TRANSFORM = from_origin(XMIN, YMAX, PIX, PIX)
BASE = "https://orthos.its.ny.gov/arcgis/rest/services/wms"

NYS = [  # (service, output name)
    ("napp", "NAPP_1994_CIR"),
    ("2004", "NYS_2004_RGB"),
    ("2007", "NYS_2007_RGB"), ("2007_cir", "NYS_2007_CIR"),
    ("2010", "NYS_2010_RGB"),                     # 2010 infrared has no coverage at this site
    ("2013", "NYS_2013_RGB"), ("2013_cir", "NYS_2013_CIR"),
    ("2016", "NYS_2016_RGB"), ("2016_cir", "NYS_2016_CIR"),
    ("2021", "NYS_2021_RGB"), ("2021_cir", "NYS_2021_CIR"),
    ("2024", "NYS_2024_RGB"), ("2024_cir", "NYS_2024_CIR"),
    ("2025", "NYS_2025_RGB"), ("2025_cir", "NYS_2025_CIR"),
]


def write_tif(name, rgb, nodata=None):
    path = os.path.join(OUT, name + ".tif")
    with rasterio.open(path, "w", driver="GTiff", width=W, height=H, count=3, dtype="uint8",
                       crs="EPSG:2260", transform=TRANSFORM, compress="deflate", predictor=2,
                       nodata=nodata) as dst:
        for b in range(3):
            dst.write(rgb[:, :, b], b + 1)
    return path


def fetch_nys(service):
    q = urllib.parse.urlencode({
        "bbox": f"{XMIN},{YMIN},{XMAX},{YMAX}", "bboxSR": 2260, "imageSR": 2260,
        "size": f"{W},{H}", "format": "png24", "transparent": "false", "dpi": 96, "f": "image"})
    with urllib.request.urlopen(f"{BASE}/{service}/MapServer/export?{q}", timeout=120) as r:
        data = r.read()
    img = np.array(Image.open(io.BytesIO(data)).convert("RGB"))
    assert img.shape[:2] == (H, W), img.shape
    return img, len(data)


def finest_lod_ft(service):
    with urllib.request.urlopen(f"{BASE}/{service}/MapServer?f=json", timeout=60) as r:
        info = json.load(r)
    lods = info.get("tileInfo", {}).get("lods", [])
    # Web Mercator resolution -> ground resolution at 41.2 N, in feet
    return round(lods[-1]["resolution"] * np.cos(np.radians(41.2)) / 0.3048006, 2) if lods else None


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for svc, name in NYS:
        img, nbytes = fetch_nys(svc)
        blank = (img.std() < 2)
        write_tif(name, img)
        print(f"{name:16s} {nbytes/1e6:5.1f} MB fetched  finest cache ~{finest_lod_ft(svc)} ft  "
              f"{'** BLANK - no coverage **' if blank else 'ok'}")
