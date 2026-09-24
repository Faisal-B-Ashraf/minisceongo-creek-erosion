r"""
Step 4 - South-bank change from the two lidar surveys (USGS Nov 19 2011 vs NYS Apr 15 2022).

Raw tiles (NYS GIS clearinghouse, not kept in the project - large):
  https://gisdata.ny.gov/elevation/LIDAR/USGS_NorthEast2011/18_05854562.las          (flown 2011-11-19)
  https://gisdata.ny.gov/elevation/LIDAR/NYS_Southeast4County2022/u_5850056150_2022.las  (flown 2022-04-15)
usage: python 04_lidar_south_bank.py [folder_with_raw_las]
  The raw tiles are only needed once: the creek area is clipped to 1_LiDAR\*_points_clip.csv
  (NY State Plane East ftUS, NAVD88 ftUS) and later runs work from those.

Method
  1. Ground points: 2011 classes 2 + 18 (18 = overlap ground, checked against class 2), 2022 class 2.
  2. Alignment: the 2011 survey is offset ~6.7 ft from 2022. The offset is measured by matching house
     roofs (surface models incl. buildings) and checked with the slope/aspect (Nuth & Kaab) test on
     ground away from the creek. 2022 is tied to the imagery frame (the transects) by matching lidar
     intensity to the NYS 2025 infrared band. Vertical bias is removed on flat stable ground.
  3. 1-ft ground surfaces (TIN) for each year, and their difference (2022 - 2011).
  4. South bank, per 10-ft transect: the bank face is the tallest steep rise on the south side of the 2022
     cross-section (lowest 12 ft of it where it runs up into the valley wall); its position is measured in
     both years at 25/50/75 % of the face height.
     Movement > 0 = bank moved away from the channel (toward the houses) = erosion.
  5. Uncertainty: the 2022 points are thinned to 2011 density (10 random draws) and re-measured, giving the
     error caused by the sparse 2011 sampling; combined with residual alignment and vertical noise into a
     95 % detection limit per transect. Movements beyond it are flagged real.

Outputs
  1_LiDAR\LiDAR_2011_Nov_points_clip.csv, LiDAR_2022_Apr_points_clip.csv, Ground_DEM_2011_Nov_1ft.tif,
         Ground_DEM_2022_Apr_1ft.tif
  3_GIS\LiDAR_Change_2011_2022.tif, South_Bank_2011_LiDAR.shp, South_Bank_2022_LiDAR.shp
  4_Results\LiDAR_Alignment_and_Accuracy.csv, LiDAR_South_Bank_Change.csv, LiDAR_South_Bank_Zone_Summary.csv,
            LiDAR_Change_Map.png, LiDAR_South_Bank_Movement.png, LiDAR_South_Bank_Profiles.png
"""
import csv
import os
import struct
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import shapefile
from pyproj import CRS, Transformer
from rasterio.transform import from_origin
from scipy import ndimage
from scipy.interpolate import LinearNDInterpolator
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LID, GIS, RES, IMG = (os.path.join(ROOT, d) for d in ("1_LiDAR", "3_GIS", "4_Results", "1_Imagery"))
XMIN, XMAX, YMIN, YMAX = 635900.0, 636850.0, 863650.0, 864150.0
FT = 0.3048006096012192                                  # metres per US survey foot
SURVEYS = {2011: dict(tile="18_05854562.las", ground=[2, 18], maxgap=10.0, date="2011-11-19", tag="2011_Nov"),
           2022: dict(tile="u_5850056150_2022.las", ground=[2], maxgap=6.0, date="2022-04-15", tag="2022_Apr")}
YEARS_APART = (np.datetime64("2022-04-15") - np.datetime64("2011-11-19")).astype(int) / 365.25
ZONES = [("West limb", 0, 35), ("First hump (inside bend)", 36, 57), ("Dip (outside bend)", 58, 75),
         ("Pool / second hump", 76, 99), ("East limb", 100, 127)]
PROFILE_STATIONS = [20, 30, 40, 50, 58, 62, 66, 70, 72, 74, 76, 80, 86, 94, 102, 106]
FACE_CAP_FT = 12.0                                       # bank face = at most the lowest 12 ft above its toe
SETBACK_FT = 15.0                                        # set back = face toe >15 ft behind the water's edge AND
                                                         # the ground in front is >1.5 ft above the channel bottom


# ------------------------------------------------------------------ LAS reading (uncompressed, numpy only)
def read_las(path):
    with open(path, "rb") as f:
        h = f.read(375)
    ver = (h[24], h[25])
    off_pts, = struct.unpack_from("<I", h, 96)
    fmt = h[104] & 0x3F
    rec_len, = struct.unpack_from("<H", h, 105)
    n, = struct.unpack_from("<I", h, 107)
    if ver >= (1, 4):
        n = struct.unpack_from("<Q", h, 247)[0] or n
    scale, offset = struct.unpack_from("<3d", h, 131), struct.unpack_from("<3d", h, 155)
    if fmt <= 5:
        fields = [("X", "<i4"), ("Y", "<i4"), ("Z", "<i4"), ("I", "<u2"), ("ret", "u1"), ("cls", "u1"),
                  ("ang", "i1"), ("usr", "u1"), ("psid", "<u2")] + ([("gps", "<f8")] if fmt in (1, 3, 4, 5) else [])
    else:
        fields = [("X", "<i4"), ("Y", "<i4"), ("Z", "<i4"), ("I", "<u2"), ("ret", "u1"), ("flg", "u1"), ("cls", "u1"),
                  ("usr", "u1"), ("ang", "<i2"), ("psid", "<u2"), ("gps", "<f8")]
    size = np.dtype(fields).itemsize
    if rec_len > size:
        fields.append(("pad", f"V{rec_len - size}"))
    P = np.memmap(path, dtype=np.dtype(fields), mode="r", offset=off_pts, shape=(n,))
    cls = P["cls"] & (0x1F if fmt <= 5 else 0xFF)
    return P, scale, offset, cls


def clip_to_csv(raw_dir, year):
    """Clip a raw tile to the analysis area, convert to NY State Plane East ftUS / NAVD88 ftUS, write CSV."""
    s = SURVEYS[year]
    P, sc, of, cls = read_las(os.path.join(raw_dir, s["tile"]))
    # Both tiles are UTM 18N on NAD83 (2011 tile: NAD83; 2022 tile: NAD83(2011)); the same projection maths is
    # used for both, and any datum-realisation difference is absorbed by the measured alignment below.
    fwd = Transformer.from_crs("EPSG:26918", "EPSG:2260", always_xy=True)
    inv = Transformer.from_crs("EPSG:2260", "EPSG:26918", always_xy=True)
    cx, cy = inv.transform([XMIN - 60, XMAX + 60, XMIN - 60, XMAX + 60], [YMIN - 60, YMIN - 60, YMAX + 60, YMAX + 60])
    ex, ey = P["X"] * sc[0] + of[0], P["Y"] * sc[1] + of[1]
    sel = (ex >= min(cx)) & (ex <= max(cx)) & (ey >= min(cy)) & (ey <= max(cy))
    x, y = fwd.transform(ex[sel], ey[sel])
    x, y = np.asarray(x), np.asarray(y)
    z = (P["Z"][sel] * sc[2] + of[2]) / FT
    k = (x >= XMIN - 20) & (x <= XMAX + 20) & (y >= YMIN - 20) & (y <= YMAX + 20)
    out = os.path.join(LID, f"LiDAR_{s['tag']}_points_clip.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["E_ft", "N_ft", "Z_ft_NAVD88", "Class", "Intensity"])
        for row in zip(np.round(x[k], 3), np.round(y[k], 3), np.round(z[k], 3), cls[sel][k], P["I"][sel][k]):
            w.writerow(row)
    return out


def load_points(year):
    a = np.loadtxt(os.path.join(LID, f"LiDAR_{SURVEYS[year]['tag']}_points_clip.csv"), delimiter=",", skiprows=1)
    return dict(x=a[:, 0], y=a[:, 1], z=a[:, 2], c=a[:, 3].astype(int), i=a[:, 4])


# ------------------------------------------------------------------ gridding helpers
GX, GY = np.meshgrid(np.arange(XMIN + 0.5, XMAX, 1.0), np.arange(YMAX - 0.5, YMIN, -1.0))


def tin(x, y, v, maxgap=None):
    Z = LinearNDInterpolator(np.column_stack([x, y]), v)(GX, GY)
    if maxgap:
        d, _ = cKDTree(np.column_stack([x, y])).query(np.column_stack([GX.ravel(), GY.ravel()]))
        Z[d.reshape(Z.shape) > maxgap] = np.nan
    return Z


def slope_aspect(Z):
    dzdy, dzdx = np.gradient(Z)
    dzdn = -dzdy
    return np.degrees(np.arctan(np.hypot(dzdx, dzdn))), np.degrees(np.arctan2(-dzdx, -dzdn)) % 360


def hillshade(Z, az=315, alt=45):
    dy, dx = np.gradient(np.nan_to_num(Z, nan=np.nanmean(Z)))
    slope = np.pi / 2 - np.arctan(np.hypot(dx, dy)); aspect = np.arctan2(-dx, dy)
    a, b = np.radians(az), np.radians(alt)
    return np.clip(np.sin(b) * np.sin(slope) + np.cos(b) * np.cos(slope) * np.cos(a - aspect), 0, 1)


def ncc_map(search, tpl):
    tpl = tpl - tpl.mean()
    num = fftconvolve(search, tpl[::-1, ::-1], mode="valid")
    ones = np.ones_like(tpl)
    s1, s2 = fftconvolve(search, ones, mode="valid"), fftconvolve(search ** 2, ones, mode="valid")
    return num / (np.sqrt(np.maximum(s2 - s1 ** 2 / tpl.size, 1e-9)) * np.sqrt((tpl ** 2).sum()) + 1e-12)


def peak(m):
    i, j = np.unravel_index(np.argmax(m), m.shape)
    if i in (0, m.shape[0] - 1) or j in (0, m.shape[1] - 1):
        return None
    f = lambda a, b, c: 0.0 if a - 2 * b + c == 0 else 0.5 * (a - c) / (a - 2 * b + c)
    return i + f(m[i - 1, j], m[i, j], m[i + 1, j]), j + f(m[i, j - 1], m[i, j], m[i, j + 1]), m[i, j]


def match(A, B, patches, S, min_ncc):
    """Median (dE, dN) of features in B relative to A, from patch correlation."""
    out = []
    for r0, c0, size in patches:
        tpl = A[r0:r0 + size, c0:c0 + size]
        srch = B[r0 - S:r0 + size + S, c0 - S:c0 + size + S]
        if r0 - S < 0 or c0 - S < 0 or srch.shape != (size + 2 * S, size + 2 * S) or tpl.std() < 1e-6:
            continue
        p = peak(ncc_map(srch, tpl))
        if p and p[2] >= min_ncc:
            out.append((p[1] - S, -(p[0] - S)))
    r = np.array(out)
    med = np.median(r, axis=0)
    return med[0], med[1], len(r), 1.4826 * np.median(np.abs(r - med), axis=0)


def centreline_distance(cl):
    m = np.zeros(GX.shape, bool)
    cols, rows = cl[:, 0] - XMIN, YMAX - cl[:, 1]
    for c0, r0, c1, r1 in zip(cols[:-1], rows[:-1], cols[1:], rows[1:]):
        k = int(max(abs(c1 - c0), abs(r1 - r0))) + 1
        m[np.clip(np.round(np.linspace(r0, r1, k)).astype(int), 0, m.shape[0] - 1),
          np.clip(np.round(np.linspace(c0, c1, k)).astype(int), 0, m.shape[1] - 1)] = True
    return ndimage.distance_transform_edt(~m)


def nuth_kaab(dod, s, a, dist):
    flat = np.isfinite(dod) & (dist > 70) & (s < 5)
    med = np.median(dod[flat])
    sl = np.isfinite(dod) & (dist > 70) & (s > 5) & (s < 40)
    yv = (dod[sl] - med) / np.tan(np.radians(s[sl])); asp = np.radians(a[sl])
    ok = np.abs(yv - np.median(yv)) < 3 * 1.4826 * np.median(np.abs(yv - np.median(yv)))
    (p, q, _), *_ = np.linalg.lstsq(np.column_stack([np.cos(asp[ok]), np.sin(asp[ok]), np.ones(ok.sum())]), yv[ok], rcond=None)
    return np.hypot(p, q), np.degrees(np.arctan2(q, p)) % 360, q, p               # magnitude, direction, dE, dN


# ------------------------------------------------------------------ bank measurement
def bank_positions(Z22, Zs, cl, n):
    """Bank-face positions (u, ft from centreline, + south) at 25/50/75 % of the 2022 face height."""
    U = np.arange(0, 80.01, 0.5)
    res = []
    for k in range(len(cl)):
        E, N = cl[k, 0] + U * n[k, 0], cl[k, 1] + U * n[k, 1]
        rc = [YMAX - N - 0.5, E - XMIN - 0.5]
        p22 = ndimage.map_coordinates(Z22, rc, order=1, cval=np.nan)
        ok = np.isfinite(p22)
        row = dict(station=k, levels=None, face=None, u={}, slope=np.nan)
        if ok.sum() < 20:
            res.append(row); continue
        z = np.interp(U, U[ok], p22[ok]); z = ndimage.uniform_filter1d(z, 5)
        start = np.argmax(ok)                                              # water's edge (first valid sample)
        dz = np.gradient(z, U)
        dz[:start] = 0
        # candidate faces = runs steeper than ~8.5 deg (gaps < 3 ft bridged); the south bank is the TALLEST
        # one, so a low gravel-bar edge in front of the main bank is not mistaken for it
        steep = dz > 0.15
        idx = np.flatnonzero(steep)
        for a, b in zip(idx[:-1], idx[1:]):
            if 1 < b - a <= 6:                                              # bridge gaps up to 3 ft
                steep[a:b] = True
        lab, nl = ndimage.label(steep)
        runs = [(int(np.flatnonzero(lab == q)[0]), int(np.flatnonzero(lab == q)[-1])) for q in range(1, nl + 1)]
        if not runs:
            res.append(row); continue
        lo, hi = max(runs, key=lambda r: z[r[1]] - z[r[0]])
        i = lo + int(np.argmax(dz[lo:hi + 1]))
        ztoe, ztop = z[lo], z[hi]
        if ztop - ztoe < 2.0:
            res.append(row); continue
        # where the bank runs straight up into the valley wall, only its lowest 12 ft (the part the creek
        # works on) is used for the measurement levels
        hgt = min(ztop - ztoe, FACE_CAP_FT)
        hi = lo + int(np.searchsorted(z[lo:hi + 1], ztoe + hgt))
        hi = min(hi, len(U) - 1)
        levels = [ztoe + f * hgt for f in (0.25, 0.5, 0.75)]
        # is the bank face set back behind a RAISED bar/bench? (ground in front of it well above the channel bottom)
        Uf = np.arange(-40, 80.01, 0.5)
        pf = ndimage.map_coordinates(Z22, [YMAX - (cl[k, 1] + Uf * n[k, 1]) - 0.5, cl[k, 0] + Uf * n[k, 0] - XMIN - 0.5],
                                     order=1, cval=np.nan)
        z_chan = np.nanpercentile(pf, 2)
        raised = float(np.nanmedian(p22[start:lo]) - z_chan) if lo - start > 2 else 0.0
        row.update(levels=levels, face=(U[lo], U[hi], ztoe, ztop), slope=np.degrees(np.arctan(dz[i])),
                   gap=float(U[lo] - U[start]), raised=raised)
        for name, Zy in Zs.items():
            py = ndimage.map_coordinates(Zy, rc, order=1, cval=np.nan)
            us = []
            for L in levels:
                w = slice(max(0, lo - 40), min(len(U), hi + 41))           # search +/-20 ft around the face
                seg, uu = py[w], U[w]
                cross = np.flatnonzero((seg[:-1] < L) & (seg[1:] >= L) & np.isfinite(seg[:-1]) & np.isfinite(seg[1:]))
                if len(cross) == 0:
                    us.append(np.nan); continue
                target = np.interp(L, z[lo:hi + 1], U[lo:hi + 1])
                j = cross[np.argmin(np.abs(uu[cross] - target))]
                us.append(uu[j] + (L - seg[j]) / (seg[j + 1] - seg[j]) * 0.5)
            row["u"][name] = us
        res.append(row)
    return res


def write_line_shp(path, pts, source):
    with shapefile.Writer(path, shapeType=shapefile.POLYLINE) as w:
        w.field("Source", "C", 60)
        segs, cur = [], []
        for p in pts:
            if p is None:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            segs.append(cur)
        w.line(segs); w.record(source)
    with open(path + ".prj", "w") as f:
        f.write(CRS.from_epsg(2260).to_wkt("WKT1_ESRI"))


def write_tif(path, Z, desc):
    with rasterio.open(path, "w", driver="GTiff", width=Z.shape[1], height=Z.shape[0], count=1, dtype="float32",
                       crs="EPSG:2260", transform=from_origin(XMIN, YMAX, 1.0, 1.0), nodata=-9999.0,
                       compress="deflate", predictor=3) as ds:
        ds.write(np.where(np.isfinite(Z), Z, -9999.0).astype("float32"), 1)
        ds.update_tags(1, DESCRIPTION=desc)


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    os.makedirs(LID, exist_ok=True)
    raw = sys.argv[1] if len(sys.argv) > 1 else None
    for y in SURVEYS:
        if not os.path.exists(os.path.join(LID, f"LiDAR_{SURVEYS[y]['tag']}_points_clip.csv")):
            if not raw:
                sys.exit(f"clipped points for {y} missing - pass the folder holding the raw .las tiles")
            print("clipped", clip_to_csv(raw, y))
    pts = {y: load_points(y) for y in SURVEYS}
    cl = np.array(shapefile.Reader(os.path.join(GIS, "Centerline_Ref.shp")).shape(0).points)
    t = np.gradient(cl, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = np.column_stack([t[:, 1], -t[:, 0]])                              # toward the south (right) bank
    dist = centreline_distance(cl)
    acc = []

    # --- 1. lidar-to-lidar alignment from roofs
    def surf_feature(p):
        k = p["c"] != 7
        Z = tin(p["x"][k], p["y"][k], p["z"][k])
        Z = np.nan_to_num(Z, nan=np.nanmedian(Z))
        return ndimage.gaussian_filter(np.clip(Z - ndimage.minimum_filter(Z, size=41), 0, 40), 1.0)
    F11, F22 = surf_feature(pts[2011]), surf_feature(pts[2022])
    patches = [(r, c, 60) for r in range(300, 470, 40) for c in range(0, 900, 60) if (F11[r:r + 60, c:c + 60] > 10).mean() > 0.15]
    patches += [(r, c, 60) for r in range(40, 250, 40) for c in range(700, 890, 40) if (F11[r:r + 60, c:c + 60] > 10).mean() > 0.15]
    dE, dN, nm, spread = match(F11, F22, patches, 12, 0.7)
    acc.append(["2022 vs 2011 horizontal offset (house roofs)", f"{dE:+.2f}", f"{dN:+.2f}", nm, f"{spread[0]:.2f}/{spread[1]:.2f}"])
    # refine with the slope/aspect test on ground surfaces (after applying the roof offset)
    g = {y: np.isin(pts[y]["c"], SURVEYS[y]["ground"]) for y in SURVEYS}
    D11 = tin(pts[2011]["x"][g[2011]] + dE, pts[2011]["y"][g[2011]] + dN, pts[2011]["z"][g[2011]], SURVEYS[2011]["maxgap"])
    D22 = tin(pts[2022]["x"][g[2022]], pts[2022]["y"][g[2022]], pts[2022]["z"][g[2022]], SURVEYS[2022]["maxgap"])
    s11, a11 = slope_aspect(D11)
    mag, dirn, rE, rN = nuth_kaab(D22 - D11, s11, a11, dist)
    dE, dN = dE + rE, dN + rN
    acc.append(["refinement from slope/aspect test on ground", f"{rE:+.2f}", f"{rN:+.2f}", "", f"residual {mag:.2f} ft"])
    acc.append(["2022 vs 2011 offset applied", f"{dE:+.2f}", f"{dN:+.2f}", "", ""])

    # --- 2. tie 2022 to the imagery frame (lidar intensity vs NYS 2025 infrared band)
    with rasterio.open(os.path.join(IMG, "NYS_2025_CIR.tif")) as ds:
        nir = ds.read(1).astype(float).reshape(500, 2, 950, 2).mean(axis=(1, 3))
    feat = lambda a: ndimage.gaussian_filter(np.log(np.clip(a, 1, None)), 2) - ndimage.gaussian_filter(np.log(np.clip(a, 1, None)), 10)
    I22 = tin(pts[2022]["x"][g[2022]], pts[2022]["y"][g[2022]], np.log(np.clip(pts[2022]["i"][g[2022]], 1, None)))
    I22 = np.exp(np.nan_to_num(I22, nan=np.nanmedian(I22)))
    ok22 = np.isfinite(D22)
    patches = [(r, c, 60) for r in range(15, 425, 30) for c in range(15, 875, 30) if ok22[r:r + 60, c:c + 60].mean() > 0.6]
    iE, iN, ni, isp = match(feat(nir), feat(I22), patches, 15, 0.5)
    acc.append(["2022 lidar vs imagery frame (intensity vs NIR)", f"{iE:+.2f}", f"{iN:+.2f}", ni, f"{isp[0]:.2f}/{isp[1]:.2f}"])
    shift = {2022: (-iE, -iN), 2011: (dE - iE, dN - iN)}

    # --- 3. ground surfaces in the imagery frame, vertical bias, accuracy by slope
    D = {y: tin(pts[y]["x"][g[y]] + shift[y][0], pts[y]["y"][g[y]] + shift[y][1], pts[y]["z"][g[y]], SURVEYS[y]["maxgap"])
         for y in SURVEYS}
    dod = D[2022] - D[2011]
    s22, _ = slope_aspect(D[2022]); s11, a11 = slope_aspect(D[2011])
    flat = np.isfinite(dod) & (dist > 70) & (s22 < 5)
    bias = float(np.median(dod[flat]))
    D[2022] = D[2022] - bias; dod = dod - bias
    acc.append(["vertical bias removed (flat stable ground)", "", f"{bias:+.3f}", int(flat.sum()), ""])
    lod_tab = []
    for lo, hi in [(0, 5), (5, 15), (15, 30), (30, 60)]:
        m = np.isfinite(dod) & (dist > 70) & (s22 >= lo) & (s22 < hi)
        v = dod[m]; nmad = 1.4826 * np.median(np.abs(v - np.median(v)))
        lod_tab.append(((lo + hi) / 2, nmad))
        acc.append([f"stable ground {lo}-{hi} deg: noise (NMAD) / 95% detection limit", "", f"{nmad:.2f}", int(m.sum()), f"{1.96 * nmad:.2f}"])
    mag, dirn, _, _ = nuth_kaab(dod, s11, a11, dist)
    acc.append(["residual horizontal misalignment after correction", "", "", "", f"{mag:.2f} ft"])
    slope_max = np.fmax(s22, s11)
    lod = 1.96 * np.interp(slope_max, [c for c, _ in lod_tab], [v for _, v in lod_tab])
    write_tif(os.path.join(LID, "Ground_DEM_2011_Nov_1ft.tif"), D[2011], "Bare-ground elevation ft NAVD88, lidar 2011-11-19, imagery frame")
    write_tif(os.path.join(LID, "Ground_DEM_2022_Apr_1ft.tif"), D[2022], "Bare-ground elevation ft NAVD88, lidar 2022-04-15, imagery frame")
    write_tif(os.path.join(GIS, "LiDAR_Change_2011_2022.tif"), dod, "Ground elevation change 2022 minus 2011, ft (- = loss)")

    # --- 4. south bank positions + interpolation uncertainty (2022 thinned to 2011 density)
    res = bank_positions(D[2022], {2011: D[2011], 2022: D[2022]}, cl, n)
    # thinning test: 2022 thinned to 2011 density (10 random draws), bank re-measured -> error of the
    # 3-level mean position caused by sparse sampling (bias + 95 % range)
    rng = np.random.default_rng(1)
    frac = g[2011].sum() / g[2022].sum()
    diffs = []
    x22, y22, z22 = pts[2022]["x"][g[2022]] + shift[2022][0], pts[2022]["y"][g[2022]] + shift[2022][1], pts[2022]["z"][g[2022]] - bias
    for rep in range(10):
        keep = rng.random(len(x22)) < frac
        Dthin = tin(x22[keep], y22[keep], z22[keep], SURVEYS[2011]["maxgap"])
        rt = bank_positions(D[2022], {"thin": Dthin, 2022: D[2022]}, cl, n)
        for r in rt:
            if r["levels"]:
                d3 = np.array(r["u"]["thin"]) - np.array(r["u"][2022])
                if np.isfinite(d3).any():
                    diffs.append(np.nanmean(d3))
    diffs = np.array(diffs)
    dens_bias = float(np.median(diffs))
    dens95 = float(np.percentile(np.abs(diffs - dens_bias), 95))
    acc.append(["sparse-2011-sampling effect on bank position (thinning test, 10 draws)", "", f"bias {dens_bias:+.2f}",
                len(diffs), f"95% range +/-{dens95:.2f} ft"])
    s_align = 0.4                                                          # 1-sigma residual alignment, ft
    with open(os.path.join(RES, "LiDAR_Alignment_and_Accuracy.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Item", "dE_ft", "dN_or_value_ft", "N", "Spread / note"]); w.writerows(acc)

    rows, b11, b22 = [], [], []
    for r in res:
        k = r["station"]
        if not r["levels"] or 2011 not in r["u"]:
            rows.append([k, k * 10, "no bank face"] + [""] * 12); b11.append(None); b22.append(None); continue
        u11, u22 = np.array(r["u"][2011]), np.array(r["u"][2022])
        mv = u22 - u11
        mv_mean = np.nanmean(mv) if np.isfinite(mv).any() else np.nan
        # 95 % detection limit: sparse sampling (measured) + residual alignment + vertical noise on the face
        lod95 = np.sqrt(dens95 ** 2 + (1.96 * s_align) ** 2 + (1.96 * 0.3 / np.tan(np.radians(max(r["slope"], 10)))) ** 2)
        real = "yes" if np.isfinite(mv_mean) and abs(mv_mean) > lod95 else "no"
        setback = r["gap"] > SETBACK_FT and r["raised"] > 1.5
        setting = f"set back {r['gap']:.0f} ft behind a raised bar/bench" if setback else "creek-facing"
        rows.append([k, k * 10, setting, round(r["face"][2], 1), round(r["face"][3], 1), round(r["slope"], 0),
                     round(u11[1], 1) if np.isfinite(u11[1]) else "", round(u22[1], 1) if np.isfinite(u22[1]) else "",
                     *[round(v, 1) if np.isfinite(v) else "" for v in mv],
                     round(mv_mean, 1) if np.isfinite(mv_mean) else "", round(lod95, 1), real,
                     round(mv_mean / YEARS_APART, 2) if np.isfinite(mv_mean) else ""])
        for store, uu in ((b11, u11[1]), (b22, u22[1])):
            store.append(tuple(cl[k] + uu * n[k]) if np.isfinite(uu) and setting == "creek-facing" else None)
    # column indices after adding Bank_setting: 2 setting, 11 mean move, 12 limit, 13 real, 14 rate
    hdr = ["Station", "Station_ft", "Bank_setting", "Face_toe_ft", "Face_top_ft", "Face_slope_deg", "Bank_u_2011_ft", "Bank_u_2022_ft",
           "Move_25pct_ft", "Move_50pct_ft", "Move_75pct_ft", "Move_mean_ft", "Detection_limit_95pct_ft", "Real_change",
           "Rate_ft_per_yr"]
    with open(os.path.join(RES, "LiDAR_South_Bank_Change.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(rows)
        w.writerow([]); w.writerow([f"Lidar 2011-11-19 vs 2022-04-15 ({YEARS_APART:.1f} yr). Move > 0 = south bank moved away "
                                    f"from the channel toward the houses (erosion). Bank_u = distance from the reference centreline "
                                    f"at mid-height of the bank face. 'Set back' = the high bank stands more than {SETBACK_FT:.0f} ft "
                                    f"behind the water's edge (behind a gravel bar or bench), so changes there are not creek erosion "
                                    f"(e.g. yard fill at stations 60-64)."])
    write_line_shp(os.path.join(GIS, "South_Bank_2011_LiDAR"), b11, "USGS lidar 2011-11-19 (mid-height of bank face)")
    write_line_shp(os.path.join(GIS, "South_Bank_2022_LiDAR"), b22, "NYS lidar 2022-04-15 (mid-height of bank face)")
    summ = []
    for zn, a0, a1 in ZONES:
        zr = [r for r in rows if a0 <= r[0] <= a1 and r[11] != "" and r[2] == "creek-facing"]
        nset = sum(1 for r in rows if a0 <= r[0] <= a1 and r[2].startswith("set back"))
        if not zr:
            summ.append([zn, f"{a0}-{a1}", 0, nset, "", "", "", "", "", ""]); continue
        v = np.array([r[11] for r in zr], float)
        summ.append([zn, f"{a0}-{a1}", v.size, nset, round(float(np.median(v)), 1), round(float(v.max()), 1),
                     zr[int(np.argmax(v))][0], sum(1 for r in zr if r[13] == "yes" and r[11] > 0),
                     sum(1 for r in zr if r[13] == "yes" and r[11] < 0), round(float(v.max()) / YEARS_APART, 2)])
    with open(os.path.join(RES, "LiDAR_South_Bank_Zone_Summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Section", "Stations", "N_creek_facing_transects", "N_set_back_transects", "Median_move_ft",
                    "Max_retreat_ft", "Max_at_station", "N_real_retreat", "N_real_build_up", "Max_rate_ft_per_yr"])
        w.writerows(summ)
        w.writerow([]); w.writerow(["Creek-facing south bank only. Move > 0 = retreat toward the houses. "
                                    f"Nov 2011 to Apr 2022 = {YEARS_APART:.1f} yr."])
    for s in summ:
        print(s)

    # --- 5. figures
    E1, E2, N1, N2 = 636000, 636800, 863760, 864060
    c0, c1, r0, r1 = E1 - int(XMIN), E2 - int(XMIN), int(YMAX) - N2, int(YMAX) - N1
    hs = hillshade(D[2022])[r0:r1, c0:c1]
    dd = np.where(np.abs(dod) >= lod, dod, np.nan)[r0:r1, c0:c1]
    fig, ax = plt.subplots(figsize=(13, 5.6))
    ax.imshow(hs, cmap="gray", extent=[E1, E2, N1, N2], vmin=0, vmax=1)
    im = ax.imshow(dd, cmap="RdBu", vmin=-6, vmax=6, extent=[E1, E2, N1, N2], alpha=0.85)
    ax.plot(cl[:, 0], cl[:, 1], color="k", lw=0.6, ls=":")
    for pts_, st, lab in ((b11, "--", "south bank 2011 (creek-facing)"), (b22, "-", "south bank 2022 (creek-facing)")):
        segs, cur = [], []
        for p in pts_ + [None]:
            if p is None:
                if len(cur) > 1:
                    segs.append(np.array(cur))
                cur = []
            else:
                cur.append(p)
        for i, sgm in enumerate(segs):
            ax.plot(*sgm.T, st, color="darkgreen" if st == "-" else "orange", lw=1.3, label=lab if i == 0 else None)
    arrow = dict(arrowstyle="->", color="k", lw=0.8)
    ax.annotate("South bank retreat up to 9 ft\n(stations 72-75)", xy=(636508, 863905), xytext=(636560, 863845),
                fontsize=8, arrowprops=arrow, bbox=dict(fc="w", ec="none", alpha=0.8))
    ax.annotate("Yard fill (terraced lot)", xy=(636420, 863800), xytext=(636250, 863790), fontsize=8, arrowprops=arrow,
                bbox=dict(fc="w", ec="none", alpha=0.8))
    ax.annotate("North bank eroding\n(channel moving north)", xy=(636420, 863938), xytext=(636345, 864020), fontsize=8,
                arrowprops=arrow, bbox=dict(fc="w", ec="none", alpha=0.8))
    for k in range(0, len(cl), 10):
        if E1 < cl[k, 0] < E2 and N1 < cl[k, 1] < N2:
            ax.text(cl[k, 0] - 25 * n[k, 0], cl[k, 1] - 25 * n[k, 1], str(k), fontsize=7, ha="center", va="center")
    cb = plt.colorbar(im, ax=ax, shrink=0.8); cb.set_label("Ground change 2011 to 2022 (ft)\nred = lost, blue = gained")
    ax.set_xlim(E1, E2); ax.set_ylim(N1, N2); ax.legend(fontsize=7, loc="lower left")
    ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
    ax.set_title("Lidar ground change, Nov 2011 to Apr 2022 (changes smaller than the detection limit hidden); "
                 "numbers = stations", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "LiDAR_Change_Map.png"), dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 4.4))
    mr = [r for r in rows if r[11] != ""]
    st = np.array([r[0] for r in mr]); mv = np.array([r[11] for r in mr], float); lim = np.array([r[12] for r in mr], float)
    creek = np.array([r[2] == "creek-facing" for r in mr])
    ax.fill_between(st * 10, -lim, lim, color="0.88", step="mid", label="detection limit (95 %)")
    col = np.where(mv > lim, "firebrick", np.where(mv < -lim, "steelblue", "0.45"))
    ax.bar(st[creek] * 10, mv[creek], width=8, color=col[creek])
    ax.bar(st[~creek] * 10, mv[~creek], width=8, color="none", edgecolor="0.55", hatch="////", lw=0.5)
    from matplotlib.patches import Patch
    handles = [Patch(color="0.88", label="detection limit (95 %)"),
               Patch(color="firebrick", label="real retreat (creek-facing bank)"),
               Patch(color="steelblue", label="real build-up (creek-facing bank)"),
               Patch(color="0.45", label="within noise"),
               Patch(facecolor="none", edgecolor="0.55", hatch="////", label="bank set back behind a raised bar (not creek erosion)")]
    ax.axhline(0, color="k", lw=0.8)
    for zn, a0, a1 in ZONES:
        ax.axvline(a0 * 10 - 5, color="0.5", lw=0.6, ls=":")
        ax.text(a0 * 10, 0.97, zn, transform=ax.get_xaxis_transform(), fontsize=7, va="top", color="0.3")
    ax.set_xlabel("Distance along the creek, ft (station x 10; downstream ->)")
    ax.set_ylabel("South bank movement, ft\n(+ = toward houses)")
    ax.set_title(f"South bank movement from lidar, Nov 2011 to Apr 2022 ({YEARS_APART:.1f} yr)", fontsize=9)
    ax.legend(handles=handles, fontsize=7, loc="lower left", ncol=3)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "LiDAR_South_Bank_Movement.png"), dpi=150); plt.close(fig)

    U = np.arange(-40, 80.01, 0.5)
    fig, axes = plt.subplots(4, 4, figsize=(16, 11), squeeze=False)
    for ax, k in zip(axes.ravel(), PROFILE_STATIONS):
        for y, col in ((2011, "tab:blue"), (2022, "tab:red")):
            px, py = pts[y]["x"][g[y]] + shift[y][0] - cl[k, 0], pts[y]["y"][g[y]] + shift[y][1] - cl[k, 1]
            u, v = px * n[k, 0] + py * n[k, 1], px * t[k, 0] + py * t[k, 1]
            m = (np.abs(v) <= 2.5) & (u >= U[0]) & (u <= U[-1])
            ax.scatter(u[m], pts[y]["z"][g[y]][m] - (bias if y == 2022 else 0), s=4, color=col, alpha=0.55)
            zz = ndimage.map_coordinates(D[y], [YMAX - (cl[k, 1] + U * n[k, 1]) - 0.5, cl[k, 0] + U * n[k, 0] - XMIN - 0.5],
                                         order=1, cval=np.nan)
            ax.plot(U, zz, color=col, lw=1, label=f"{SURVEYS[y]['date']}")
        rr = rows[k]
        if rr[11] != "":
            note = "real" if rr[13] == "yes" else "within noise"
            if rr[2] != "creek-facing":
                note += ", bank set back"
            ax.set_title(f"Station {k}: south bank moved {rr[11]:+.1f} ft ({note})", fontsize=8, loc="left")
        else:
            ax.set_title(f"Station {k}: no distinct bank face", fontsize=8, loc="left")
        ax.axvline(0, color="0.6", lw=0.5, ls=":"); ax.tick_params(labelsize=6)
    axes[0, 0].legend(fontsize=6)
    fig.supxlabel("Distance from creek centreline, ft (- north bank | + south bank)", fontsize=9)
    fig.supylabel("Ground elevation, ft NAVD88", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "LiDAR_South_Bank_Profiles.png"), dpi=130); plt.close(fig)
    print("done")
