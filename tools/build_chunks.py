"""
Builds the assistant's search index from the knowledge base.

1. Writes the per-station results table into docs/knowledge/knowledge_base.md (between the STATION_TABLE markers),
   straight from analysis/4_Results/LiDAR_South_Bank_Change.csv, so the text always matches the results.
2. Splits the knowledge base into short passages (one per ### heading, long ones split further) and writes
   docs/knowledge/chunks.json: [{id, title, steps, text}], used by the web page and by assistant/ask.py.

Steps are the animation steps 0-9 (step 1 in the animation = 0 here), taken from '<!-- steps: ... -->' lines.
usage:  python build_chunks.py
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.join(HERE, "..", "docs", "knowledge", "knowledge_base.md")
OUT = os.path.join(HERE, "..", "docs", "knowledge", "chunks.json")
CSV = os.path.join(HERE, "..", "analysis", "4_Results", "LiDAR_South_Bank_Change.csv")
SECTIONS = [("West limb", 0, 35), ("First hump", 36, 57), ("Dip", 58, 75), ("Pool / second hump", 76, 99), ("East limb", 100, 127)]
MAX_WORDS = 260


def section_of(st):
    return next(n for n, a, b in SECTIONS if a <= st <= b)


def station_table():
    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8-sig")) if r["Station"].isdigit()]
    out = []
    for a in range(0, 128, 10):
        b = min(a + 9, 127)
        out.append(f"### Stations {a} to {b}")
        out.append("<!-- steps: 7,8 -->")
        for r in rows[a:b + 1]:
            st = int(r["Station"])
            head = f"- Station {st} ({st * 10} ft, {section_of(st)}):"
            if r["Move_mean_ft"] == "":
                out.append(f"{head} no clear bank face on the 2022 cross-section, not measured.")
                continue
            mv, lim = float(r["Move_mean_ft"]), float(r["Detection_limit_95pct_ft"])
            setting = r["Bank_setting"]
            if setting == "creek-facing":
                verdict = ("REAL retreat toward the houses" if r["Real_change"] == "yes" and mv > 0 else
                           "REAL build-up toward the creek" if r["Real_change"] == "yes" else "within the noise (no measurable change)")
                where = "creek-facing bank"
            else:
                verdict = ("real change, but at a set-back bank (not creek erosion)" if r["Real_change"] == "yes"
                           else "within the noise, set-back bank")
                where = setting.replace("set back", "bank set back").replace("bar/bench", "bar or bench")
            out.append(f"{head} {where}; bank {r['Bank_u_2011_ft']} ft from the centreline in 2011 and {r['Bank_u_2022_ft']} ft "
                       f"in 2022; moved {mv:+.1f} ft (25/50/75% heights: {r['Move_25pct_ft']}, {r['Move_50pct_ft']}, "
                       f"{r['Move_75pct_ft']} ft); error limit {lim:.1f} ft; {verdict}; {float(r['Rate_ft_per_yr']):+.2f} ft/yr.")
        out.append("")
    intro = ("Movement is 2022 minus 2011 (+ = toward the houses). Distances are from the reference centreline to the bank face "
             "at mid-height. Lidar dates: 19 Nov 2011 and 15 Apr 2022 (10.4 years).")
    return "\n".join([intro, ""] + out).strip()


def update_kb():
    text = open(KB, encoding="utf-8").read()
    new = re.sub(r"(<!-- STATION_TABLE_START -->)(.*?)(<!-- STATION_TABLE_END -->)",
                 lambda m: m.group(1) + "\n" + station_table() + "\n" + m.group(3), text, flags=re.S)
    with open(KB, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    return new


def split_long(body):
    """Split a long passage at paragraph / bullet boundaries into pieces of at most MAX_WORDS words."""
    blocks, cur = [], []
    for line in body.split("\n"):
        if line.strip() == "" or line.startswith("- ") or re.match(r"^\d+\. ", line):
            if cur:
                blocks.append("\n".join(cur)); cur = []
        if line.strip():
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    pieces, piece = [], []
    for b in blocks:
        if piece and len(" ".join(piece + [b]).split()) > MAX_WORDS:
            pieces.append("\n".join(piece)); piece = []
        piece.append(b)
    if piece:
        pieces.append("\n".join(piece))
    return pieces


def chunks(text):
    text = re.sub(r"<!-- STATION_TABLE_(START|END) -->", "", text)
    out, h2, h2_steps = [], "", []
    parts = re.split(r"^(#{2,3} .+)$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        head, body = parts[i].strip(), parts[i + 1]
        m = re.search(r"<!--\s*steps:\s*([\d,\s]+)-->", body)
        steps = [int(s) for s in re.findall(r"\d+", m.group(1))] if m else None
        body = re.sub(r"<!--.*?-->", "", body).strip()
        if head.startswith("## "):
            h2, h2_steps = head[3:], steps or []
            if not body:
                continue
            title = h2
        else:
            title = f"{h2} > {head[4:]}"
        for n, piece in enumerate(split_long(body) if body else []):
            out.append({"id": len(out), "title": title + (f" (part {n + 1})" if n else ""),
                        "steps": steps if steps is not None else h2_steps, "text": piece})
    return out


if __name__ == "__main__":
    kb = update_kb()
    ch = chunks(kb)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ch, f, ensure_ascii=False, indent=0)
    words = [len(c["text"].split()) for c in ch]
    print(f"{len(ch)} passages, {sum(words)} words (max {max(words)}, median {sorted(words)[len(words) // 2]})")
