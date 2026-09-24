r"""
Step 2 - Align every year to NYS 2025 and build the reference centreline + transects.

Outputs
  4_Results\Coregistration_Offsets.csv   offset of each image vs NYS 2025 (ft), from patch matching on
                                          houses/streets/Samsondale Ave (stable features)
  3_GIS\Centerline_Ref.shp               reference channel centreline (least-cost path along the
                                          multi-year mean 'non-red' channel signal)
  3_GIS\Transects_10ft.shp               transects every 10 ft, -30 ft (north/left) to +45 ft (south/right)
  3_GIS\Analysis_Area.shp                extent of the imagery clips
  3_GIS\Bank_Lines.shp                   EMPTY template for tracing bank lines (only created if missing)
  4_Results\M_Bend_2007_2016_2025.png    aligned imagery of the M (2007 / 2016 / 2025) with the reference centreline
All in NAD83 NY State Plane East, US ft (EPSG 2260).
"""
import csv
import glob
import os

import numpy as np
import rasterio
import shapefile                      # pyshp
from pyproj import CRS
from scipy import ndimage
from scipy.signal import fftconvolve
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG, GIS, RES = (os.path.join(ROOT, d) for d in ("1_Imagery", "3_GIS", "4_Results"))
XMIN, YMAX, PIX = 635900.0, 864150.0, 0.5
REF = "NYS_2025_RGB"
PRJ = CRS.from_epsg(2260).to_wkt("WKT1_ESRI")


# ---------------------------------------------------------------- co-registration
def gray(path):
    with rasterio.open(path) as ds:
        return np.mean([ds.read(b).astype(float) for b in (1, 2, 3)], axis=0)


def dog(g):
    return ndimage.gaussian_filter(g, 1.0) - ndimage.gaussian_filter(g, 6.0)


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


def offsets(ref, tgt, patch=80, step=50, search=30, min_ncc=0.35):
    """Median offset of target vs reference from many small patches on stable ground."""
    regions = [(640, 1000, 0, 1900), (0, 420, 1560, 1900)]      # houses/streets strip; Samsondale Ave
    out = []
    for r0, r1, c0, c1 in regions:
        for r in range(r0 + search, r1 - patch - search, step):
            for c in range(c0 + search, c1 - patch - search, step):
                tpl = ref[r:r + patch, c:c + patch]
                if tpl.std() < 2.0:
                    continue
                p = peak(ncc_map(tgt[r - search:r + patch + search, c - search:c + patch + search], tpl))
                if p and p[2] >= min_ncc:
                    out.append((p[0] - search, p[1] - search))
    s = np.array(out)
    if len(s) < 10:
        return None
    dy, dx = np.median(s, axis=0)
    spread = 1.4826 * np.median(np.abs(s - [dy, dx]), axis=0)
    return dx * PIX, -dy * PIX, spread[1] * PIX, spread[0] * PIX, len(s)


# ---------------------------------------------------------------- centreline + transects
def z_redness(path):
    with rasterio.open(path) as ds:
        a = np.dstack([ds.read(b).astype(float) for b in (1, 2, 3)])
    r = ndimage.gaussian_filter((a[..., 0] - a[..., 2]) / (a.sum(axis=2) + 1e-9), 2.0)
    valid = a.sum(axis=2) > 0
    q1, med, q3 = np.percentile(r[valid], [25, 50, 75])
    z = (r - med) / (q3 - q1 + 1e-9); z[~valid] = np.nan
    return z


def least_cost_path(cost, start, end):
    H, W = cost.shape
    idx = np.arange(H * W).reshape(H, W)
    rows, cols, wts = [], [], []
    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        y0, y1, x0, x1 = max(0, -dy), H - max(0, dy), max(0, -dx), W - max(0, dx)
        a, b = idx[y0:y1, x0:x1].ravel(), idx[y0 + dy:y1 + dy, x0 + dx:x1 + dx].ravel()
        w = np.hypot(dy, dx) * 0.5 * (cost[y0:y1, x0:x1].ravel() + cost[y0 + dy:y1 + dy, x0 + dx:x1 + dx].ravel())
        rows += [a, b]; cols += [b, a]; wts += [w, w]
    G = coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(H * W,) * 2).tocsr()
    _, pred = dijkstra(G, indices=idx[start], return_predecessors=True)
    path = [idx[end]]
    while path[-1] != idx[start]:
        path.append(pred[path[-1]])
    return np.column_stack(np.unravel_index(np.array(path[::-1]), (H, W))).astype(float)


def centreline(offs):
    """Least-cost path along the multi-year mean channel signal (images shifted into the 2025 frame)."""
    zs = []
    for name, (oe, on, *_ ) in offs.items():
        if not name.endswith("_RGB") or name.startswith("NYS_2004"):
            continue
        z = z_redness(os.path.join(IMG, name + ".tif"))
        zs.append(ndimage.shift(np.nan_to_num(z, nan=0.0), (on / PIX, -oe / PIX), order=1, cval=0.0))
    zmean = np.mean(zs, axis=0)
    cost = ndimage.zoom(np.exp(np.clip(zmean, -3, 3) * 1.5), 0.5, order=1)          # 1-ft grid
    zc = ndimage.zoom(zmean, 0.5, order=1)
    start = (300 + int(np.argmin(zc[300:, 3])), 3)                                  # west-edge entry
    end = (250 + int(np.argmin(zc[250:, -4])), zc.shape[1] - 4)                     # east-edge exit
    path = least_cost_path(cost, start, end) * 2.0
    k = np.ones(41) / 41                                                            # 20-ft moving average
    pad = np.pad(path, ((20, 20), (0, 0)), mode="edge")
    sm = np.column_stack([np.convolve(pad[:, i], k, mode="valid") for i in range(2)])
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(sm, axis=0).T))])
    t = np.arange(0, s[-1], 10.0 / PIX)                                             # station every 10 ft
    cl = np.column_stack([np.interp(t, s, sm[:, 0]), np.interp(t, s, sm[:, 1])])
    return np.column_stack([XMIN + (cl[:, 1] + 0.5) * PIX, YMAX - (cl[:, 0] + 0.5) * PIX])   # E, N


def write_prj(base):
    with open(base + ".prj", "w") as f:
        f.write(PRJ)


if __name__ == "__main__":
    os.makedirs(GIS, exist_ok=True); os.makedirs(RES, exist_ok=True)
    ref = dog(gray(os.path.join(IMG, REF + ".tif")))
    offs, rows = {}, []
    for f in sorted(glob.glob(os.path.join(IMG, "*.tif"))):
        name = os.path.basename(f)[:-4]
        r = (0.0, 0.0, 0.0, 0.0, 0) if name == REF else offsets(ref, dog(gray(f)))
        note = ""
        if r is None:
            note = "not aligned - too few matches; excluded from measurement"
        elif name.startswith("NYS_2004"):
            note = "1-ft source; offsets inconsistent between areas - use +/-4 ft"
        elif name.startswith("NAPP"):
            note = "1990s DOQ, ~3 ft pixels; reference only"
        if r is not None:
            offs[name] = r
        rows.append([name] + ([f"{v:.2f}" for v in r[:4]] + [r[4]] if r else ["", "", "", "", 0]) + [note])
        print(name, rows[-1][1:])
    with open(os.path.join(RES, "Coregistration_Offsets.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Image", "Offset_E_ft", "Offset_N_ft", "Spread_E_ft", "Spread_N_ft", "N_patches", "Note"])
        w.writerows(rows)

    cl = centreline(offs)
    base = os.path.join(GIS, "Centerline_Ref")
    with shapefile.Writer(base, shapeType=shapefile.POLYLINE) as sw:
        sw.field("Name", "C", 40); sw.field("Length_ft", "N", 10, 1)
        sw.line([cl.tolist()]); sw.record("Reference centreline (2007-2026 mean)", float(10 * (len(cl) - 1)))
    write_prj(base)

    d = np.gradient(cl, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True)
    right = np.column_stack([d[:, 1], -d[:, 0]])          # (E, N) unit normal to the right of flow
    base = os.path.join(GIS, "Transects_10ft")
    with shapefile.Writer(base, shapeType=shapefile.POLYLINE) as sw:
        sw.field("Station", "N", 5, 0); sw.field("Sta_ft", "N", 8, 0)
        sw.field("U_start", "N", 6, 1); sw.field("U_end", "N", 6, 1)
        for k, (p, n) in enumerate(zip(cl, right)):
            sw.line([[(p - 30 * n).tolist(), (p + 45 * n).tolist()]])
            sw.record(k, k * 10, -30.0, 45.0)
    write_prj(base)

    base = os.path.join(GIS, "Analysis_Area")
    with shapefile.Writer(base, shapeType=shapefile.POLYGON) as sw:
        sw.field("Name", "C", 40)
        sw.poly([[[635900, 864150], [636850, 864150], [636850, 863650], [635900, 863650], [635900, 864150]]])
        sw.record("Imagery clip extent")
    write_prj(base)
    print(f"centreline {10 * (len(cl) - 1)} ft, {len(cl)} transects")

    base = os.path.join(GIS, "Bank_Lines")
    if not os.path.exists(base + ".shp"):                    # never overwrite traced lines
        with shapefile.Writer(base, shapeType=shapefile.POLYLINE) as sw:
            sw.field("Year", "N", 4, 0); sw.field("Bank", "C", 10); sw.field("Notes", "C", 80)
        write_prj(base)

    # comparison figure: the M in 2007 / 2016 / 2026, aligned, with the same reference centreline
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    E1, E2, N1, N2 = 636080, 636760, 863830, 864060
    c0, c1, r0, r1 = int((E1 - XMIN) / PIX), int((E2 - XMIN) / PIX), int((YMAX - N2) / PIX), int((YMAX - N1) / PIX)
    fig, axes = plt.subplots(3, 1, figsize=(11, 12))
    for ax, name, label in zip(axes, ["NYS_2007_RGB", "NYS_2016_RGB", "NYS_2025_RGB"],
                               ["NYS 2007", "NYS 2016", "NYS 2025"]):
        with rasterio.open(os.path.join(IMG, name + ".tif")) as ds:
            a = np.dstack([ds.read(b).astype(float) for b in (1, 2, 3)])
        oe, on = offs[name][:2]
        sub = np.dstack([ndimage.shift(a[..., b], (on / PIX, -oe / PIX), order=1) for b in range(3)])[r0:r1, c0:c1]
        lo, hi = np.percentile(sub, [1, 99.5])
        ax.imshow(np.clip((sub - lo) / (hi - lo), 0, 1), extent=[E1, E2, N1, N2])
        ax.plot(cl[:, 0], cl[:, 1], color="cyan", lw=1.0, label="reference centreline (identical on every panel)")
        for k in range(0, len(cl), 10):
            if E1 < cl[k, 0] < E2 and N1 < cl[k, 1] < N2:
                ax.plot(*cl[k], "o", color="cyan", ms=3); ax.text(cl[k, 0] + 4, cl[k, 1] + 4, str(k), color="yellow", fontsize=8)
        ax.set_xlim(E1, E2); ax.set_ylim(N1, N2); ax.set_title(label, fontsize=10, loc="left")
        ax.ticklabel_format(useOffset=False, style="plain"); ax.tick_params(labelsize=7)
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Minisceongo Creek M-bend, aligned imagery (NY State Plane East ft; yellow = transect station)", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "M_Bend_2007_2016_2025.png"), dpi=150); plt.close(fig)
