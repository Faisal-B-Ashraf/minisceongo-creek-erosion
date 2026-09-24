r"""
Step 5 - Measure bank movement from traced bank lines (DSAS-style transect method).

Input   3_GIS\Bank_Lines.shp   polylines traced on the imagery, one or more per year and bank
                               fields: Year (int), Bank ('South' or 'North')
        3_GIS\Transects_10ft.shp  from step 2
Output  4_Results\Bank_Positions.csv    distance of each bank line from the reference centreline, per transect
        4_Results\Bank_Migration.csv    retreat since the first year, end-point rate and regression rate
        4_Results\Zone_Summary.csv      the same, summarised by section of the M
        4_Results\Bank_Migration_Chart.png, 4_Results\Bank_Lines_Map.png
        3_GIS\Bank_Crossings.shp        the measured crossing points

Sign convention: retreat > 0 means the bank moved away from the channel (erosion);
                 retreat < 0 means it moved toward the channel (deposition).
usage: python 05_measure_traced_bank_lines.py [bank_lines.shp] [output_folder]
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import shapefile
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString, Point

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIS, RES, IMG = (os.path.join(ROOT, d) for d in ("3_GIS", "4_Results", "1_Imagery"))
LINES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(GIS, "Bank_Lines.shp")
OUT = sys.argv[2] if len(sys.argv) > 2 else RES

# Sections of the M (transect station numbers, 10 ft apart)
ZONES = [("West limb", 0, 35), ("First hump (inside bend)", 36, 57), ("Dip (outside bend)", 58, 75),
         ("Pool / second hump", 76, 99), ("East limb", 100, 127)]
# 1-sigma position uncertainty per year (ft): image alignment (see Coregistration_Offsets.csv) combined
# with ~2 ft for tracing the edge by eye on 0.5-0.75 ft pixels
ALIGN_FT = {2004: 4.0}
DIGITISE_FT = 2.0


def year_sigma(y):
    return float(np.hypot(ALIGN_FT.get(y, 1.5), DIGITISE_FT))


def read_lines(path):
    r = shapefile.Reader(path)
    names = [f[0].lower() for f in r.fields[1:]]
    iy, ib = names.index("year"), names.index("bank")
    out = {}
    for sr in r.iterShapeRecords():
        pts, parts = sr.shape.points, list(sr.shape.parts) + [len(sr.shape.points)]
        segs = [pts[a:b] for a, b in zip(parts[:-1], parts[1:]) if b - a >= 2]
        key = (int(sr.record[iy]), str(sr.record[ib]).strip().title())
        out.setdefault(key, []).extend(segs)
    return {k: MultiLineString(v) for k, v in out.items()}


def crossing_u(transect, start, direction, bank_geom, bank):
    """Signed distance u (ft from the centreline) where the transect crosses the bank line."""
    x = transect.intersection(bank_geom)
    pts = [x] if isinstance(x, Point) else [g for g in getattr(x, "geoms", []) if isinstance(g, Point)]
    if not pts:
        return np.nan
    us = [np.dot(np.array(p.coords[0]) - start, direction) - 30.0 for p in pts]
    target = 10.0 if bank == "South" else -10.0              # typical bank offset; picks the relevant crossing
    return float(min(us, key=lambda u: abs(u - target)))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tr = shapefile.Reader(os.path.join(GIS, "Transects_10ft.shp"))
    transects = []
    for sr in tr.iterShapeRecords():
        a, b = np.array(sr.shape.points[0]), np.array(sr.shape.points[-1])
        transects.append((int(sr.record[0]), LineString([a, b]), a, (b - a) / np.linalg.norm(b - a)))
    lines = read_lines(LINES)
    banks = sorted({b for _, b in lines})
    rows, crossings, mig, summary = [], [], [], []
    for bank in banks:
        years = sorted(y for y, b in lines if b == bank)
        U = np.full((len(years), len(transects)), np.nan)
        for i, y in enumerate(years):
            for j, (st, line, a, d) in enumerate(transects):
                U[i, j] = crossing_u(line, a, d, lines[(y, bank)], bank)
                if np.isfinite(U[i, j]):
                    rows.append([bank, st, st * 10, y, round(U[i, j], 2)])
                    crossings.append((a + d * (U[i, j] + 30.0), bank, st, y, U[i, j]))
        sign = 1.0 if bank == "South" else -1.0              # retreat = movement away from the channel
        t = np.array(years, float)
        for j, (st, *_ ) in enumerate(transects):
            ok = np.isfinite(U[:, j])
            if ok.sum() < 2:
                continue
            ty, uy = t[ok], U[ok, j] * sign
            first, last = int(ty[0]), int(ty[-1])
            total = uy[-1] - uy[0]
            sig = np.hypot(year_sigma(first), year_sigma(last))
            epr = total / (ty[-1] - ty[0])
            if ok.sum() >= 3:
                A = np.column_stack([ty - ty.mean(), np.ones_like(ty)])
                coef, res, *_ = np.linalg.lstsq(A, uy, rcond=None)
                dof = ok.sum() - 2
                se = np.sqrt((res[0] / dof if dof > 0 and res.size else 0.0) / np.sum((ty - ty.mean()) ** 2)) if dof > 0 else np.nan
                lrr, lrr_se = coef[0], se
            else:
                lrr, lrr_se = np.nan, np.nan
            mig.append([bank, st, st * 10, first, last, int(ok.sum()), round(total, 1), round(sig, 1),
                        "yes" if abs(total) > 2 * sig else "no", round(epr, 2), round(sig / (ty[-1] - ty[0]), 2),
                        round(lrr, 2) if np.isfinite(lrr) else "", round(lrr_se, 2) if np.isfinite(lrr_se) else ""])
        for zn, a0, a1 in ZONES:
            m = [r for r in mig if r[0] == bank and a0 <= r[1] <= a1]
            if not m:
                continue
            tot = np.array([r[6] for r in m])
            summary.append([bank, zn, f"{a0}-{a1}", len(m), round(float(np.median(tot)), 1),
                            round(float(tot.max()), 1), m[int(np.argmax(tot))][1],
                            round(float(np.median([r[9] for r in m])), 2),
                            sum(1 for r in m if r[8] == "yes")])

    with open(os.path.join(OUT, "Bank_Positions.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Bank", "Station", "Station_ft", "Year", "Dist_from_CL_ft"]); w.writerows(rows)
    with open(os.path.join(OUT, "Bank_Migration.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Bank", "Station", "Station_ft", "First_year", "Last_year", "N_years", "Retreat_ft",
                    "Uncert_1sigma_ft", "Beyond_2sigma", "EndPoint_rate_ft_yr", "EPR_uncert_ft_yr",
                    "Regression_rate_ft_yr", "LRR_std_err_ft_yr"])
        w.writerows(mig)
    with open(os.path.join(OUT, "Zone_Summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Bank", "Section", "Stations", "N_transects", "Median_retreat_ft", "Max_retreat_ft",
                    "Max_at_station", "Median_rate_ft_yr", "N_beyond_2sigma"])
        w.writerows(summary)

    base = os.path.join(GIS if OUT == RES else OUT, "Bank_Crossings")
    with shapefile.Writer(base, shapeType=shapefile.POINT) as sw:
        for fld in (("Bank", "C", 10), ("Station", "N", 5, 0), ("Year", "N", 4, 0), ("Dist_CL", "N", 8, 2)):
            sw.field(*fld)
        for p, bank, st, y, u in crossings:
            sw.point(*p); sw.record(bank, st, y, round(float(u), 2))
    with open(base + ".prj", "w") as f:
        f.write(CRS.from_epsg(2260).to_wkt("WKT1_ESRI"))

    # chart: retreat since the first year, per transect
    fig, axes = plt.subplots(len(banks), 1, figsize=(11, 3.6 * len(banks)), squeeze=False)
    for ax, bank in zip(axes[:, 0], banks):
        years = sorted(y for y, b in lines if b == bank)
        sign = 1.0 if bank == "South" else -1.0
        base_u = {r[1]: r[4] for r in rows if r[0] == bank and r[3] == years[0]}
        cmap = plt.get_cmap("viridis", max(len(years), 2))
        for i, y in enumerate(years[1:], 1):
            pts = sorted((r[1], sign * (r[4] - base_u[r[1]])) for r in rows if r[0] == bank and r[3] == y and r[1] in base_u)
            if pts:
                ax.plot([p[0] * 10 for p in pts], [p[1] for p in pts], "-o", ms=2.5, lw=1.2, color=cmap(i), label=str(y))
        s2 = 2 * np.hypot(year_sigma(years[0]), year_sigma(years[-1]))
        ax.axhspan(-s2, s2, color="0.85", zorder=0, label="noise band (2 sigma)")
        for zn, a0, a1 in ZONES:
            ax.axvline(a0 * 10, color="0.6", lw=0.6, ls=":")
            ax.text(a0 * 10 + 5, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1, zn, fontsize=7, va="top", color="0.35")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_title(f"{bank} bank: movement since {years[0]} (+ = retreat / erosion, - = build-up)", fontsize=10)
        ax.set_xlabel("Distance along reference centreline (ft, downstream)"); ax.set_ylabel("ft")
        ax.legend(fontsize=7, ncol=6, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "Bank_Migration_Chart.png"), dpi=150); plt.close(fig)

    # map: bank lines by year over the latest imagery
    bg = os.path.join(IMG, "NYS_2025_RGB.tif")
    with rasterio.open(bg) as ds:
        img = np.dstack([ds.read(b) for b in (1, 2, 3)]); ext = [ds.bounds.left, ds.bounds.right, ds.bounds.bottom, ds.bounds.top]
    img = np.dstack([img, np.where(img.sum(axis=2) > 0, 255, 0).astype(np.uint8)])    # no-data strip transparent
    fig, ax = plt.subplots(figsize=(12, 6.8))
    ax.imshow(img, extent=ext)
    allyears = sorted({y for y, _ in lines}); cmap = plt.get_cmap("plasma", max(len(allyears), 2))
    for (y, bank), geom in sorted(lines.items()):
        for g in geom.geoms:
            xs, ys = g.xy
            ax.plot(xs, ys, color=cmap(allyears.index(y)), lw=1.6, ls="-" if bank == "South" else "--")
    for st, line, a, d in transects[::10]:
        ax.plot(*line.xy, color="w", lw=0.5, alpha=0.7); ax.text(*line.coords[-1], str(st), color="w", fontsize=7)
    handles = [plt.Line2D([], [], color=cmap(i), lw=2, label=str(y)) for i, y in enumerate(allyears)]
    ax.legend(handles=handles, fontsize=8, loc="lower right", title="Bank line year", title_fontsize=8)
    ax.set_title("Traced bank lines (solid = south bank, dashed = north bank) on NYS 2025 orthophoto", fontsize=10)
    ax.set_xlabel("NY State Plane East, E (ft)"); ax.set_ylabel("N (ft)"); ax.ticklabel_format(useOffset=False, style="plain")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "Bank_Lines_Map.png"), dpi=150); plt.close(fig)
    for r in summary:
        print(r)

