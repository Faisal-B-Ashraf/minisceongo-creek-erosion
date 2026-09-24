"""
Renders the animation frames for the web explainer from the analysis data.

Reads   <ANALYSIS_DIR>/1_Imagery, 1_LiDAR, 2_Scripts, 3_GIS, 4_Results   (default: ../analysis)
Writes  ../docs/frames/f###.webp  and  ../docs/frames.json  (steps, captions, frame list with durations)

usage:  python build_frames.py [analysis_dir]
The imagery and lidar inputs are produced by analysis/2_Scripts/01, 02 and 04.
"""
import csv, importlib.util, io, json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
from PIL import Image
import rasterio, shapefile
from scipy import ndimage
from scipy.interpolate import LinearNDInterpolator
from scipy.signal import fftconvolve
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import Delaunay

HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "analysis")
DOCS = os.path.join(HERE, "..", "docs")
FRAMES_DIR = os.path.join(DOCS, "frames")
XMIN, XMAX, YMIN, YMAX, PIX = 635900.0, 636850.0, 863650.0, 864150.0, 0.5
plt.rcParams.update({"font.family": "Arial"})

STEPS = ["The question", "Line up the photos", "Score and average", "Draw the centreline", "Stations and cross lines",
         "Lidar: two laser surveys", "Ground surfaces", "One cross-section", "Every station", "The answer"]
DPI = 80
CROP = (29, 473)                     # keep the figure band of the 960 x 540 canvas (captions live in the web page)
fig = plt.figure(figsize=(12, 6.75), dpi=DPI)
MAIN = [0.012, 0.165, 0.976, 0.755]
FRAMES, CAPTIONS = [], []


# ------------------------------------------------------------------------------------------------ helpers
OFFS = {r["Image"]: (float(r["Offset_E_ft"]), float(r["Offset_N_ft"]))
        for r in csv.DictReader(open(os.path.join(A, "4_Results", "Coregistration_Offsets.csv"))) if r["Offset_E_ft"]}
CL = np.array(shapefile.Reader(os.path.join(A, "3_GIS", "Centerline_Ref.shp")).shape(0).points)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def rgb(name):
    with rasterio.open(os.path.join(A, "1_Imagery", name + ".tif")) as ds:
        return np.dstack([ds.read(b).astype(float) for b in (1, 2, 3)])


def to_ref(a, name):
    """Slide an image back onto the NYS 2025 frame using its measured offset."""
    oe, on = OFFS[name]
    if a.ndim == 2:
        return ndimage.shift(a, (on / PIX, -oe / PIX), order=1, cval=0)
    return np.dstack([ndimage.shift(a[..., b], (on / PIX, -oe / PIX), order=1, cval=0) for b in range(a.shape[2])])


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


def z_redness(a):
    r = ndimage.gaussian_filter((a[..., 0] - a[..., 2]) / (a.sum(axis=2) + 1e-9), 2.0)
    valid = a.sum(axis=2) > 0
    q1, med, q3 = np.percentile(r[valid], [25, 50, 75])
    z = (r - med) / (q3 - q1 + 1e-9); z[~valid] = np.nan
    return z


def put(k, caption, draw, ms):
    fig.clf()
    draw()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=DPI); buf.seek(0)
    im = Image.open(buf).convert("RGB")
    im = im.crop((0, CROP[0], im.width, CROP[1]))
    name = f"f{len(FRAMES):03d}.webp"
    im.save(os.path.join(FRAMES_DIR, name), format="WEBP", quality=76, method=6)
    if not CAPTIONS or CAPTIONS[-1] != caption:
        CAPTIONS.append(caption)
    FRAMES.append(dict(f=name, d=int(ms), k=k, c=len(CAPTIONS) - 1))


def mapax(rect=MAIN):
    ax = fig.add_axes(rect); ax.set_xticks([]); ax.set_yticks([])
    return ax


def win(a, ext, cell=PIX):
    E1, E2, N1, N2 = ext
    return a[int(round((YMAX - N2) / cell)):int(round((YMAX - N1) / cell)), int(round((E1 - XMIN) / cell)):int(round((E2 - XMIN) / cell))]


def hillshade(Z):
    z = np.nan_to_num(Z, nan=np.nanmean(Z)); dy, dx = np.gradient(z)
    s = np.pi / 2 - np.arctan(np.hypot(dx, dy)); asp = np.arctan2(-dx, dy); a, b = np.radians(315), np.radians(45)
    return np.clip(np.sin(b) * np.sin(s) + np.cos(b) * np.cos(s) * np.cos(a - asp), 0, 1)


def gray_rgb(z):
    return plt.cm.gray((np.clip(z, -3, 3) + 3) / 6)[..., :3]


def shp_parts(path):
    sh = shapefile.Reader(path).shape(0); p = np.array(sh.points); parts = list(sh.parts) + [len(p)]
    return [p[a:b] for a, b in zip(parts[:-1], parts[1:])]


# ------------------------------------------------------------------------------------------------ data
os.makedirs(FRAMES_DIR, exist_ok=True)
for f in os.listdir(FRAMES_DIR):
    if f.endswith(".webp"):
        os.remove(os.path.join(FRAMES_DIR, f))
print("preparing data...")
M_EXT = [636000, 636800, 863740, 864070]
FULL = [XMIN, XMAX, YMIN, YMAX]
tng = np.gradient(CL, axis=0); tng /= np.linalg.norm(tng, axis=1, keepdims=True)
NRM = np.column_stack([tng[:, 1], -tng[:, 0]])                      # toward the south (house) bank
p25 = np.clip(rgb("NYS_2025_RGB") / 255, 0, 1)
p16 = np.clip(to_ref(rgb("NYS_2016_RGB"), "NYS_2016_RGB") / 255, 0, 1)
NAMES = ["NYS_2007_RGB", "NYS_2010_RGB", "NYS_2013_RGB", "NYS_2016_RGB", "NYS_2021_RGB", "NYS_2024_RGB", "NYS_2025_RGB"]
YEARS = ["2007", "2010", "2013", "2016", "2021", "2024", "2025"]
zs = [to_ref(np.nan_to_num(z_redness(rgb(n)), nan=0.0), n) for n in NAMES]
avgs = [np.mean(zs[:k], axis=0) for k in range(1, len(NAMES) + 1)]
# --- photo matching (as in 02_align_and_transects.py)
REG = [(640, 1000, 0, 1900), (0, 420, 1560, 1900)]
R25, T16 = dog(rgb("NYS_2025_RGB").mean(axis=2)), dog(rgb("NYS_2016_RGB").mean(axis=2))
good = []
for r0_, r1_, c0_, c1_ in REG:
    for r in range(r0_ + 30, r1_ - 110, 50):
        for c in range(c0_ + 30, c1_ - 110, 50):
            tpl = R25[r:r + 80, c:c + 80]
            if tpl.std() < 2.0:
                continue
            m = ncc_map(T16[r - 30:r + 110, c - 30:c + 110], tpl); p = peak(m)
            if p and p[2] >= 0.35:
                good.append(dict(r=r, c=c, m=m, p=p, dE=(p[1] - 30) * PIX, dN=-(p[0] - 30) * PIX))
mdE, mdN = np.median([q["dE"] for q in good]), np.median([q["dN"] for q in good])
best = max((q for q in good if q["r"] > 600), key=lambda q: q["p"][2])
# --- cheapest path on the 1-ft grid (as in 02_align_and_transects.py)
zc = ndimage.zoom(avgs[-1], 0.5, order=1)
cost = np.exp(np.clip(zc, -3, 3) * 1.5)
Hh, Ww = cost.shape
idx = np.arange(Hh * Ww).reshape(Hh, Ww)
rows_, cols_, wts_ = [], [], []
for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
    y0, y1, x0, x1 = max(0, -dy), Hh - max(0, dy), max(0, -dx), Ww - max(0, dx)
    a_, b_ = idx[y0:y1, x0:x1].ravel(), idx[y0 + dy:y1 + dy, x0 + dx:x1 + dx].ravel()
    w_ = np.hypot(dy, dx) * 0.5 * (cost[y0:y1, x0:x1].ravel() + cost[y0 + dy:y1 + dy, x0 + dx:x1 + dx].ravel())
    rows_ += [a_, b_]; cols_ += [b_, a_]; wts_ += [w_, w_]
G = coo_matrix((np.concatenate(wts_), (np.concatenate(rows_), np.concatenate(cols_))), shape=(Hh * Ww,) * 2).tocsr()
start = (300 + int(np.argmin(zc[300:, 3])), 3); end = (250 + int(np.argmin(zc[250:, -4])), Ww - 4)
d0, pred = dijkstra(G, indices=idx[start], return_predecessors=True)
pth = [idx[end]]
while pth[-1] != idx[start]:
    pth.append(pred[pth[-1]])
pth = np.column_stack(np.unravel_index(np.array(pth[::-1]), (Hh, Ww)))
PE, PN = XMIN + pth[:, 1] + 0.5, YMAX - pth[:, 0] - 0.5
D0 = d0.reshape(Hh, Ww); DEND = D0[end]
# --- lidar
ld = lambda tag: np.loadtxt(os.path.join(A, "1_LiDAR", f"LiDAR_{tag}_points_clip.csv"), delimiter=",", skiprows=1)
L11, L22 = ld("2011_Nov"), ld("2022_Apr")


def dem(name):
    with rasterio.open(os.path.join(A, "1_LiDAR", name)) as ds:
        z = ds.read(1).astype(float)
    z[z < -1000] = np.nan
    return z


D11, D22 = dem("Ground_DEM_2011_Nov_1ft.tif"), dem("Ground_DEM_2022_Apr_1ft.tif")
with rasterio.open(os.path.join(A, "3_GIS", "LiDAR_Change_2011_2022.tif")) as ds:
    DOD = ds.read(1).astype(float); DOD[DOD < -1000] = np.nan
HS22, HS11 = hillshade(D22), hillshade(D11)
BANK = [r for r in csv.DictReader(open(os.path.join(A, "4_Results", "LiDAR_South_Bank_Change.csv"))) if r["Station"].isdigit()]
SB11 = shp_parts(os.path.join(A, "3_GIS", "South_Bank_2011_LiDAR.shp"))
SB22 = shp_parts(os.path.join(A, "3_GIS", "South_Bank_2022_LiDAR.shp"))
K = 74
U = np.arange(-40, 80.01, 0.5)
rc = [YMAX - (CL[K, 1] + U * NRM[K, 1]) - 0.5, CL[K, 0] + U * NRM[K, 0] - XMIN - 0.5]
Z11p = ndimage.map_coordinates(D11, rc, order=1, cval=np.nan); Z22p = ndimage.map_coordinates(D22, rc, order=1, cval=np.nan)
row74 = BANK[K]
toe, top = float(row74["Face_toe_ft"]), float(row74["Face_top_ft"]); hgt = min(top - toe, 12.0)
LV = [toe + f * hgt for f in (0.25, 0.5, 0.75)]


def cross(prof, L):
    i = np.flatnonzero((prof[:-1] < L) & (prof[1:] >= L) & (U[:-1] > 5))[0]
    return U[i] + (L - prof[i]) / (prof[i + 1] - prof[i]) * 0.5


X11 = [cross(Z11p, L) for L in LV]
MOVES = [float(row74[k]) for k in ("Move_25pct_ft", "Move_50pct_ft", "Move_75pct_ft")]   # the measured values
X22 = [x + mv for x, mv in zip(X11, MOVES)]
W1, W2, S1, S2 = 636215, 636315, 863780, 863880
SH = (2.21, -6.37)


def height_map(p):
    m = 40
    k = (p[:, 0] > W1 - m) & (p[:, 0] < W2 + m) & (p[:, 1] > S1 - m) & (p[:, 1] < S2 + m) & (p[:, 3] != 7)
    gx, gy = np.meshgrid(np.arange(W1 - m + 0.5, W2 + m), np.arange(S2 + m - 0.5, S1 - m, -1.0))
    Z = LinearNDInterpolator(p[k, :2], p[k, 2])(gx, gy); Z = np.nan_to_num(Z, nan=np.nanmedian(Z))
    return ndimage.gaussian_filter(np.clip(Z - ndimage.minimum_filter(Z, size=41), 0, 40), 1.0)[m:-m, m:-m]


H11h, H22h = height_map(L11), height_map(L22)
_f, _a = plt.subplots()
XX, YY = np.linspace(W1 + 0.5, W2 - 0.5, 100), np.linspace(S2 - 0.5, S1 + 0.5, 100)
SEG11 = _a.contour(XX, YY, H11h, levels=[10]).allsegs[0]; SEG22 = _a.contour(XX, YY, H22h, levels=[10]).allsegs[0]
plt.close(_f)
hw = L11[(L11[:, 0] > W1) & (L11[:, 0] < W2) & (L11[:, 1] > S1) & (L11[:, 1] < S2) & (L11[:, 3] != 7)]
s4 = load_module(os.path.join(A, "2_Scripts", "04_lidar_south_bank.py"), "s4")
pts = {y: s4.load_points(y) for y in (2011, 2022)}
gm = {y: np.isin(pts[y]["c"], s4.SURVEYS[y]["ground"]) for y in pts}
T22 = s4.tin(pts[2022]["x"][gm[2022]], pts[2022]["y"][gm[2022]], pts[2022]["z"][gm[2022]], 6.0)
dist = s4.centreline_distance(CL)
WAVES = []
for sE, sN in ((0.0, 0.0), (2.21, -6.37)):                          # as delivered -> after the final slide
    T11 = s4.tin(pts[2011]["x"][gm[2011]] + sE, pts[2011]["y"][gm[2011]] + sN, pts[2011]["z"][gm[2011]], 10.0)
    dd = T22 - T11; sl, asp = s4.slope_aspect(T11)
    bias = np.median(dd[np.isfinite(dd) & (dist > 70) & (sl < 5)])
    ok = np.isfinite(dd) & (dist > 70) & (sl > 5) & (sl < 40)
    yv = (dd[ok] - bias) / np.tan(np.radians(sl[ok])); av = asp[ok]
    kk = np.abs(yv - np.median(yv)) < 3 * 1.4826 * np.median(np.abs(yv - np.median(yv)))
    cf, *_ = np.linalg.lstsq(np.column_stack([np.cos(np.radians(av[kk])), np.sin(np.radians(av[kk])), np.ones(kk.sum())]), yv[kk], rcond=None)
    bins = np.arange(0, 361, 20)
    WAVES.append((np.array([np.median(yv[kk][(av[kk] >= a) & (av[kk] < b)]) for a, b in zip(bins[:-1], bins[1:])]), cf))
WMID = np.arange(10, 360, 20)
print("data ready; rendering frames...")


# ------------------------------------------------------------------------------------------------ step 1
def s1():
    ax = mapax(); ax.imshow(win(p25, M_EXT), extent=M_EXT)
    for i, seg in enumerate(SB22):
        ax.plot(*seg.T, color="yellow", lw=3.5)
    ax.annotate("", xy=CL[34], xytext=CL[24], arrowprops=dict(arrowstyle="-|>", color="#00d0ff", lw=3, mutation_scale=22))
    ax.text(*(CL[27] - 40 * NRM[27]), "creek flows\nthis way", color="#00d0ff", fontsize=13, fontweight="bold", ha="center")
    ax.text(636420, 864030, "NORTH bank", color="w", fontsize=14, fontweight="bold", ha="center", bbox=dict(fc="0.1", ec="none", alpha=0.55))
    ax.text(636330, 863760, "SOUTH bank (house side)  =  what we care about", color="yellow", fontsize=14, fontweight="bold",
            ha="center", bbox=dict(fc="0.1", ec="none", alpha=0.6))
    ax.set_xlim(M_EXT[:2]); ax.set_ylim(M_EXT[2:])


put(0, "The question: has the creek's SOUTH bank (the house side, yellow) moved toward the houses? We answer it with two kinds of "
       "data: aerial photos from many years, and two laser (lidar) surveys flown from planes in 2011 and 2022.", s1, 7000)

# ------------------------------------------------------------------------------------------------ step 2
CAP2a = ("Photos from different years do not sit exactly on top of each other: each is off by about 1 to 2.5 ft. So first we "
         "line every photo up on the 2025 photo, using things that do not move: curbs, driveways, road edges and roofs "
         "(yellow boxes).")


def s2a():
    ax = mapax(); ax.imshow(p25, extent=FULL)
    for r0_, r1_, c0_, c1_ in REG:
        e = [XMIN + c0_ * PIX, XMIN + c1_ * PIX, YMAX - r1_ * PIX, YMAX - r0_ * PIX]
        ax.add_patch(Rectangle((e[0], e[2]), e[1] - e[0], e[3] - e[2], fill=False, ec="yellow", lw=2.5, ls="--"))
    ax.text(XMIN + 8, YMAX - 322, "houses, driveways, streets", color="yellow", fontsize=13, fontweight="bold", va="top",
            bbox=dict(fc="0.1", ec="none", alpha=0.6))
    ax.text(XMIN + 1560 * PIX - 6, YMAX - 8, "Samsondale Ave", color="yellow", fontsize=13, fontweight="bold", va="top", ha="right",
            bbox=dict(fc="0.1", ec="none", alpha=0.6))


put(1, CAP2a, s2a, 5000)
r, c = best["r"], best["c"]
M = best["m"]
bi, bj = best["p"][0], best["p"][1]
t25 = p25[r - 20:r + 100, c - 20:c + 100]
s16 = np.clip(rgb("NYS_2016_RGB") / 255, 0, 1)[r - 30:r + 110, c - 30:c + 110]
scan = [(e, n) for n in (15, 7.5, 0, -7.5, -15) for e in ((-15, -7.5, 0, 7.5, 15) if n in (15, 0, -15) else (15, 7.5, 0, -7.5, -15))]
CAP2b = ("How: cut a 40-ft square around a landmark out of the 2025 photo (yellow). Slide it over the other photo (here 2016) and "
         "score how well it fits at every spot. The best spot shows how far that photo is off.")


def s2b(nvis, final=False):
    def draw():
        a1 = mapax([0.02, 0.2, 0.28, 0.68]); a2 = mapax([0.35, 0.2, 0.28, 0.68]); a3 = fig.add_axes([0.69, 0.25, 0.22, 0.6])
        a1.imshow(t25, extent=[-10, 50, -10, 50]); a1.add_patch(Rectangle((0, 0), 40, 40, fill=False, ec="yellow", lw=3))
        a1.set_title("2025: the 40-ft square", fontsize=13, loc="left")
        a2.imshow(s16, extent=[-15, 55, -15, 55]); a2.set_title("2016: slide it around", fontsize=13, loc="left")
        mask = np.zeros_like(M, bool)
        for (e, n) in scan[:nvis]:
            j, i = int(round(30 + e / PIX)), int(round(30 - n / PIX))
            mask[max(0, i - 8):i + 9, max(0, j - 8):j + 9] = True
        shown = np.where(mask | final, M, np.nan)
        im = a3.imshow(shown, extent=[-15, 15, -15, 15], cmap="magma", vmin=0, vmax=1)
        a3.set_xlabel("slide east (ft)", fontsize=11); a3.set_ylabel("slide north (ft)", fontsize=11)
        a3.set_title("fit score at each spot", fontsize=13, loc="left")
        cax = fig.add_axes([0.925, 0.25, 0.012, 0.6]); cb = fig.colorbar(im, cax=cax); cb.set_label("1 = perfect fit", fontsize=10)
        if final:
            ex, ny = (bj - 30) * PIX, -(bi - 30) * PIX
            a2.add_patch(Rectangle((ex, ny), 40, 40, fill=False, ec="lime", lw=3))
            a3.plot(ex, ny, "+", color="lime", ms=22, mew=3)
            a3.text(-14, 12.5, f"best: {M.max():.2f}", color="lime", fontsize=13, fontweight="bold")
        else:
            e, n = scan[nvis - 1]
            j, i = int(round(30 + e / PIX)), int(round(30 - n / PIX))
            a2.add_patch(Rectangle((e, n), 40, 40, fill=False, ec="cyan", lw=3))
            a3.plot(e, n, "s", mfc="none", mec="cyan", ms=14, mew=2)
            a3.text(-14, 12.5, f"score here: {M[i, j]:.2f}", color="w", fontsize=12, fontweight="bold")
    return draw


put(1, CAP2b, s2b(1), 2500)
for nv in range(2, len(scan) + 1):
    put(1, CAP2b, s2b(nv), 110)
put(1, CAP2b, s2b(len(scan), True), 3500)
CAP2c = (f"We repeat this for every landmark square that finds a clear match ({len(good)} for 2016) and take the middle value "
         f"(red star): the 2016 photo sat {abs(mdE):.1f} ft east and {abs(mdN):.1f} ft south of the 2025 photo.")


def s2c(n, star=False):
    def draw():
        a1 = mapax([0.012, 0.19, 0.6, 0.72]); a1.imshow(p25, extent=FULL)
        for q in good[:n]:
            e0, n0 = XMIN + q["c"] * PIX, YMAX - (q["r"] + 80) * PIX
            a1.add_patch(Rectangle((e0, n0), 40, 40, fill=False, ec="lime", lw=1.6))
        a2 = fig.add_axes([0.68, 0.24, 0.26, 0.62])
        a2.scatter([q["dE"] for q in good[:n]], [q["dN"] for q in good[:n]], s=40, color="lime", ec="k", lw=0.6)
        if star:
            a2.plot(mdE, mdN, "*", color="red", ms=26, mec="k", mew=0.8)
        a2.axhline(0, color="0.6", lw=0.8); a2.axvline(0, color="0.6", lw=0.8)
        a2.set_xlim(-6, 6); a2.set_ylim(-6, 6); a2.set_aspect("equal")
        a2.set_xlabel("how far off, east (ft)", fontsize=11); a2.set_ylabel("north (ft)", fontsize=11)
        a2.set_title(f"one dot per square ({n} of {len(good)})", fontsize=13, loc="left")
    return draw


for n in range(3, len(good) + 1, 3):
    put(1, CAP2c, s2c(n), 110)
put(1, CAP2c, s2c(len(good), True), 3500)
g16 = p16.mean(axis=2)
gm_ = np.hypot(*np.gradient(ndimage.gaussian_filter(g16, 1.0)))
reg = (slice(r - 20, r + 100), slice(c - 20, c + 100))
edge = gm_[reg] > np.percentile(gm_[reg], 90)
EDGE = np.zeros(edge.shape + (4,)); EDGE[edge] = (0, 1, 1, 0.9)
CAP2d = ("Then the whole 2016 photo is slid back by that amount (the move is shown 5 times bigger here so you can see it). "
         "Every other year is lined up the same way. Now all the photos sit on top of each other.")


def s2d(t):
    def draw():
        ax = mapax([0.25, 0.19, 0.5, 0.72])
        ax.imshow(p25[reg].mean(axis=2), extent=[0, 60, 0, 60], cmap="gray")
        sx, sy = 5 * mdE * (1 - t), 5 * mdN * (1 - t)
        ax.imshow(EDGE, extent=[sx, 60 + sx, sy, 60 + sy])
        ax.set_xlim(0, 60); ax.set_ylim(0, 60)
        ax.set_title("grey = 2025 photo;  cyan = outlines from the 2016 photo", fontsize=13, loc="left")
        ax.text(2, 2, "lined up!" if t >= 1 else "sliding...", color="lime" if t >= 1 else "w", fontsize=15, fontweight="bold")
    return draw


put(1, CAP2d, s2d(0), 1800)
for t in np.linspace(0.1, 1, 10):
    put(1, CAP2d, s2d(t), 110)
put(1, CAP2d, s2d(1), 2800)

# ------------------------------------------------------------------------------------------------ step 3
CAP3a = ("Next, every pixel of every photo gets a score: how red-brown is it, compared with a typical pixel of that photo? "
         "In spring, soil and dead leaves are red-brown (light). Water, shadows and grey roofs are not (dark).")
ph16, sc16 = win(p16, M_EXT), gray_rgb(win(zs[3], M_EXT))


def s3a(t):
    def draw():
        ax = mapax(); ax.imshow((1 - t) * ph16 + t * sc16, extent=M_EXT)
        ax.text(M_EXT[0] + 6, M_EXT[3] - 8, "2016 photo" if t < 0.5 else "2016 score", color="yellow", fontsize=15,
                fontweight="bold", va="top", bbox=dict(fc="0.1", ec="none", alpha=0.6))
    return draw


put(2, CAP3a, s3a(0), 2200)
for t in np.linspace(0.1, 1, 10):
    put(2, CAP3a, s3a(t), 110)
put(2, CAP3a, s3a(1), 2500)
CAP3b = (f"Then we average the scores of {len(NAMES)} spring photos ({YEARS[0]} to {YEARS[-1]}), pixel by pixel. Shadows and "
         "glare that show up in only one year fade away. The creek is dark in EVERY year, so it becomes one clean dark band.")


def s3b(k, bar=False):
    def draw():
        ax = mapax([0.012, 0.22, 0.976, 0.70]); ax.imshow(gray_rgb(win(avgs[k - 1], M_EXT)), extent=M_EXT)
        ax.text(M_EXT[0] + 6, M_EXT[3] - 8, f"average of {k} photo{'s' if k > 1 else ''}:  " + ", ".join(YEARS[:k]),
                color="yellow", fontsize=14, fontweight="bold", va="top", bbox=dict(fc="0.1", ec="none", alpha=0.6))
        if bar:
            cax = fig.add_axes([0.25, 0.185, 0.5, 0.022])
            cb = fig.colorbar(plt.cm.ScalarMappable(cmap="gray", norm=plt.Normalize(-3, 3)), cax=cax, orientation="horizontal")
            cb.set_ticks([-3, 0, 3]); cb.set_ticklabels(["dark = water-like", "typical", "light = red soil / leaves"]); cb.ax.tick_params(labelsize=11)
    return draw


for k in range(1, len(NAMES) + 1):
    put(2, CAP3b, s3b(k), 900)
put(2, CAP3b, s3b(len(NAMES), True), 3200)

# ------------------------------------------------------------------------------------------------ step 4
ZC = gray_rgb(zc)
SE, SN = XMIN + start[1] + 0.5, YMAX - start[0] - 0.5
EE, EN = XMIN + end[1] + 0.5, YMAX - end[0] - 0.5


def s4f(reach=None, frac=None, cap_note=None, smooth=False):
    def draw():
        ax = mapax()
        if smooth:
            ax.imshow(p25, extent=FULL); ax.plot(CL[:, 0], CL[:, 1], color="#00d0ff", lw=4)
        else:
            ax.imshow(ZC, extent=FULL)
            if reach is not None:
                ov = np.zeros(ZC.shape[:2] + (4,)); ov[D0 <= reach] = (0.0, 0.85, 1.0, 0.55); ax.imshow(ov, extent=FULL)
            if frac is not None:
                n = max(2, int(frac * len(PE))); ax.plot(PE[:n], PN[:n], color="#ff3030", lw=3.5)
        ax.plot(SE, SN, "o", color="lime", ms=16, mec="k"); ax.plot(EE, EN, "s", color="lime", ms=16, mec="k")
        ax.text(SE + 10, SN - 36, "START", color="lime", fontsize=14, fontweight="bold")
        ax.text(EE - 110, EN - 36, "END", color="lime", fontsize=14, fontweight="bold")
        if cap_note:
            ax.text(XMIN + 10, YMAX - 10, cap_note, color="w", fontsize=13, fontweight="bold", va="top",
                    bbox=dict(fc="0.1", ec="none", alpha=0.65))
    return draw


CAP4a = ("Now the centreline. The computer must get from a START point on the west edge to an END point on the east edge. "
         "Every 1-ft step has a price: very cheap on dark (water-like) pixels, very expensive on red ground.")
put(3, CAP4a, s4f(cap_note="price of one 1-ft step:  water 0.01   |   typical ground 1   |   red ground up to 90"), 5000)
CAP4b = ("Think of water poured at the START: it races along the cheap dark band and hardly creeps onto the expensive ground. "
         "It also spills into other dark spots (roofs, the cul-de-sac), but those lead nowhere. The first way to reach the END "
         "is the cheapest route.")
for t in np.linspace(0.03, 1.0, 26):
    put(3, CAP4b, s4f(reach=t * DEND * 1.02), 110)
put(3, CAP4b, s4f(reach=DEND * 1.02), 1500)
CAP4c = ("That cheapest route (red) follows the creek. Roofs and shadows are dark too, but they are dead ends: to reach them the "
         "route would have to cross expensive ground and come back.")
for t in np.linspace(0.07, 1, 14):
    put(3, CAP4c, s4f(frac=t), 90)
put(3, CAP4c, s4f(frac=1), 2500)
put(3, "The route is then smoothed over 20 ft. This is the centreline (blue): a fixed ruler that stays the same for every year.",
    s4f(smooth=True), 3500)

# ------------------------------------------------------------------------------------------------ step 5
CAP5 = ("Along the centreline we put a station every 10 ft (0 to 127) and draw a cross line square to the creek at each station. "
        "Both years are measured on these SAME lines, so they are compared at exactly the same places.")


def s5(ns, nl):
    def draw():
        ax = mapax(); ax.imshow(p25, extent=FULL); ax.plot(CL[:, 0], CL[:, 1], color="#00d0ff", lw=2.5)
        if nl:
            segs = [[CL[k] - 30 * NRM[k], CL[k] + 45 * NRM[k]] for k in range(nl)]
            ax.add_collection(LineCollection(segs, colors="w", linewidths=[1.8 if k % 10 == 0 else 0.8 for k in range(nl)]))
        ax.plot(CL[:ns, 0], CL[:ns, 1], "o", color="yellow", ms=4.5, mec="k", mew=0.4)
        for k in range(0, ns, 10):
            p = CL[k] - 40 * NRM[k]
            if XMIN + 12 < p[0] < XMAX - 12 and YMIN + 12 < p[1] < YMAX - 12:          # skip labels off the map edge
                ax.text(*p, str(k), color="yellow", fontsize=12, fontweight="bold", ha="center", va="center",
                        bbox=dict(fc="0.1", ec="none", alpha=0.55, pad=1))
        ax.set_xlim(XMIN, XMAX); ax.set_ylim(YMIN, YMAX)
    return draw


for ns in range(8, 129, 8):
    put(4, CAP5, s5(min(ns, 128), 0), 90)
for nl in range(8, 129, 8):
    put(4, CAP5, s5(128, min(nl, 128)), 90)
put(4, CAP5, s5(128, 128), 3500)

# ------------------------------------------------------------------------------------------------ step 6
cx, cy = CL[K] + 28 * NRM[K]
LW = [cx - 45, cx + 45, cy - 45, cy + 45]
inl = lambda P: P[(P[:, 0] > LW[0]) & (P[:, 0] < LW[1]) & (P[:, 1] > LW[2]) & (P[:, 1] < LW[3]) & (P[:, 3] != 7)]
w11, w22 = inl(L11), inl(L22)
g11, g22 = np.isin(w11[:, 3], [2, 18]), w22[:, 3] == 2
CAP6a = ("Lidar = a laser scanner flown in a plane. Every laser hit becomes a point with an exact position and height. "
         "We have two surveys: 19 Nov 2011 (fewer points) and 15 Apr 2022. Brown = hits on the ground, green = everything "
         "else (mostly trees).")
CAP6b = "The survey company already labelled every point (ground, tree, roof...). We keep only the ground points."


def s6a(alpha_other):
    def draw():
        for j, (w, g, lab, sz) in enumerate(((w11, g11, "2011 survey", 9), (w22, g22, "2022 survey", 4))):
            ax = mapax([0.06 + j * 0.47, 0.19, 0.4, 0.71])
            ax.set_facecolor("#f4f4f4")
            ax.scatter(w[~g, 0], w[~g, 1], s=sz, color="#1b9e77", alpha=alpha_other, lw=0)
            ax.scatter(w[g, 0], w[g, 1], s=sz, color="#8c510a", lw=0)
            ax.set_xlim(LW[:2]); ax.set_ylim(LW[2:]); ax.set_aspect("equal")
            ax.set_title(f"{lab}: {len(w) if alpha_other > 0.5 else g.sum()} points in this 90 x 90 ft square", fontsize=13, loc="left")
            ax.plot([LW[1] - 25, LW[1] - 5], [LW[2] + 5, LW[2] + 5], color="k", lw=3); ax.text(LW[1] - 15, LW[2] + 7, "20 ft", ha="center", fontsize=11)
    return draw


put(5, CAP6a, s6a(1.0), 6000)
for a_ in np.linspace(0.85, 0.05, 8):
    put(5, CAP6b, s6a(a_), 120)
put(5, CAP6b, s6a(0.05), 3000)
CAP6c = ("But the 2011 survey sits about 6.7 ft off: its house (blue outline) does not sit on the 2022 house (red outline). "
         "Matching the roofs of 29 house areas gives the shift. Then ALL 2011 points slide 2.2 ft east and 6.4 ft south - "
         "nothing is stretched or turned.")


def s6c(t):
    def draw():
        ax = mapax([0.2, 0.17, 0.6, 0.70])
        ax.imshow(H22h, extent=[W1, W2, S1, S2], cmap="viridis", vmin=0, vmax=30, alpha=0.8)
        dx, dy = SH[0] * t, SH[1] * t
        ax.scatter(hw[:, 0] + dx, hw[:, 1] + dy, s=5, color="#1f77b4", alpha=0.55, lw=0)
        for s_ in SEG22:
            ax.plot(s_[:, 0], s_[:, 1], color="red", lw=3)
        for s_ in SEG11:
            ax.plot(s_[:, 0] + dx, s_[:, 1] + dy, color="#1f77b4", lw=3)
        ax.set_xlim(W1, W2); ax.set_ylim(S1, S2)
        ax.set_title("red = house in 2022 lidar;  blue = house (and dots) in 2011 lidar", fontsize=13, loc="left")
        ax.text(W1 + 3, S1 + 3, f"2011 moved: {dx:.1f} ft east, {abs(dy):.1f} ft south", color="w", fontsize=14,
                fontweight="bold", bbox=dict(fc="0.1", ec="none", alpha=0.6))
    return draw


put(5, CAP6c, s6c(0), 5500)
for t in np.linspace(0.07, 1, 15):
    put(5, CAP6c, s6c(t), 110)
put(5, CAP6c, s6c(1), 3000)
CAP6d = ("Check on hillsides away from the creek: when one survey sits sideways, hills show fake height changes (one side up, "
         "the other down) that make a wave in this chart. Before the slide the wave is big; after it, only 0.2 ft is left, "
         "so the two surveys are lined up.")


def s6d(t):
    def draw():
        a1 = mapax([0.03, 0.2, 0.36, 0.66])
        xh = np.linspace(0, 100, 300)
        hill = lambda o: np.interp(xh, [0, 20 + o, 45 + o, 55 + o, 80 + o, 100], [0, 0, 12, 12, 0, 0])
        off = 6 * (1 - t) + 0.3 * t
        a1.plot(xh, hill(0), color="#1f77b4", lw=7, label="2011 ground"); a1.plot(xh, hill(off), color="red", lw=2.5, label="2022 ground")
        a1.set_ylim(-4, 16); a1.legend(fontsize=11, loc="lower center", frameon=False, ncol=2)
        a1.set_title("a hill in the two surveys (sketch)", fontsize=13, loc="left")
        a1.text(50, 14, "sitting sideways" if t < 0.5 else "on top of each other", ha="center", fontsize=12,
                fontweight="bold", color="#b30000" if t < 0.5 else "#1a7f1a")
        a2 = fig.add_axes([0.47, 0.25, 0.5, 0.6])
        (m0, c0), (m1, c1) = WAVES
        cf = (1 - t) * c0 + t * c1; med = (1 - t) * m0 + t * m1
        xx = np.linspace(0, 360, 200)
        a2.plot(WMID, med, "o", color="k", ms=5); a2.plot(xx, cf[0] * np.cos(np.radians(xx)) + cf[1] * np.sin(np.radians(xx)) + cf[2], color="tab:orange", lw=3)
        a2.axhline(0, color="0.5", lw=1); a2.set_ylim(-4, 4)
        a2.set_xticks([0, 90, 180, 270, 360]); a2.set_xticklabels(["N", "E", "S", "W", "N"]); a2.tick_params(labelsize=11)
        a2.set_xlabel("which way the hillside faces", fontsize=12); a2.set_ylabel("height change / steepness (ft)", fontsize=12)
        a2.set_title(f"real hillsides (~145,000 spots): wave = {np.hypot(cf[0], cf[1]):.1f} ft"
                     + ("  (before the slide)" if t == 0 else "  (after the slide)" if t >= 1 else ""), fontsize=13, loc="left")
    return draw


put(5, CAP6d, s6d(0), 3500)
for t in np.linspace(0.1, 1, 9):
    put(5, CAP6d, s6d(t), 130)
put(5, CAP6d, s6d(1), 3500)

# ------------------------------------------------------------------------------------------------ step 7
TW = [cx - 30, cx + 30, cy - 30, cy + 30]
tp = L22[(L22[:, 0] - 0.25 > TW[0] - 6) & (L22[:, 0] - 0.25 < TW[1] + 6) & (L22[:, 1] - 1.74 > TW[2] - 6) & (L22[:, 1] - 1.74 < TW[3] + 6) & (L22[:, 3] == 2)]
tx, ty = tp[:, 0] - 0.25, tp[:, 1] - 1.74
tri = Delaunay(np.column_stack([tx, ty]))
TSEG = np.array([[(tx[a], ty[a]), (tx[b], ty[b])] for s_ in tri.simplices for a, b in ((s_[0], s_[1]), (s_[1], s_[2]), (s_[2], s_[0]))])
zwin = win(D22, TW, cell=1.0)
SURF = plt.cm.terrain(np.clip((zwin - np.nanpercentile(zwin, 2)) / (np.nanpercentile(zwin, 98) - np.nanpercentile(zwin, 2)), 0, 1))[..., :3]
SURF = SURF * (0.45 + 0.55 * win(HS22, TW, cell=1.0))[..., None]
CAP7a = ("Next the ground points are joined into small triangles, like a net thrown over the ground, and the height is read "
         "every 1 ft. That gives a ground surface (a 'DEM') for the survey.")


def s7a(ta, ts):
    def draw():
        ax = mapax([0.25, 0.17, 0.5, 0.70]); ax.set_facecolor("white")
        if ts > 0:
            ax.imshow(SURF, extent=TW, alpha=ts)
        if ta > 0:
            ax.add_collection(LineCollection(TSEG, colors="k", linewidths=0.5, alpha=ta * (1 - 0.7 * ts)))
        ax.scatter(tx, ty, s=14, color="#8c510a", lw=0, alpha=1 - 0.8 * ts)
        ax.set_xlim(TW[:2]); ax.set_ylim(TW[2:]); ax.set_aspect("equal")
        ax.set_title("2022 ground points near station 74 (60 x 60 ft)", fontsize=13, loc="left")
    return draw


put(6, CAP7a, s7a(0, 0), 2200)
for t in np.linspace(0.15, 1, 6):
    put(6, CAP7a, s7a(t, 0), 120)
put(6, CAP7a, s7a(1, 0), 1500)
for t in np.linspace(0.15, 1, 6):
    put(6, CAP7a, s7a(1, t), 120)
put(6, CAP7a, s7a(1, 1), 2500)
CAP7b = ("This is done SEPARATELY for each survey: two ground surfaces, 2011 and 2022, never merged. Lidar cannot see under water, "
         "so there is no data for the creek bed (grey). Houses are grey too: no ground hits under a roof.")


def s7b():
    for j, (Hs, lab) in enumerate(((HS11, "ground surface from the 2011 survey"), (HS22, "ground surface from the 2022 survey"))):
        ax = mapax([0.01 + j * 0.495, 0.2, 0.485, 0.7])
        cm = plt.cm.gray.copy(); cm.set_bad("#9e9e9e")
        Z = win(D11 if j == 0 else D22, M_EXT, cell=1.0)
        ax.imshow(np.ma.masked_invalid(np.where(np.isfinite(Z), win(Hs, M_EXT, cell=1.0), np.nan)), extent=M_EXT, cmap=cm, vmin=0, vmax=1)
        ax.set_title(lab, fontsize=13, loc="left")


put(6, CAP7b, s7b, 5500)

# ------------------------------------------------------------------------------------------------ step 8
MW = [CL[K, 0] - 80, CL[K, 0] + 80, CL[K, 1] - 70, CL[K, 1] + 55]
CAP8a = ("At each station we cut BOTH ground surfaces along the cross line. That gives a cross-section: the shape of the ground "
         "across the creek. Here is station 74: 2011 in blue, 2022 in red.")


def s8(f11, f22, arrows=0.0, done=False):
    def draw():
        a1 = mapax([0.012, 0.19, 0.3, 0.72])
        a1.imshow(win(HS22, MW, cell=1.0), extent=MW, cmap="gray", vmin=0, vmax=1)
        e0, e1 = CL[K] + U[0] * NRM[K], CL[K] + U[-1] * NRM[K]
        a1.plot([e0[0], e1[0]], [e0[1], e1[1]], color="yellow", lw=3)
        a1.plot(CL[:, 0], CL[:, 1], color="#00d0ff", lw=1.5, ls="--")
        f = max(f11, f22); p = CL[K] + U[int(f * (len(U) - 1))] * NRM[K]
        a1.plot(*p, "o", color="red" if f22 > 0 else "#1f77b4", ms=11, mec="k")
        a1.set_xlim(MW[:2]); a1.set_ylim(MW[2:]); a1.set_title("station 74, top view", fontsize=13, loc="left")
        a1.text(*(CL[K] + 70 * NRM[K] + np.array([3, 0])), "houses\nthis way", fontsize=11, color="yellow", fontweight="bold")
        a2 = fig.add_axes([0.38, 0.25, 0.6, 0.64])
        n11, n22 = int(f11 * (len(U) - 1)) + 1, int(f22 * (len(U) - 1)) + 1
        if f11 > 0:
            a2.plot(U[:n11], Z11p[:n11], color="#1f77b4", lw=3, label="ground 19 Nov 2011")
        if f22 > 0:
            a2.plot(U[:n22], Z22p[:n22], color="red", lw=3, label="ground 15 Apr 2022")
        a2.axvline(0, color="#00a0d0", lw=1.2, ls=":")
        a2.text(1, 41, "centreline", color="#0080b0", fontsize=11)
        a2.text(-38, 29.6, "north bank", fontsize=12, fontweight="bold"); a2.text(38, 41, "SOUTH bank (house side)", fontsize=12, fontweight="bold")
        a2.fill_between([4, 16], 19.5, 21.2, color="#9cc9ee", alpha=0.6); a2.text(10, 19.8, "water:\nno data", ha="center", fontsize=9.5, color="#1f5f99")
        a2.set_xlim(-40, 80); a2.set_ylim(19, 42.5); a2.tick_params(labelsize=11)
        a2.set_xlabel("distance from the centreline along the cross line (ft)", fontsize=12); a2.set_ylabel("ground elevation (ft)", fontsize=12)
        if arrows > 0:
            a2.axhspan(toe, toe + hgt, xmin=0.38, xmax=0.62, color="yellow", alpha=0.18)
            for L, xa, xb in zip(LV, X11, X22):
                a2.plot([15, 44], [L, L], color="0.4", lw=1, ls="--")
                a2.annotate("", xy=(xa + arrows * (xb - xa), L), xytext=(xa, L), arrowprops=dict(arrowstyle="-|>", color="k", lw=2.2))
                if done:
                    a2.text(xb + 1.2, L - 0.3, f"+{xb - xa:.1f} ft", fontsize=12, fontweight="bold")
        if done:
            a2.text(47, 20.4, f"average: +{float(row74['Move_mean_ft']):.1f} ft\ntoward the houses\n"
                              f"error limit: {row74['Detection_limit_95pct_ft']} ft\n->  REAL change",
                    fontsize=12, fontweight="bold", color="#b30000", bbox=dict(fc="w", ec="#b30000"))
        if f11 > 0 or f22 > 0:
            a2.legend(fontsize=11, loc="upper left")
    return draw


put(7, CAP8a, s8(0, 0), 2500)
for t in np.linspace(0.08, 1, 12):
    put(7, CAP8a, s8(t, 0), 100)
for t in np.linspace(0.08, 1, 12):
    put(7, CAP8a, s8(1, t), 100)
put(7, CAP8a, s8(1, 1), 2500)
CAP8b = ("On the cross-section we find the south bank face and measure how far it is from the centreline at 1/4, 1/2 and 3/4 of "
         "its height, in 2011 and in 2022. At station 74 the bank moved about 9 ft toward the houses. The error here is only "
         "1.3 ft, so this is real.")
for t in np.linspace(0.12, 1, 8):
    put(7, CAP8b, s8(1, 1, arrows=t), 120)
put(7, CAP8b, s8(1, 1, arrows=1, done=True), 6000)

# ------------------------------------------------------------------------------------------------ step 9
ST = np.array([int(r_["Station"]) for r_ in BANK if r_["Move_mean_ft"] != ""])
MV = np.array([float(r_["Move_mean_ft"]) for r_ in BANK if r_["Move_mean_ft"] != ""])
LM = np.array([float(r_["Detection_limit_95pct_ft"]) for r_ in BANK if r_["Move_mean_ft"] != ""])
CF = np.array([r_["Bank_setting"] == "creek-facing" for r_ in BANK if r_["Move_mean_ft"] != ""])
COL = np.where(~CF, "#d0d0d0", np.where(MV > LM, "#d62728", np.where(MV < -LM, "#1f77b4", "#6d6d6d")))
CAP9 = ("We repeat this at all 128 stations. Grey band = the error (1.3 to 2.2 ft): a bar inside it is just noise. "
        "Red = real movement toward the houses. Blue = real build-up. Pale bars = banks set back behind a gravel bar.")


def s9(kmax, final=False):
    def draw():
        a1 = mapax([0.012, 0.56, 0.976, 0.37])
        a1.imshow(win(HS22, M_EXT, cell=1.0), extent=M_EXT, cmap="gray", vmin=0, vmax=1)
        a1.plot(CL[:, 0], CL[:, 1], color="#00d0ff", lw=1.5)
        if not final:
            kk = min(kmax, 127); e0, e1 = CL[kk] - 30 * NRM[kk], CL[kk] + 45 * NRM[kk]
            a1.plot([e0[0], e1[0]], [e0[1], e1[1]], color="red", lw=4)
            a1.text(*(CL[kk] - 45 * NRM[kk]), f"station {kk}", color="yellow", fontsize=12, fontweight="bold", ha="center",
                    clip_on=True, bbox=dict(fc="0.1", ec="none", alpha=0.6))
        else:
            box = np.vstack([CL[72] - 5 * NRM[72], CL[76] - 5 * NRM[76], CL[76] + 45 * NRM[76], CL[72] + 45 * NRM[72], CL[72] - 5 * NRM[72]])
            a1.plot(*box.T, color="red", lw=3)
        a1.set_xlim(M_EXT[:2]); a1.set_ylim(M_EXT[2:])
        a2 = fig.add_axes([0.07, 0.2, 0.9, 0.33])
        sel = ST <= kmax
        a2.fill_between(ST * 10, -LM, LM, color="0.88", step="mid")
        a2.bar(ST[sel] * 10, MV[sel], width=8, color=COL[sel])
        a2.axhline(0, color="k", lw=0.8); a2.set_xlim(-10, 1280); a2.set_ylim(-6.5, 10)
        a2.set_ylabel("bank moved (ft)\n+ = toward houses", fontsize=11); a2.tick_params(labelsize=10)
        a2.set_xlabel("distance along the creek (ft)  =  station x 10", fontsize=11)
        if final:
            a2.add_patch(Rectangle((712, -1), 46, 11, fill=False, ec="#d62728", lw=2.5))
            a2.text(770, 7.5, "stations 72-75: up to 9.1 ft", color="#d62728", fontsize=13, fontweight="bold")
    return draw


for km in range(4, 132, 4):
    put(8, CAP9, s9(km), 100)
put(8, CAP9, s9(127, True), 5000)

# ------------------------------------------------------------------------------------------------ step 10
CAP10 = ("The answer: along almost the whole M the south bank stayed put (within about 1.5 ft). The one big move is at stations "
         "72 to 75, where the creek leaves the dip: up to 9 ft toward the houses between Nov 2011 and Apr 2022. "
         "A few other spots moved about 2 ft.")


def s10():
    ax = mapax()
    ax.imshow(win(HS22, M_EXT, cell=1.0), extent=M_EXT, cmap="gray", vmin=0, vmax=1)
    dd = win(DOD, M_EXT, cell=1.0)
    ax.imshow(np.ma.masked_where(~(np.abs(dd) >= 1.0), dd), extent=M_EXT, cmap="RdBu", vmin=-6, vmax=6, alpha=0.85)
    for i, sg in enumerate(SB11):
        ax.plot(*sg.T, color="orange", lw=2.5, ls="--", label="south bank 2011" if i == 0 else None)
    for i, sg in enumerate(SB22):
        ax.plot(*sg.T, color="#00c800", lw=2.5, label="south bank 2022" if i == 0 else None)
    box = np.vstack([CL[72] - 5 * NRM[72], CL[76] - 5 * NRM[76], CL[76] + 45 * NRM[76], CL[72] + 45 * NRM[72], CL[72] - 5 * NRM[72]])
    ax.plot(*box.T, color="red", lw=3)
    ax.text(636560, 863800, "stations 72-75:\nbank moved up to 9 ft\ntoward the houses", color="#b30000", fontsize=14, fontweight="bold",
            bbox=dict(fc="w", ec="#b30000", alpha=0.9))
    ax.annotate("", xy=(636505, 863895), xytext=(636575, 863845), arrowprops=dict(arrowstyle="-|>", color="#b30000", lw=2.5))
    ax.text(636280, 863770, "blue patch = yard fill\n(not the creek)", color="#1f3a8a", fontsize=11.5, fontweight="bold",
            bbox=dict(fc="w", ec="none", alpha=0.8))
    ax.text(M_EXT[0] + 6, M_EXT[3] - 8, "red = ground lost, blue = ground gained (2011 -> 2022)", color="w", fontsize=12.5,
            fontweight="bold", va="top", bbox=dict(fc="0.1", ec="none", alpha=0.65))
    ax.legend(fontsize=12, loc="lower left")
    ax.set_xlim(M_EXT[:2]); ax.set_ylim(M_EXT[2:])


put(9, CAP10, s10, 9000)

# ------------------------------------------------------------------------------------------------ manifest
with open(os.path.join(DOCS, "frames.json"), "w", encoding="utf-8") as f:
    json.dump({"steps": STEPS, "captions": CAPTIONS, "frames": FRAMES}, f, separators=(",", ":"))
size = sum(os.path.getsize(os.path.join(FRAMES_DIR, x["f"])) for x in FRAMES)
print(f"{len(FRAMES)} frames, {sum(x['d'] for x in FRAMES) / 1000:.0f} s at 1x, {size / 1e6:.1f} MB, {len(CAPTIONS)} captions")
